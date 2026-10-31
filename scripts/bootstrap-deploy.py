#!/usr/bin/python3 -I
"""Operator-reviewed installation; preview by default, no daemon/provider changes."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'LC_ALL': 'C'}
ACCOUNT = 'uniwares-deploy-user'


def extract(archive, digest, destination):
    if not re.fullmatch(r'[a-f0-9]{64}', digest):
        raise ValueError('Invalid bundle digest')
    # Copy into a root-only directory before verifying/extracting to prevent TOCTOU.
    copy = destination / 'verified.tar'
    with archive.open('rb') as source, copy.open('xb') as out:
        remaining = 130 * 1024 * 1024
        while chunk := source.read(min(1024 * 1024, remaining + 1)):
            remaining -= len(chunk)
            if remaining < 0:
                raise ValueError('Archive too large')
            out.write(chunk)
    if hashlib.sha256(copy.read_bytes()).hexdigest() != digest:
        raise ValueError('Bundle checksum mismatch')
    root = destination / 'source'
    root.mkdir(mode=0o700)
    allowed = {'package.json', 'package-lock.json', 'project.config.json', 'tsconfig.json', 'src', 'scripts', 'deploy', 'messages'}
    with tarfile.open(copy) as bundle:
        seen = set()
        total = 0
        for item in bundle.getmembers():
            path = PurePosixPath(item.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] not in allowed or item.name in seen:
                raise ValueError('Unsafe archive path')
            if not (item.isdir() or item.isfile()):
                raise ValueError('Archive links/special files forbidden')
            hidden = any(part.startswith('.') and not (part == '.well-known' and path.parts[:3] == ('src', 'app', '.well-known')) for part in path.parts)
            if (hidden or path.suffix in ('.pem', '.key', '.env') or
                    path.as_posix() == 'deploy/config.json' or 'secrets' in path.parts or
                    (path.suffix == '.json' and ('credentials' in path.name or 'service-account' in path.name))):
                raise ValueError('Private/hidden archive paths forbidden')
            total += item.size
            if total > 128 * 1024 * 1024:
                raise ValueError('Bundle too large')
            seen.add(item.name)
            target = root.joinpath(*path.parts)
            if item.isdir():
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with bundle.extractfile(item) as source, target.open('xb') as out:
                    shutil.copyfileobj(source, out)
                target.chmod(0o600)
    return root


def tree_contents(root):
    result = {}
    for path in root.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Unsafe installed bundle member')
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return result


def public_key(value):
    parts = value.strip().split()
    if len(parts) < 2 or parts[0] != 'ssh-ed25519' or '\n' in value.strip():
        raise ValueError('One plain Ed25519 public key required')
    blob = base64.b64decode(parts[1], validate=True)
    if len(blob) != 51 or blob[:19] != b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20':
        raise ValueError('Invalid Ed25519 public key')
    return parts[0] + ' ' + parts[1]


def safe_parent(path):
    for item in [path, *path.parents]:
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                raise ValueError('Unsafe installation path')


def main():
    import pwd
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--public-key', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise ValueError('Trusted root operator required')
    os.umask(0o077)
    key = public_key(args.public_key.read_text())
    dispatcher = Path(__file__).with_name('deploy-dispatch.py')
    safe_parent(dispatcher)
    installed_dispatcher = Path('/usr/local/sbin/uniwares-deploy')
    sudo_rule = Path('/etc/sudoers.d/uniwares-deploy')
    home = Path('/var/lib/uniwares-deploy-user')
    registration_root = Path('/etc/uniwares-infrastructure/apps')
    for path in (installed_dispatcher, sudo_rule, home, registration_root, Path('/opt/uniwares-control')):
        safe_parent(path)
    rule = 'uniwares-deploy-user ALL=(root) NOPASSWD: /usr/local/sbin/uniwares-deploy ""\n'
    authorized = 'restrict,command="/usr/bin/sudo -n /usr/local/sbin/uniwares-deploy" ' + key + '\n'
    try:
        account = pwd.getpwnam(ACCOUNT)
    except KeyError:
        account = None
    if account and (account.pw_dir != str(home) or account.pw_shell != '/bin/sh' or account.pw_uid == 0):
        raise ValueError('Existing deployment account differs; inspect without changing it')
    if account:
        groups = subprocess.check_output(['/usr/bin/id', '-nG', ACCOUNT], text=True).split()
        if set(groups) != {ACCOUNT}:
            raise ValueError('Existing deployment account has unexpected groups')
    # Initial account bootstrap must not copy a dispatcher without its modules/venv.
    # Preserve an existing controller; new hosts remain fail-closed until reviewed install.
    disabled = b"#!/usr/bin/python3\nprint('{\"compatible\":false,\"code\":\"CONTROLLER_INSTALL_REQUIRED\"}')\nraise SystemExit(2)\n"
    files = {sudo_rule: rule.encode(), home / '.ssh/authorized_keys': authorized.encode()}
    if not installed_dispatcher.exists():
        files[installed_dispatcher] = disabled
    for target, content in files.items():
        safe_parent(target)
        if target.exists() and target.read_bytes() != content:
            raise ValueError('Existing installation differs; explicit operator update required')
    with tempfile.TemporaryDirectory(prefix='uniwares-bootstrap-', dir='/root') as temporary:
        source = extract(args.bundle, args.sha256, Path(temporary))
        slug = json.loads((source / 'project.config.json').read_text())['slug']
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', slug):
            raise ValueError('Invalid project')
        target = Path('/opt/uniwares-control') / slug / args.sha256
        registration = registration_root / (slug + '.json')
        for path in (target, registration):
            safe_parent(path)
        registration_data = json.dumps({'revision': args.sha256}) + '\n'
        if registration.exists() and registration.read_text() != registration_data:
            raise ValueError('Existing project registration differs; review an explicit update')
        if target.exists():
            for member in target.rglob('*'):
                safe_parent(member)
            if tree_contents(target) != tree_contents(source):
                raise ValueError('Installed bundle incomplete or changed; inspect before resuming')
        draft = Path(temporary) / 'sudoers'
        draft.write_text(rule)
        subprocess.run(['/usr/sbin/visudo', '-cf', '/etc/sudoers'], env=ENV, check=True)
        subprocess.run(['/usr/sbin/visudo', '-cf', str(draft)], env=ENV, check=True)
        print('Preview: restricted shared account, forced-command public key, root-owned control bundle and exact sudo rule')
        if not args.apply:
            return
        if not account:
            subprocess.run(['/usr/sbin/useradd', '--system', '--user-group', '--home-dir', str(home), '--shell', '/bin/sh', ACCOUNT], env=ENV, check=True)
        if not target.exists():
            target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.install-', dir=target.parent) as staging:
                complete = Path(staging) / 'complete'
                shutil.copytree(source, complete)
                complete.rename(target)
        registration_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        new_rule = not sudo_rule.exists()
        for output, content in {**files, registration: registration_data.encode()}.items():
            output.parent.mkdir(parents=True, mode=0o755 if output.parent == home / '.ssh' else 0o700, exist_ok=True)
            if not output.exists():
                with output.open('xb') as file:
                    file.write(content)
            output.chmod(0o755 if output == installed_dispatcher else 0o440 if output == sudo_rule else 0o600)
        # Public-key authentication needs traversal, while ownership stays root.
        home.chmod(0o755)
        (home / '.ssh').chmod(0o755)
        (home / '.ssh/authorized_keys').chmod(0o644)
        try:
            subprocess.run(['/usr/sbin/visudo', '-cf', '/etc/sudoers'], env=ENV, check=True)
        except subprocess.CalledProcessError:
            if new_rule:
                sudo_rule.unlink()
            raise
        print('Installed control tooling only; prepare credentials/indexes separately, no application started')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit('Bootstrap failed; inspect operator inputs and any partial installation before resuming (private details suppressed)')
