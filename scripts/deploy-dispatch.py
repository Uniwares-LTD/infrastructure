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
import signal
import time
import tempfile
from contextlib import contextmanager

REGISTRY = Path('/etc/uniwares-infrastructure/apps')
CONTROL = Path('/opt/uniwares-control')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1'}


class Rejection(ValueError):
    def __init__(self, code, revision=None, digest=None):
        self.code = code
        self.revision = revision
        self.digest = digest
        super().__init__(code)


def trusted(path):
    for item in [path, *path.parents]:
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise Rejection('UNTRUSTED_CONTROL')


def validate_request(request):
    required = {'version', 'project', 'environment', 'action', 'configurationHash'}
    if not isinstance(request, dict) or type(request.get('version')) is not int or request['version'] not in (1, 2):
        raise ValueError('Invalid protocol')
    action = request.get('action')
    expected = required | ({'image', 'commit'} if action == 'deploy' else set())
    if request['version'] == 2 and 'requiredCapabilities' in request:
        capabilities = request['requiredCapabilities']
        if not isinstance(capabilities, list) or len(capabilities) > 16 or any(
                not isinstance(item, str) or not re.fullmatch(r'[a-z][a-z0-9-]{1,63}', item) for item in capabilities):
            raise ValueError('Invalid capabilities')
        expected.add('requiredCapabilities')
    if set(request) != expected or action not in ('deploy', 'check', 'rollback', 'preflight'):
        raise ValueError('Invalid operation')
    if request['environment'] not in (('staging',) if request['version'] == 1 else ('staging', 'prod')):
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


def installed_state(request):
    try:
        validate_request(request)
    except (ValueError, TypeError):
        raise Rejection('INVALID_REQUEST') from None
    registration = REGISTRY / (request['project'] + '.json')
    try:
        trusted(registration)
    except FileNotFoundError:
        raise Rejection('MISSING_REGISTRATION') from None
    installed = json.loads(registration.read_text())
    revision = installed['revision']
    if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{64}', revision):
        raise Rejection('UNTRUSTED_CONTROL')
    source = CONTROL / request['project'] / revision
    trusted(source)
    for path in source.rglob('*'):
        trusted(path)
    if request.get('requiredCapabilities'):
        try:
            installed_contract = json.loads((source / 'deploy/contract.json').read_text())
            if not set(request['requiredCapabilities']) <= set(installed_contract['requiredCapabilities']):
                raise Rejection('UNSUPPORTED_CAPABILITY')
            require_lock_capability(source)
        except (OSError, ValueError, KeyError, TypeError):
            raise Rejection('UNSUPPORTED_CAPABILITY') from None
    config = json.loads((source / ('deploy/environments/' + ('production' if request['environment'] == 'prod' else request['environment']) + '.json')).read_text())
    if json.loads((source / 'project.config.json').read_text())['slug'] != request['project']:
        raise Rejection('UNTRUSTED_CONTROL')
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return source, config, revision, digest


def response(code, request=None, revision=None, digest=None):
    # Only fixed codes and validated hexadecimal identities cross this boundary.
    requested = request.get('configurationHash') if isinstance(request, dict) else None
    if not isinstance(requested, str) or not re.fullmatch(r'[a-f0-9]{64}', requested):
        requested = None
    return dict(version=2 if isinstance(request, dict) and request.get('version') == 2 else 1, code=code, compatible=code == 'COMPATIBLE',
                installedRevision=revision, installedConfigurationHash=digest,
                requestedConfigurationHash=requested)


def preflight(request):
    source, _, revision, digest = installed_state(request)
    if request['version'] == 2:
        require_lock_capability(source)
    return response('COMPATIBLE' if request['configurationHash'] == digest else
                    'CONFIGURATION_MISMATCH', request, revision, digest)


