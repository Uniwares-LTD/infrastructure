#!/usr/bin/python3 -I
"""Root-only, recoverable staging runtime/control update. Never starts services."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

PUBLIC = {'DIFY_MODE', 'DIFY_BASE_URL', 'DIFY_CONSOLE_URL', 'DIFY_WORKSPACE_ID',
          'DIFY_ORCHESTRATORS_JSON', 'MCP_ENABLED', 'MCP_CLIENTS_JSON',
          'MCP_ALLOWED_HOSTS_JSON', 'RUN_MCP_CLIENT_ID',
          'PERSONA_COMPLETION_MODE', 'PERSONA_COMPLETION_BASE_URL'}
PRIVATE = {'DIFY_MANAGEMENT_KEY', 'DIFY_CREDENTIAL_ENCRYPTION_KEY', 'PERSONA_COMPLETION_API_KEY'}


def sync_directory(path):
    if os.name == 'posix':
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def atomic(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.update-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            if hasattr(os, 'fchmod'):
                os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def runtime_values(raw):
    values = {}
    for line in raw.splitlines():
        if not line or line.startswith('#'):
            continue
        key, value = line.split('=', 1)
        if key in values:
            raise ValueError('Duplicate runtime key')
        values[key] = value
    return values


def merge(old_public, new_public, old_runtime, private):
    before, after = json.loads(json.dumps(old_public)), json.loads(json.dumps(new_public))
    for config in (before, after):
        for key in PUBLIC:
            config['runtime'].pop(key, None)
    if before != after:
        raise ValueError('Only optional AI/MCP runtime settings may change')
    if not isinstance(private, dict) or not private:
        raise ValueError('Private input must be a nonempty object')
    for key, value in private.items():
        if key not in PRIVATE and not re.fullmatch(r'(DIFY_KEY_|MCP_TOKEN_)[A-Z0-9_]+', key):
            raise ValueError('Private input contains a forbidden field')
        if not isinstance(value, str) or not value or any(c in value for c in '\r\n\0'):
            raise ValueError('Invalid private value')
    values = runtime_values(old_runtime)
    values.update({k: v for k, v in new_public['runtime'].items() if v is not None})
    values.update(private)
    if values.get('FIREBASE_AUTH_EMULATOR_HOST') or values.get('APP_ENV') != 'staging':
        raise ValueError('Local configuration forbidden')
    if values.get('PAYMENTS_MODE', 'disabled') != 'disabled' or values.get('ASSET_STORE', 'mongo') != 'mongo':
        raise ValueError('Payments and storage changes are outside this update')
    if values.get('DIFY_MODE') == 'live':
        if not values.get('DIFY_MANAGEMENT_KEY') or not re.fullmatch(r'[a-fA-F0-9]{64}', values.get('DIFY_CREDENTIAL_ENCRYPTION_KEY', '')):
            raise ValueError('Live Dify requires management and explicit encryption credentials')
        for item in json.loads(values.get('DIFY_ORCHESTRATORS_JSON', '[]')):
            if not values.get(item.get('keyEnv', '')):
                raise ValueError('Missing Dify execution credential')
    return ''.join(f'{k}={v}\n' for k, v in sorted(values.items()))


def recover(journal, runtime, registration):
    if not journal.exists():
        return False
    # Registration stays disabled until every previous private byte is restored.
    atomic(registration, b'{"revision":"update-in-progress"}\n')
    atomic(runtime, (journal / 'runtime.env').read_bytes())
    atomic(registration, (journal / 'registration.json').read_bytes())
    shutil.rmtree(journal)
    sync_directory(journal.parent)
    return True


def apply_change(journal, runtime, registration, content, revision, checkpoint=lambda _: None):
    # Publish the complete journal before disabling dispatch or changing runtime.
    with tempfile.TemporaryDirectory(prefix='.config-backup-', dir=journal.parent) as temp:
        backup = Path(temp) / 'backup'
        backup.mkdir(mode=0o700)
        atomic(backup / 'runtime.env', runtime.read_bytes())
        atomic(backup / 'registration.json', registration.read_bytes())
        backup.rename(journal)
        sync_directory(journal.parent)
    try:
        atomic(registration, b'{"revision":"update-in-progress"}\n')
        checkpoint('disabled')
        atomic(runtime, content.encode())
        checkpoint('runtime')
        atomic(registration, (json.dumps({'revision': revision}) + '\n').encode())
        checkpoint('registration')
    except BaseException:
        recover(journal, runtime, registration)
        raise
    # Keep previous private bytes for an explicit operator rollback, outside releases.
    journal.rename(journal.with_name('config-previous-' + revision))
    sync_directory(journal.parent)


def check_encryption_state(slug, old, new):
    old_values, new_values = runtime_values(old), runtime_values(new)
    if old_values.get('DIFY_CREDENTIAL_ENCRYPTION_KEY') == new_values.get('DIFY_CREDENTIAL_ENCRYPTION_KEY'):
        return
    if old_values.get('DIFY_MODE', 'disabled') != 'disabled' or old_values.get('MCP_ENABLED', 'false') != 'false':
        raise ValueError('Encryption migration requires a separate drained-writer procedure')
    probe = """const {MongoClient}=require('mongodb');
