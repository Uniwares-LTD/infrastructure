#!/usr/bin/python3 -I
"""Fixed protocol for root-owned application control code; no uploaded scripts."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

REGISTRY = Path('/etc/uniwares-infrastructure/apps')
CONTROL = Path('/opt/uniwares-control')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1'}


def trusted(path):
    for item in [path, *path.parents]:
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Untrusted control path')


def validate_request(request):
    required = {'version', 'project', 'environment', 'action', 'configurationHash'}
    if not isinstance(request, dict) or type(request.get('version')) is not int or request['version'] != 1:
        raise ValueError('Invalid protocol')
    action = request.get('action')
    expected = required | ({'image', 'commit'} if action == 'deploy' else set())
    if set(request) != expected or action not in ('deploy', 'check', 'rollback'):
        raise ValueError('Invalid operation')
    if request['environment'] != 'staging':
        raise ValueError('Only staging is enabled')
    if not isinstance(request['project'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', request['project']):
        raise ValueError('Invalid project')
    if not isinstance(request['configurationHash'], str) or not re.fullmatch(r'[a-f0-9]{64}', request['configurationHash']):
        raise ValueError('Invalid configuration identity')
    if action == 'deploy':
        if not isinstance(request['image'], str) or not re.fullmatch(r'ghcr.io/[a-z0-9_.-]+/[a-z0-9_.-]+@sha256:[a-f0-9]{64}', request['image']):
            raise ValueError('Immutable image required')
        if not isinstance(request['commit'], str) or not re.fullmatch(r'[a-f0-9]{40}', request['commit']):
            raise ValueError('Invalid release commit')


def command(request):
    validate_request(request)
    registration = REGISTRY / (request['project'] + '.json')
    trusted(registration)
    installed = json.loads(registration.read_text())
    revision = installed['revision']
    if not re.fullmatch(r'[a-f0-9]{64}', revision):
        raise ValueError('Invalid installed revision')
    source = CONTROL / request['project'] / revision
    trusted(source)
    for path in source.rglob('*'):
        trusted(path)
    configuration = source / 'deploy/environments/staging.json'
    config = json.loads(configuration.read_text())
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if request['configurationHash'] != digest:
        raise ValueError('Installed configuration differs; operator update required')
    if json.loads((source / 'project.config.json').read_text())['slug'] != request['project']:
        raise ValueError('Installed project mismatch')
    args = ['/bin/bash', str(source / 'scripts/deploy/vps.sh'), request['action'], 'staging', '--apply']
    if request['action'] == 'deploy':
        if request['image'].split('@')[0] != config['deployment']['imageRepository']:
            raise ValueError('Image repository mismatch')
        args += [request['image'], request['commit']]
    return args


def main():
    if len(sys.argv) != 1 or os.geteuid() != 0:
        raise ValueError('Installed scoped dispatcher required; no arguments')
    raw = sys.stdin.buffer.read(16385)
    if len(raw) > 16384:
        raise ValueError('Request too large')
    args = command(json.loads(raw))
    return subprocess.run(args, cwd='/', env=ENV, stdin=subprocess.DEVNULL, timeout=1200).returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit('Deployment request failed; inspect configuration and installed control revision (private details suppressed)')