def command(request):
    source, config, revision, digest = installed_state(request)
    if request['configurationHash'] != digest:
        raise Rejection('CONFIGURATION_MISMATCH', revision, digest)
    if request['action'] == 'preflight':
        raise Rejection('INVALID_REQUEST')  # Never execute a host script for preflight.
    args = ['/bin/bash', str(source / 'scripts/deploy/vps.sh'), request['action'], ('production' if request['environment'] == 'prod' else request['environment']), '--apply']
    if request['action'] == 'deploy':
        if request['image'].split('@')[0] != config['deployment']['imageRepository']:
            raise Rejection('IMAGE_REPOSITORY_MISMATCH')
        args += [request['image'], request['commit']]
    return args


STATE = Path('/var/lib')
LOCK_WAIT = 300
OPERATION_TIMEOUT = 1200


@contextmanager
def operation_lock(project):
    import fcntl
    path = STATE / project / 'operation.lock'
    trusted(path.parent)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
            raise Rejection('UNTRUSTED_CONTROL')
        deadline = time.monotonic() + LOCK_WAIT
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise Rejection('LOCK_TIMEOUT') from None
                time.sleep(0.1)
        yield fd
    finally:
        os.close(fd)


def require_lock_capability(source):
    try:
        contract = json.loads((source / 'deploy/contract.json').read_text())
    except (OSError, ValueError):
        raise Rejection('UNSUPPORTED_CAPABILITY') from None
    if contract.get('version') != 1 or 'operation-lock-v1' not in contract.get('requiredCapabilities', []):
        raise Rejection('UNSUPPORTED_CAPABILITY')
    supported = {'operation-lock-v1', 'image-retention-v1', 'data-operations-v1'}
    if not set(contract.get('requiredCapabilities', [])) <= supported:
        raise Rejection('UNSUPPORTED_CAPABILITY')
    if 'image-retention-v1' in contract['requiredCapabilities']:
        try:
            directory = Path(__file__).resolve().parent
            trusted(directory)
            sys.path.insert(0, str(directory))
            from image_maintenance import policy, Maintenance
            project = json.loads((source / 'project.config.json').read_text())['slug']
            Maintenance(policy()).enrolled(project)
            trusted(Path('/usr/local/sbin/uniwares-image-maintenance'))
        except Exception:
            raise Rejection('UNSUPPORTED_CAPABILITY') from None



