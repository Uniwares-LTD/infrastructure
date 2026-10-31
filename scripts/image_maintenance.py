"""Root-owned Docker image retention. No registry writes, prune, or arbitrary shell."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time

POLICY = Path('/etc/uniwares-infrastructure/image-retention.json')
STATE = Path('/var/lib/uniwares-infrastructure')
APPS = Path('/var/lib')
RELEASES = Path('/opt')
CAPABILITY = 'image-retention-v1'
GIB = 1024 ** 3
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'LC_ALL': 'C'}
HEX = r'[a-f0-9]{64}'
REPOSITORY = r'[a-z0-9][a-z0-9.-]*(?::[0-9]{1,5})?/[a-z0-9_.-]+(?:/[a-z0-9_.-]+)*'
IMAGE = REPOSITORY + '@sha256:' + HEX


class MaintenanceError(ValueError):
    pass


def fail(code):
    raise MaintenanceError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def trusted(path):
    for item in [Path(path), *Path(path).parents]:
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            fail('UNTRUSTED_MAINTENANCE_STATE')


def read(path):
    trusted(path)
    if path.stat().st_size > 4 * 1024 * 1024:
        fail('MAINTENANCE_STATE_LIMIT')
    return json.loads(path.read_text())


def atomic(path, value):
    trusted(path.parent)
    if path.exists() or path.is_symlink():
        trusted(path)
    fd, name = tempfile.mkstemp(prefix='.maintenance-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(canonical(value) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def policy(path=POLICY):
    value = read(path)
    if set(value) != {'version', 'keepReleases', 'keepDays', 'minimumFreeGiB',
                      'targetFreeGiB', 'warnUsedPercent', 'projects'} or value['version'] != 1:
        fail('INVALID_RETENTION_POLICY')
    for key in ('keepReleases', 'keepDays', 'minimumFreeGiB', 'targetFreeGiB', 'warnUsedPercent'):
        if type(value[key]) is not int or value[key] < 1:
            fail('INVALID_RETENTION_POLICY')
    if value['targetFreeGiB'] < value['minimumFreeGiB'] or value['warnUsedPercent'] > 100:
        fail('INVALID_RETENTION_POLICY')
    if not isinstance(value['projects'], dict) or len(value['projects']) > 64:
        fail('INVALID_RETENTION_POLICY')
    repos = set()
    for project, item in value['projects'].items():
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', project):
            fail('INVALID_RETENTION_POLICY')
        if set(item) != {'imageRepository', 'environments', 'automatic'}:
            fail('INVALID_RETENTION_POLICY')
        if not re.fullmatch(REPOSITORY, item['imageRepository']):
            fail('INVALID_RETENTION_POLICY')
        if item['imageRepository'] in repos or type(item['automatic']) is not bool:
            fail('INVALID_RETENTION_POLICY')
        repos.add(item['imageRepository'])
        if not item['environments'] or any(k not in ('staging', 'prod') or
                v != ('production' if k == 'prod' else k) for k, v in item['environments'].items()):
            fail('INVALID_RETENTION_POLICY')
    return value


def run(args, timeout=60):
    # Capture privately and return fixed failures, never Docker stderr/config values.
    with tempfile.TemporaryFile() as out:
        try:
            result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=out,
                                    stderr=subprocess.DEVNULL, env=ENV, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired):
            fail('DOCKER_OUTCOME_UNKNOWN')
        out.seek(0)
        raw = out.read(4 * 1024 * 1024 + 1)
    if result.returncode:
        fail('DOCKER_OPERATION_FAILED')
    if len(raw) > 4 * 1024 * 1024:
        fail('DOCKER_OUTPUT_LIMIT')
    return raw.decode()


class Docker:
    def root(self):
        root = run(['docker', 'info', '--format', '{{.DockerRootDir}}']).strip()
        if not root.startswith('/'):
            fail('INVALID_DOCKER_ROOT')
        return Path(root)

    def inventory(self):
        ids = sorted(set(run(['docker', 'image', 'ls', '-aq', '--no-trunc']).split()))
        images = []
        for identity in ids:
            if not re.fullmatch('sha256:' + HEX, identity):
                fail('INVALID_IMAGE_ID')
            raw = run(['docker', 'image', 'inspect', '--format',
                       '{{json .Id}} {{json .RepoTags}} {{json .RepoDigests}}', identity]).strip()
            decoder = json.JSONDecoder()
            fields = []
            for _ in range(3):
                value, end = decoder.raw_decode(raw.lstrip())
                fields.append(value)
                raw = raw.lstrip()[end:]
            image_id, tags, digests = fields
            refs = sorted(set((tags or []) + (digests or [])))
            if image_id != identity or any(not isinstance(x, str) for x in refs):
                fail('INVALID_IMAGE_METADATA')
            images.append({'id': identity, 'references': refs})
        used = set()
        for container in run(['docker', 'ps', '-aq', '--no-trunc']).split():
            if not re.fullmatch(HEX, container):
                fail('INVALID_CONTAINER_ID')
            identity = run(['docker', 'container', 'inspect', '--format', '{{.Image}}', container]).strip()
            if not re.fullmatch('sha256:' + HEX, identity):
                fail('INVALID_IMAGE_ID')
            used.add(identity)
        return images, used

    def remove(self, reference):
        # Delete one reviewed reference; never force a container conflict.
        run(['docker', 'image', 'rm', '--', reference], timeout=90)


def verify_fd(fd, path):
    expected = path.lstat()
    inherited = os.fstat(fd)
    if (not stat.S_ISREG(inherited.st_mode) or inherited.st_uid != 0 or
            inherited.st_mode & 0o077 or
            (expected.st_dev, expected.st_ino) != (inherited.st_dev, inherited.st_ino)):
        fail('INVALID_MAINTENANCE_LOCK')
    probe = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            fail('INVALID_MAINTENANCE_LOCK')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(probe)


@contextmanager
def lock(path, variable, wait=30):
    trusted(path.parent)
    inherited = os.environ.get(variable)
    if inherited is not None:
        if not inherited.isdigit():
            fail('INVALID_MAINTENANCE_LOCK')
        fd = int(inherited)
        verify_fd(fd, path)
        yield fd
        return
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
            fail('INVALID_MAINTENANCE_LOCK')
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    fail('MAINTENANCE_BUSY')
                time.sleep(.1)
        yield fd
    finally:
        os.close(fd)


def values(path):
    trusted(path)
    if path.stat().st_size > 65536:
        fail('INVALID_RELEASE_IDENTITY')
    result = {}
    for line in path.read_text().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            if key in ('IMAGE_DIGEST', 'RELEASE_COMMIT', 'DEPLOY_ENV'):
                if key in result:
                    fail('INVALID_RELEASE_IDENTITY')
                result[key] = value
    if not re.fullmatch(IMAGE, result.get('IMAGE_DIGEST', '')) or not re.fullmatch(
            r'[a-f0-9]{40}', result.get('RELEASE_COMMIT', '')):
        fail('INVALID_RELEASE_IDENTITY')
    return result


class Maintenance:
    def __init__(self, config, docker=None, state=STATE, apps=APPS, releases=RELEASES):
        self.config = config
        self.docker = docker or Docker()
        self.state, self.apps, self.releases = Path(state), Path(apps), Path(releases)

    def enrolled(self, project):
        if project not in self.config['projects']:
            fail('RETENTION_NOT_ENROLLED')
        return self.config['projects'][project]

    def disk(self, project):
        roots = [self.docker.root(), self.releases / project, self.apps / project]
        devices, measurements = set(), []
        for root in roots:
            device = root.stat().st_dev
            if device in devices:
                continue
            devices.add(device)
            fs = os.statvfs(root)
            total, free = fs.f_blocks * fs.f_frsize, fs.f_bavail * fs.f_frsize
            used = round(100 * (1 - free / total), 2)
            measurements.append({'filesystem': str(root), 'freeBytes': free,
                                 'usedPercent': used, 'warning': used >= self.config['warnUsedPercent']})
        return measurements

    def check_space(self, project):
        self.enrolled(project)
        result = self.disk(project)
        if any(x['freeBytes'] < self.config['minimumFreeGiB'] * GIB for x in result):
            fail('INSUFFICIENT_DISK_SPACE')
        return result

    def ledger(self, project):
        path = self.apps / project / 'image-release-ledger.json'
        value = read(path) if path.exists() else {'version': 1, 'activations': []}
        if set(value) != {'version', 'activations'} or value['version'] != 1:
            fail('INVALID_RELEASE_LEDGER')
        repo = self.enrolled(project)['imageRepository']
        for entry in value['activations']:
            if set(entry) != {'environment', 'snapshot', 'image', 'commit', 'activatedAt'}:
                fail('INVALID_RELEASE_LEDGER')
            if (entry['environment'] not in self.enrolled(project)['environments'] or
                    not re.fullmatch(r'[a-f0-9]{40}\.[A-Za-z0-9]+', entry['snapshot']) or
                    not re.fullmatch(re.escape(repo) + '@sha256:' + HEX, entry['image']) or
                    not re.fullmatch(r'[a-f0-9]{40}', entry['commit']) or
                    type(entry['activatedAt']) is not int or entry['activatedAt'] < 0):
                fail('INVALID_RELEASE_LEDGER')
        return value

    def snapshots(self, project):
        found = []
        for environment, target in self.enrolled(project)['environments'].items():
            base = self.releases / project / target
            if not base.exists():
                continue
            trusted(base)
            selected = set()
            for name in ('current', 'previous'):
                link = base / name
                if link.is_symlink():
                    resolved = link.resolve(strict=True)
                    if resolved.parent != base / 'releases':
                        fail('INVALID_RELEASE_PATH')
                    selected.add(resolved.name)
                elif link.exists():
                    fail('INVALID_RELEASE_PATH')
            directory = base / 'releases'
            if not directory.exists():
                continue
            trusted(directory)
            for snapshot in sorted(directory.iterdir()):
                trusted(snapshot)
                if not snapshot.is_dir() or not re.fullmatch(r'[a-f0-9]{40}\.[A-Za-z0-9]+', snapshot.name):
                    fail('INVALID_RELEASE_PATH')
                # Failed creation before compose.env is complete is not deletion evidence.
                if not (snapshot / 'compose.env').exists():
                    fail('INCOMPLETE_RELEASE_SNAPSHOT')
                entry = values(snapshot / 'compose.env')
                if entry.get('DEPLOY_ENV') != target or not entry['IMAGE_DIGEST'].startswith(
                        self.enrolled(project)['imageRepository'] + '@'):
                    fail('INVALID_RELEASE_IDENTITY')
                found.append({'environment': environment, 'snapshot': snapshot.name,
                              'image': entry['IMAGE_DIGEST'], 'commit': entry['RELEASE_COMMIT'],
                              'selected': snapshot.name in selected})
        return found

    def record(self, project, environment):
        marker = self.apps / project / 'image-ledger-pending.json'
        atomic(marker, {'status': 'unknown'})
        entries = self.snapshots(project)
        target = self.enrolled(project)['environments'].get(environment)
        if target is None:
            fail('INVALID_ENVIRONMENT')
        current = (self.releases / project / target / 'current').resolve(strict=True).name
        entry = next((x for x in entries if x['environment'] == environment and x['snapshot'] == current), None)
        if entry is None:
            fail('INVALID_RELEASE_IDENTITY')
        ledger = self.ledger(project)
        ledger['activations'].append({k: entry[k] for k in ('environment', 'snapshot', 'image', 'commit')} |
                                     {'activatedAt': int(time.time())})
        if len(canonical(ledger)) > 4 * 1024 * 1024:
            fail('MAINTENANCE_STATE_LIMIT')
        atomic(self.apps / project / 'image-release-ledger.json', ledger)
        marker.unlink()

    def protections(self, project, now):
        if (self.apps / project / 'image-ledger-pending.json').exists():
            fail('RELEASE_LEDGER_READBACK_REQUIRED')
        ledger = self.ledger(project)['activations']
        snapshots = self.snapshots(project)
        protected = {}
        def protect(image, reason):
            protected.setdefault(image, set()).add(reason)
        cutoff = now - self.config['keepDays'] * 86400
        known = {(x['environment'], x['snapshot'], x['image'], x['commit']) for x in ledger}
        for environment in self.enrolled(project)['environments']:
            history = sorted((x for x in reversed(ledger) if x['environment'] == environment),
                             key=lambda x: x['activatedAt'], reverse=True)
            seen = set()
            for entry in history:
                key = entry['snapshot']
                if key not in seen and len(seen) < self.config['keepReleases']:
                    protect(entry['image'], 'retained-release')
                seen.add(key)
                if entry['activatedAt'] >= cutoff:
                    protect(entry['image'], 'retention-window')
        for entry in snapshots:
            identity = tuple(entry[k] for k in ('environment', 'snapshot', 'image', 'commit'))
            if entry['selected']:
                protect(entry['image'], 'current-or-previous')
            if identity not in known:
                protect(entry['image'], 'legacy-unverified')
        pending = self.apps / project / 'config-update-pending'
        if pending.exists() or pending.is_symlink():
            fail('PENDING_CONFIGURATION_RECOVERY')
        operation = self.apps / project / 'operation-status.json'
        if operation.exists():
            status = read(operation).get('status')
            if status not in ('completed', 'failed'):
                fail('OPERATION_OUTCOME_UNKNOWN')
        plans = self.apps / project / 'operation-plans'
        if plans.exists():
            trusted(plans)
            for path in plans.glob('*.plan.json'):
                envelope = read(path)
                if set(envelope) != {'plan', 'digest'} or digest(envelope['plan']) != envelope['digest']:
                    fail('INVALID_OPERATION_PLAN')
                plan = envelope['plan']
                if plan.get('project') != project or not re.fullmatch(IMAGE, plan.get('image', '')):
                    fail('INVALID_OPERATION_PLAN')
                journal = path.with_name(path.name.replace('.plan.json', '.journal.json'))
                if not journal.exists() or read(journal).get('status') != 'completed':
                    protect(plan['image'], 'pending-operation')
        return protected, snapshots, {x['image'] for x in ledger}

    def preview(self, project, legacy=()):
        repo = self.enrolled(project)['imageRepository']
        protected, snapshots, known = self.protections(project, int(time.time()))
        images, used = self.docker.inventory()
        candidates, skipped, local = [], [], set()
        requested = set(legacy)
        if any(not re.fullmatch(re.escape(repo) + '@sha256:' + HEX, ref) for ref in requested):
            fail('INVALID_LEGACY_REFERENCE')
        for image in images:
            refs = image['references']
            ours = [r for r in refs if r.startswith(repo + '@') or r.startswith(repo + ':')]
            if not ours:
                continue
            local.update(refs)
            reasons = set()
            if image['id'] in used:
                reasons.add('container-reference')
            if len(ours) != len(refs):
                reasons.add('other-repository-reference')
            for ref in refs:
                reasons.update(reason for reason in protected.get(ref, ())
                               if reason != 'legacy-unverified' or ref not in requested)
            immutable = [r for r in ours if re.fullmatch(re.escape(repo) + '@sha256:' + HEX, r)]
            if not immutable or any(r not in known and r not in requested for r in immutable):
                reasons.add('legacy-unverified')
            # A reviewed legacy exception cannot override snapshot or recovery protection.
            if reasons:
                skipped.append({'id': image['id'], 'references': ours, 'reasons': sorted(reasons)})
            else:
                for ref in ours:
                    candidates.append({'id': image['id'], 'reference': ref})
        if len(candidates) + len(skipped) > 250:
            fail('MAINTENANCE_REPORT_LIMIT')
        ownership = {}
        for item in images:
            for ref in item['references']:
                owner = ref.split('@', 1)[0] if '@' in ref else ref.rsplit(':', 1)[0]
                ownership.setdefault(owner, set()).add(item['id'])
        if len(ownership) > 250:
            fail('MAINTENANCE_REPORT_LIMIT')
        plan = {'version': 1, 'project': project, 'policyDigest': digest(self.config),
                'candidates': sorted(candidates, key=lambda x: x['reference']),
                'legacyReferences': sorted(requested)}
        selected_snapshots = [x for x in snapshots if x['selected']]
        reported_snapshots = selected_snapshots + [x for x in snapshots[-100:] if x not in selected_snapshots]
        return {'plan': plan, 'digest': digest(plan), 'protected': skipped,
                'disk': self.disk(project),
                'ownershipInventory': [{'repository': k, 'images': len(v)} for k, v in sorted(ownership.items())],
                'snapshots': [{**x, 'cached': x['image'] in local} for x in reported_snapshots]}

    def status(self, project):
        self.enrolled(project)
        result = {'version': 2, 'disk': self.disk(project), 'lastMaintenance': None}
        previous = self.apps / project / 'image-maintenance-status.json'
        try:
            if previous.exists():
                saved = read(previous)
                state = saved.get('status')
                if state not in ('completed', 'running', 'unknown', 'replan-required'):
                    fail('INVALID_MAINTENANCE_STATUS')
                summary = {'status': state, 'removedCount': len(saved.get('removed', []))}
                if re.fullmatch(HEX, saved.get('previewDigest', '')):
                    summary['previewDigest'] = saved['previewDigest']
                result['lastMaintenance'] = summary
            preview = self.preview(project)
            result.update(protection='verified', snapshots=preview['snapshots'],
                          protected=preview['protected'], ownershipInventory=preview['ownershipInventory'])
        except MaintenanceError as error:
            result.update(protection='blocked', code=str(error))
        except (ValueError, TypeError, KeyError):
            result.update(protection='blocked', code='MAINTENANCE_STATE_INVALID')
        return result

    def apply(self, project, preview, automatic=False):
        plan = preview['plan']
        if digest(plan) != preview['digest'] or plan['project'] != project or plan['policyDigest'] != digest(self.config):
            fail('MAINTENANCE_PLAN_CHANGED')
        fresh = self.preview(project, plan['legacyReferences'])
        if fresh['digest'] != preview['digest']:
            fail('MAINTENANCE_PLAN_CHANGED')
        status_path = self.apps / project / 'image-maintenance-status.json'
        result = {'version': 1, 'status': 'running', 'previewDigest': preview['digest'],
                  'removed': [], 'alreadyAbsent': [], 'active': None, 'before': self.disk(project)}
        atomic(status_path, result)
        for candidate in plan['candidates']:
            if automatic and all(x['freeBytes'] >= self.config['targetFreeGiB'] * GIB for x in self.disk(project)):
                break
            # Re-read containers, selections, journals, ledger and references for each deletion.
            available = self.preview(project, plan['legacyReferences'])['plan']['candidates']
            if candidate not in available:
                # Docker may remove digest aliases with the final tag. Confirm
                # absence rather than treating our own completed removal as a race.
                images, _ = self.docker.inventory()
                if not any(candidate['reference'] in x['references'] for x in images):
                    result['alreadyAbsent'].append(candidate)
                    atomic(status_path, result)
                    continue
                result.update(status='replan-required', active=None)
                atomic(status_path, result)
                return result
            result.update(status='unknown', active=candidate)
            atomic(status_path, result)
            try:
                self.docker.remove(candidate['reference'])
            except MaintenanceError as error:
                result.update(code=str(error), status='unknown')
                atomic(status_path, result)
                return result
            result['removed'].append(candidate)
            result.update(active=None, status='running')
            atomic(status_path, result)
        result.update(status='completed', after=self.disk(project))
        result['spacePressure'] = any(x['freeBytes'] < self.config['targetFreeGiB'] * GIB or x['warning']
                                      for x in result['after'])
        atomic(status_path, result)
        return result

    @contextmanager
    def locks(self, project, wait=30):
        self.enrolled(project)
        with lock(self.apps / project / 'operation.lock', 'UNIWARES_OPERATION_LOCK_FD', wait) as app_fd:
            with lock(self.state / 'image-maintenance.lock', 'UNIWARES_IMAGE_LOCK_FD', wait) as image_fd:
                yield app_fd, image_fd

    def cleanup(self, project):
        if not self.enrolled(project)['automatic']:
            return {'status': 'disabled'}
        previous = self.apps / project / 'image-maintenance-status.json'
        if previous.exists() and read(previous).get('status') in ('running', 'unknown'):
            fail('MAINTENANCE_READBACK_REQUIRED')
        return self.apply(project, self.preview(project), automatic=True)


def supervise(args, app_fd, image_fd):
    env = dict(ENV, UNIWARES_OPERATION_LOCK_FD=str(app_fd), UNIWARES_IMAGE_LOCK_FD=str(image_fd))
    if os.environ.get('UNIWARES_DISPATCHED') == '1':
        env['UNIWARES_DISPATCHED'] = '1'
    if os.environ.get('UNIWARES_DISPATCHED') == '1':
        # Preserve the dispatcher's process group: its timeout must reap every writer.
        os.set_inheritable(app_fd, True)
        os.set_inheritable(image_fd, True)
        os.execve(args[0], args, env)
    process = subprocess.Popen(args, env=env, pass_fds=(app_fd, image_fd), start_new_session=True)
    def interrupted(signum, frame):
        raise InterruptedError()
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    try:
        return process.wait(timeout=1200)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preview', 'apply', 'status', 'check-space', 'record',
                                         'cleanup', 'daily', 'run-release'])
    parser.add_argument('project', nargs='?')
    parser.add_argument('--environment', choices=['staging', 'prod'])
    parser.add_argument('--digest')
    parser.add_argument('--legacy-reference', action='append', default=[])
    parser.add_argument('--script', type=Path)
    parser.add_argument('--release-action', choices=['deploy', 'rollback'])
    parser.add_argument('--image', default='')
    parser.add_argument('--commit', default='')
    args = parser.parse_args()
    if os.geteuid() != 0:
        fail('ROOT_OPERATOR_REQUIRED')
    engine = Maintenance(policy())
    if args.action == 'daily':
        results = {}
        for project, settings in engine.config['projects'].items():
            if not settings['automatic']:
                continue
            try:
                with engine.locks(project, wait=0):
                    engine.config = policy()
                    results[project] = engine.cleanup(project)
            except MaintenanceError as error:
                results[project] = {'status': 'skipped', 'code': str(error)}
        print(json.dumps(results))
        return 0
    engine.enrolled(args.project)
    if args.action == 'check-space':
        print(json.dumps({'disk': engine.check_space(args.project)}))
        return 0
    with engine.locks(args.project) as (app_fd, image_fd):
        engine.config = policy()
        engine.enrolled(args.project)
        directory = engine.apps / args.project
        if args.action == 'run-release':
            if not args.script or not args.environment or not args.release_action:
                fail('INVALID_RELEASE_REQUEST')
            trusted(args.script)
            control = Path('/opt/uniwares-control') / args.project
            if args.script.resolve().parents[3] != control or args.script.name != 'vps.sh':
                fail('INVALID_RELEASE_REQUEST')
            target = engine.enrolled(args.project)['environments'][args.environment]
            try:
                return supervise(['/bin/bash', str(args.script), args.release_action, target, '--apply',
                                  args.image, args.commit], app_fd, image_fd)
            except BaseException:
                # Dispatched operations exec in place and use the dispatcher journal.
                # Direct operator supervision records uncertainty after reaping writers.
                atomic(directory / 'image-maintenance-status.json',
                       {'version': 1, 'status': 'unknown', 'code': 'RELEASE_OUTCOME_UNKNOWN'})
                raise
        if args.action == 'preview':
            result = engine.preview(args.project, args.legacy_reference)
            atomic(directory / 'image-maintenance-preview.json', result)
        elif args.action == 'apply':
            result = read(directory / 'image-maintenance-preview.json')
            if not args.digest or args.digest != result['digest']:
                fail('EXACT_PREVIEW_DIGEST_REQUIRED')
            result = engine.apply(args.project, result)
        elif args.action == 'record':
            engine.record(args.project, args.environment)
            result = {'status': 'recorded'}
        elif args.action == 'cleanup':
            result = engine.cleanup(args.project)
        else:
            result = engine.status(args.project)
        print(json.dumps(result, separators=(',', ':')))
        return 0 if result.get('status') not in ('unknown', 'replan-required') else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except MaintenanceError as error:
        print(json.dumps({'status': 'blocked', 'code': str(error)}))
        sys.exit(2)
    except Exception:
        print(json.dumps({'status': 'unknown', 'code': 'MAINTENANCE_INTERNAL_FAILURE'}))
        sys.exit(1)

