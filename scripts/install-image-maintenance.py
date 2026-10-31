"""Explicit root installation of retention policy, command and disabled timer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from image_maintenance import policy, trusted, MaintenanceError, STATE, lock

COMMAND = Path('/usr/local/sbin/uniwares-image-maintenance')
POLICY = Path('/etc/uniwares-infrastructure/image-retention.json')
UNITS = Path('/etc/systemd/system')
INSTALL_ROOT = Path('/opt/uniwares-infrastructure/maintenance')
SERVICE = """[Unit]
Description=Reviewed application image retention
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/uniwares-image-maintenance daily
TimeoutStartSec=10min
KillMode=control-group
UMask=0077
Nice=10
IOSchedulingClass=idle
StandardOutput=journal
StandardError=journal
"""
TIMER = """[Unit]
Description=Daily application image retention

[Timer]
OnCalendar=*-*-* 03:00:00 UTC
RandomizedDelaySec=30min
Persistent=true
Unit=uniwares-image-maintenance.service

[Install]
WantedBy=timers.target
"""


def replace(path, content, mode):
    trusted(path.parent)
    if path.exists() or path.is_symlink():
        trusted(path)
    fd, temporary = tempfile.mkstemp(prefix='.maintenance-install-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            os.fchmod(stream.fileno(), mode)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install_command(source, locked=False):
    if not locked:
        with lock(STATE / 'image-maintenance.lock', 'UNIWARES_IMAGE_LOCK_FD'):
            return install_command(source, locked=True)
    trusted(source)
    body = ("#!/usr/bin/python3 -I\nimport runpy\nrunpy.run_path(" +
            repr(str(source)) + ",run_name='__main__')\n").encode()
    if COMMAND.exists():
        before = COMMAND.read_bytes()
        predecessor = COMMAND.with_name(COMMAND.name + '.previous-' + hashlib.sha256(before).hexdigest())
        if not predecessor.exists():
            replace(predecessor, before, 0o700)
    replace(COMMAND, body, 0o755)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--expected-policy-sha256')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise MaintenanceError('ROOT_OPERATOR_REQUIRED')
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise MaintenanceError('MAINTENANCE_CHECKSUM_MISMATCH')
    proposed = policy(args.policy)
    if POLICY.exists() and POLICY.read_bytes() != args.policy.read_bytes():
        if hashlib.sha256(POLICY.read_bytes()).hexdigest() != args.expected_policy_sha256:
            raise MaintenanceError('EXPECTED_POLICY_CHECKSUM_REQUIRED')
    for name, value in [('service', SERVICE), ('timer', TIMER)]:
        path = UNITS / ('uniwares-image-maintenance.' + name)
        if path.exists() and path.read_text() != value:
            raise MaintenanceError('REVIEW_EXISTING_TIMER_REQUIRED')
    print(json.dumps({'policy': proposed, 'sourceChecksum': args.sha256,
                      'timerActivation': 'separate operator action'}))
    if not args.apply:
        return
    STATE.mkdir(parents=True, mode=0o700, exist_ok=True)
    with lock(STATE / 'image-maintenance.lock', 'UNIWARES_IMAGE_LOCK_FD'):
        if POLICY.exists() and POLICY.read_bytes() != args.policy.read_bytes():
            if hashlib.sha256(POLICY.read_bytes()).hexdigest() != args.expected_policy_sha256:
                raise MaintenanceError('EXPECTED_POLICY_CHECKSUM_REQUIRED')
        directory = INSTALL_ROOT / args.sha256
        directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        trusted(directory)
        installed = directory / 'image_maintenance.py'
        if installed.exists() and installed.read_bytes() != raw:
            raise MaintenanceError('MAINTENANCE_CHECKSUM_MISMATCH')
        replace(installed, raw, 0o600)
        STATE.mkdir(parents=True, mode=0o700, exist_ok=True)
        POLICY.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        replace(POLICY, args.policy.read_bytes(), 0o600)
        install_command(installed, locked=True)
        for name, value in [('service', SERVICE), ('timer', TIMER)]:
            replace(UNITS / ('uniwares-image-maintenance.' + name), value.encode(), 0o644)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        # Deliberately no enable/start; do not change an operator's existing timer state.


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Maintenance installation stopped; inspect reviewed source/policy identities.') from None