def record_operation(request, status):
    directory = STATE / request['project']
    fd, temporary = tempfile.mkstemp(prefix='.operation-', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump({'version': 2, 'status': status, 'action': request['action'],
                       'configurationHash': request['configurationHash']}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / 'operation-status.json')
        directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def execute_locked(request):
    with operation_lock(request['project']) as fd:
        return execute_with_lock(request, fd)


def execute_with_lock(request, fd, timeout=OPERATION_TIMEOUT):
    source, _, _, _ = installed_state(request)
    require_lock_capability(source)
    args = command(request)
    env = dict(ENV, UNIWARES_OPERATION_LOCK_FD=str(fd), UNIWARES_DISPATCHED='1')
    if 'data-operations-v1' in json.loads((source / 'deploy/contract.json').read_text()).get('requiredCapabilities', []):
        gate=Path(__file__).with_name('data-operation-gate.py');trusted(gate)
        env['UNIWARES_DATA_GATE']=str(gate)
    def interrupted(signum, frame):
        raise InterruptedError('Operation interrupted')
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    process = None
    try:
        record_operation(request, 'unknown')
        process = subprocess.Popen(args, cwd='/', env=env, stdin=subprocess.DEVNULL,
                                   pass_fds=(fd,), start_new_session=True)
        status = process.wait(timeout=timeout)
        record_operation(request, 'completed' if status == 0 else 'failed')
        if status == 0 and request['action'] in ('deploy', 'rollback') and 'image-retention-v1' in json.loads((source / 'deploy/contract.json').read_text()).get('requiredCapabilities', []):
            # Readiness and the application ledger commit precede optional maintenance.
            try:
                from image_maintenance import Maintenance, policy, lock, STATE as maintenance_state
                engine = Maintenance(policy())
                if 'image-retention-v1' in json.loads((source / 'deploy/contract.json').read_text()).get('requiredCapabilities', []):
                    with lock(maintenance_state / 'image-maintenance.lock', 'UNIWARES_IMAGE_LOCK_FD'):
                        # The caller still owns fd; never acquire a second app lock.
                        engine.config = policy()
                        ledger = engine.ledger(request['project'])
                        current = engine.releases / request['project'] / ('production' if request['environment'] == 'prod' else request['environment']) / 'current'
                        if not any(x['snapshot'] == current.resolve().name for x in ledger['activations']):
                            raise ValueError('RELEASE_LEDGER_MISSING')
                        result = engine.cleanup(request['project'])
                        print('maintenance=' + result['status'])
            except Exception:
                print('maintenance=warning operator-inspection-required')
        return status
    except BaseException:
        # Kill all descendants and reap before releasing the lock. Never retry blindly.
        if process is None:
            raise
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        record_operation(request, 'unknown')
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def handle(request):
    try:
        if isinstance(request, dict) and type(request.get('version')) is int and request['version'] == 2 and request.get('action') in ('plan','apply','status','capabilities','maintenance','backup','restore','migrations','migrate'):
            directory = Path(__file__).resolve().parent
            trusted(directory)
            sys.path.insert(0,str(directory))
            import operation_engine
            try:
                result=operation_engine.route(sys.modules[__name__],request)
            except ValueError as error:
                allowed={'OWNER_ACTION_REQUIRED','HOST_STATE_CHANGED','READBACK_REQUIRED','APPROVAL_REPLAY','ADMIN_NOT_ENROLLED','APPROVAL_EXPIRED','APPROVAL_IDENTITY_REJECTED','CONTROLLER_CHANGED','PLAN_DIGEST_MISMATCH','PLAN_IDENTITY_MISMATCH','OTHER_ENVIRONMENT_CHANGED','HOST_STATE_CHANGED','UNSUPPORTED_CAPABILITY','RESOLVED_PLAN_REQUIRES_NEW_APPROVAL','REQUEST_ID_REUSED'}
                code=str(error) if str(error) in allowed else 'OPERATION_REJECTED'
                raise Rejection(code) from None
            print(json.dumps(result,separators=(',',':')))
            return 0
        try:
            validate_request(request)
        except (ValueError, TypeError):
            raise Rejection('INVALID_REQUEST') from None
        if request['version'] == 2 and request['action'] != 'preflight':
            return execute_locked(request)
        result = preflight(request)
        if not result['compatible'] or request['action'] == 'preflight':
            print(json.dumps(result, separators=(',', ':')))
            return 0 if result['compatible'] else 2
        args = command(request)  # Re-read at the execution boundary, never trust an earlier preflight.
        return subprocess.run(args, cwd='/', env=ENV, stdin=subprocess.DEVNULL, timeout=1200).returncode
    except Rejection as error:
        print(json.dumps(response(error.code, request, error.revision, error.digest), separators=(',', ':')))
        return 2
    except Exception:
        print(json.dumps(response('INTERNAL_FAILURE', request), separators=(',', ':')))
        return 1


def main():
    if len(sys.argv) != 1 or os.geteuid() != 0:
        raise Rejection('INVALID_REQUEST')
    raw = sys.stdin.buffer.read(48*1024*1024+1)
    if len(raw) > 48*1024*1024:
        raise Rejection('INVALID_REQUEST')
    try:
        request = json.loads(raw)
    except (ValueError, UnicodeError):
        raise Rejection('INVALID_REQUEST') from None
    return handle(request)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Rejection as error:
        print(json.dumps(response(error.code)))
        sys.exit(2)
    except Exception:
        print(json.dumps(response('INTERNAL_FAILURE')))
        sys.exit(1)