const c=new MongoClient(process.env.MONGODB_URI,{serverSelectionTimeoutMS:10000});
(async()=>{try{await c.connect();const d=c.db(process.env.MONGODB_DATABASE);
const a=await d.collection('difyCredentials').findOne({}, {projection:{_id:1}});
const b=await d.collection('runCapabilities').findOne({expiresAt:{$gt:new Date()}},{projection:{_id:1}});
process.exitCode=(a||b)?2:0;}catch{process.exitCode=3;}finally{await c.close();}})();"""
    # Discover only this app's current container; never print its environment.
    result = subprocess.run(['docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project='+slug+'-staging',
                             '--filter', 'label=com.docker.compose.service=app'], capture_output=True, text=True, check=True)
    ids = result.stdout.split()
    if len(ids) != 1 or not re.fullmatch(r'[a-f0-9]+', ids[0]):
        raise ValueError('One running app required for encryption compatibility check')
    result = subprocess.run(['docker', 'exec', ids[0], 'node', '-e', probe], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('Encryption update refused: existing protected records or unverified database state')


def main():
    import fcntl
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--expected-revision', required=True)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--private-input', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', args.project):
        raise ValueError('Root operator and valid project required')
    if not re.fullmatch(r'[a-f0-9]{64}', args.expected_revision):
        raise ValueError('Expected installed bundle SHA-256 required')
    os.umask(0o077)
    spec = importlib.util.spec_from_file_location('bootstrap', Path(__file__).with_name('bootstrap-deploy.py'))
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
    state = Path('/var/lib') / args.project
    registration = Path('/etc/uniwares-infrastructure/apps') / (args.project+'.json')
    root = Path('/etc') / args.project
    runtime = root / 'staging/runtime.env'
    journal = state / 'config-update-pending'
    for path in (state, registration, runtime, journal, state / 'operation.lock'):
        bootstrap.safe_parent(path)
    with (state / 'operation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if journal.exists():
            for member in journal.rglob('*'):
                bootstrap.safe_parent(member)
            prior = json.loads((journal / 'registration.json').read_text())['revision']
            if not args.recover or not args.apply or prior != args.expected_revision:
                raise ValueError('Interrupted update: use --recover --apply with its previous revision')
            recover(journal, runtime, registration)
            print('Previous runtime/control selection restored; running services unchanged')
            return
        if args.recover:
            raise ValueError('No pending update')
        installed = json.loads(registration.read_text())['revision']
        if installed != args.expected_revision:
            raise ValueError('Installed revision changed')
        if not args.bundle or not args.sha256 or not args.private_input:
            raise ValueError('Bundle, digest and protected private input required')
        if not re.fullmatch(r'[a-f0-9]{64}', args.sha256):
            raise ValueError('Invalid candidate digest')
        bootstrap.safe_parent(args.private_input.absolute())
        if args.private_input.stat().st_mode & 0o077:
            raise ValueError('Private input must be accessible only to root')
        old_source = Path('/opt/uniwares-control') / args.project / installed
        target = old_source.parent / args.sha256
        bootstrap.safe_parent(old_source)
        bootstrap.safe_parent(target)
        with tempfile.TemporaryDirectory(prefix='uniwares-update-', dir='/root') as temp:
            source = bootstrap.extract(args.bundle, args.sha256, Path(temp))
            if json.loads((source / 'project.config.json').read_text())['slug'] != args.project:
                raise ValueError('Bundle project mismatch')
            old_public = json.loads((old_source / 'deploy/environments/staging.json').read_text())
            new_public = json.loads((source / 'deploy/environments/staging.json').read_text())
            content = merge(old_public, new_public, runtime.read_text(), json.loads(args.private_input.read_text()))
            candidate = Path(temp) / 'runtime.env'
            candidate.write_text(content)
            result = subprocess.run(['python3', '-IB', str(source / 'scripts/deploy/config.py'), str(root), 'staging', str(candidate)], capture_output=True)
            if result.returncode:
                raise ValueError('Candidate runtime validation failed')
            check_encryption_state(args.project, runtime.read_text(), content)
            if target.exists():
                for member in target.rglob('*'):
                    bootstrap.safe_parent(member)
                if bootstrap.tree_contents(target) != bootstrap.tree_contents(source):
                    raise ValueError('Existing candidate bundle differs')
            if (state / ('config-previous-'+args.sha256)).exists():
                raise ValueError('Prior update for this bundle exists; inspect before retrying')
            print('Preview passed: optional AI/MCP settings only; runtime and encryption validation passed')
            if not args.apply:
                return
            if not target.exists():
                with tempfile.TemporaryDirectory(prefix='.update-bundle-', dir=target.parent) as installing:
                    complete = Path(installing) / 'complete'
                    shutil.copytree(source, complete)
                    complete.rename(target)
                    sync_directory(target.parent)
            apply_change(journal, runtime, registration, content, args.sha256)
            print('AI_CONFIGURATION_PREPARED; application release remains separate')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Configuration update stopped; inspect checkpoint/permissions; private details suppressed')
