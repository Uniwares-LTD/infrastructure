"""Retention behavior against disposable filesystems; Docker is a deterministic adapter."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import image_maintenance as m

REPO = 'ghcr.io/example/app'
def image(number):
    return REPO + '@sha256:' + format(number, '064x')

def identity(number):
    return 'sha256:' + format(number, '064x')

CONFIG = {'version': 1, 'keepReleases': 3, 'keepDays': 14, 'minimumFreeGiB': 20,
          'targetFreeGiB': 30, 'warnUsedPercent': 80,
          'projects': {'app': {'imageRepository': REPO, 'environments': {'staging': 'staging', 'prod': 'production'},
                               'automatic': True}}}


class Docker:
    def __init__(self, root):
        self.path = root
        self.images = []
        self.used = set()
        self.removed = []
        self.error = False

    def root(self):
        return self.path

    def inventory(self):
        return copy.deepcopy(self.images), set(self.used)

    def remove(self, reference):
        if self.error:
            raise m.MaintenanceError('DOCKER_OUTCOME_UNKNOWN')
        self.removed.append(reference)
        for item in self.images:
            if reference in item['references']:
                item['references'].remove(reference)
        self.images = [x for x in self.images if x['references']]


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in ('state', 'apps/app', 'releases/app'):
            (self.root / path).mkdir(parents=True)
        self.docker = Docker(self.root)
        self.engine = m.Maintenance(copy.deepcopy(CONFIG), self.docker, self.root / 'state',
                                    self.root / 'apps', self.root / 'releases')
        # These tests are runnable by non-root developers; production trust validation
        # is tested separately on a root-owned Linux fixture.
        self.trust = patch.object(m, 'trusted')
        self.trust.start()
        self.addCleanup(self.trust.stop)
        self.engine.disk = lambda project: [{'filesystem': 'fixture', 'freeBytes': 25*m.GIB,
                                             'usedPercent': 84, 'warning': True}]
        self.now = int(time.time())

    def release(self, number, age=30, environment='staging', recorded=True):
        target = CONFIG['projects']['app']['environments'][environment]
        name = format(number, '040x') + '.fixture'
        directory = self.root / 'releases/app' / target / 'releases' / name
        directory.mkdir(parents=True)
        (directory / 'compose.env').write_text('DEPLOY_ENV=' + target + '\nIMAGE_DIGEST=' + image(number) +
                                               '\nRELEASE_COMMIT=' + format(number, '040x') + '\n')
        entry = {'environment': environment, 'snapshot': name, 'image': image(number),
                 'commit': format(number, '040x'), 'activatedAt': self.now - age*86400}
        path = self.root / 'apps/app/image-release-ledger.json'
        if recorded:
            value = json.loads(path.read_text()) if path.exists() else {'version': 1, 'activations': []}
            value['activations'].append(entry)
            path.write_text(json.dumps(value))
        self.docker.images.append({'id': identity(number), 'references': [image(number)]})
        return directory

    def candidates(self, legacy=()):
        return [x['reference'] for x in self.engine.preview('app', legacy)['plan']['candidates']]

    def select(self, snapshot, name='current'):
        link = snapshot.parent.parent / name
        link.unlink(missing_ok=True)
        link.symlink_to(snapshot)

    def test_three_distinct_plus_window_and_environments(self):
        for number in range(1, 7):
            self.release(number, age=40-number)
        self.release(7, age=1)
        self.release(8, age=50, environment='prod')
        self.assertEqual(self.candidates(), [image(n) for n in (1, 2, 3, 4)])
        path = self.root / 'apps/app/image-release-ledger.json'
        data = json.loads(path.read_text())
        data['activations'].extend([data['activations'][-2]]*10)
        path.write_text(json.dumps(data))
        self.assertEqual(self.candidates(), [image(n) for n in (1, 2, 3, 4)])

    def test_current_previous_containers_and_shared_repository(self):
        entries = [self.release(n, age=40-n) for n in range(1, 9)]
        self.select(entries[0])
        self.select(entries[1], 'previous')
        self.docker.used.add(identity(3))  # includes stopped containers
        self.docker.images[3]['references'].append('ghcr.io/other/app:old')
        self.assertEqual(self.candidates(), [image(5)])

    def test_legacy_requires_exact_manual_review_and_cannot_override_selection(self):
        snapshot = self.release(1, recorded=False)
        self.assertEqual(self.candidates(), [])
        self.assertEqual(self.candidates([image(1)]), [image(1)])
        self.select(snapshot)
        self.assertEqual(self.candidates([image(1)]), [])

    def test_pending_plan_and_completed_plan(self):
        for n in range(1, 5):
            self.release(n, age=40-n)
        directory = self.root / 'apps/app/operation-plans'
        directory.mkdir()
        plan = {'project': 'app', 'image': image(1)}
        envelope = {'plan': plan, 'digest': m.digest(plan)}
        path = directory / (envelope['digest'] + '.plan.json')
        path.write_text(json.dumps(envelope))
        self.assertEqual(self.candidates(), [])
        journal = directory / (envelope['digest'] + '.journal.json')
        for status in ('unknown', 'failed', 'prepared'):
            journal.write_text(json.dumps({'status': status}))
            self.assertEqual(self.candidates(), [])
        journal.write_text(json.dumps({'status': 'completed'}))
        self.assertEqual(self.candidates(), [image(1)])

    def test_pending_config_ledger_and_operation_fail_closed(self):
        for name, content in [('config-update-pending', None), ('image-ledger-pending.json', {}),
                              ('operation-status.json', {'status': 'unknown'})]:
            path = self.root / 'apps/app' / name
            if content is None:
                path.mkdir()
            else:
                path.write_text(json.dumps(content))
            with self.assertRaises(m.MaintenanceError):
                self.candidates()
            if content is None:
                path.rmdir()
            else:
                path.unlink()

    def test_exact_preview_revalidation_and_resume(self):
        for n in range(1, 6):
            self.release(n, age=40-n)
        preview = self.engine.preview('app')
        self.docker.used.add(identity(1))
        with self.assertRaisesRegex(m.MaintenanceError, 'PLAN_CHANGED'):
            self.engine.apply('app', preview)
        self.assertEqual(self.docker.removed, [])
        self.docker.used.clear()
        original = self.docker.remove
        def race(reference):
            original(reference)
            self.docker.used.add(identity(2))
        self.docker.remove = race
        result = self.engine.apply('app', preview)
        self.assertEqual(result['status'], 'replan-required')
        self.assertEqual(self.docker.removed, [image(1)])
        self.docker.remove = original
        self.docker.used.clear()
        result = self.engine.apply('app', self.engine.preview('app'))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(self.docker.removed, [image(1), image(2)])

    def test_docker_removing_digest_alias_with_tag_is_completed(self):
        for n in range(1, 5):
            self.release(n, age=40-n)
        self.docker.images[0]['references'].append(REPO + ':old')
        def remove_all(reference):
            self.docker.removed.append(reference)
            self.docker.images = [x for x in self.docker.images if reference not in x['references']]
        self.docker.remove = remove_all
        result = self.engine.apply('app', self.engine.preview('app'))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(len(result['removed']), 1)
        self.assertEqual(len(result['alreadyAbsent']), 1)

    def test_status_remains_available_with_pending_recovery(self):
        (self.root / 'apps/app/config-update-pending').mkdir()
        result = self.engine.status('app')
        self.assertEqual(result['protection'], 'blocked')
        self.assertEqual(result['code'], 'PENDING_CONFIGURATION_RECOVERY')
        self.assertIn('disk', result)

    def test_timeout_retains_unknown_and_blocks_automatic_retry(self):
        for n in range(1, 5):
            self.release(n, age=40-n)
        self.docker.error = True
        result = self.engine.apply('app', self.engine.preview('app'))
        self.assertEqual(result['status'], 'unknown')
        with self.assertRaisesRegex(m.MaintenanceError, 'READBACK_REQUIRED'):
            self.engine.cleanup('app')

    def test_disk_floor_target_and_policy_change(self):
        for n in range(1, 5):
            self.release(n, age=40-n)
        preview = self.engine.preview('app')
        self.engine.config['keepDays'] = 15
        with self.assertRaisesRegex(m.MaintenanceError, 'PLAN_CHANGED'):
            self.engine.apply('app', preview)
        self.engine.disk = lambda _: [{'freeBytes': 19*m.GIB}]
        with self.assertRaisesRegex(m.MaintenanceError, 'INSUFFICIENT_DISK_SPACE'):
            self.engine.check_space('app')
        self.engine.disk = lambda _: [{'freeBytes': 30*m.GIB, 'warning': False}]
        self.engine.cleanup('app')
        self.assertEqual(self.docker.removed, [])

    def test_record_rollback_and_missing_ledger_fail_closed(self):
        first = self.release(1, recorded=False)
        second = self.release(2, recorded=False)
        self.select(first)
        self.engine.record('app', 'staging')
        self.select(second)
        self.engine.record('app', 'staging')
        self.select(first)
        self.engine.record('app', 'staging')
        self.assertEqual([x['image'] for x in self.engine.ledger('app')['activations']],
                         [image(1), image(2), image(1)])
        with patch.object(m, 'atomic', side_effect=[None, OSError('private detail')]):
            with self.assertRaises(OSError):
                self.engine.record('app', 'staging')

    def test_malformed_and_secret_safe_state(self):
        path = self.root / 'apps/app/image-release-ledger.json'
        path.write_text(json.dumps({'version': 7, 'secret': 'not-for-output'}))
        with self.assertRaisesRegex(m.MaintenanceError, '^INVALID_RELEASE_LEDGER$'):
            self.candidates()

    def test_disabled_automatic_does_not_inspect_or_delete(self):
        self.engine.config['projects']['app']['automatic'] = False
        self.docker.inventory = lambda: self.fail('Disabled policy must not inspect images')
        self.assertEqual(self.engine.cleanup('app'), {'status': 'disabled'})

    def test_policy_validation(self):
        path = self.root / 'policy.json'
        path.write_text(json.dumps(CONFIG))
        self.assertEqual(m.policy(path), CONFIG)
        data = copy.deepcopy(CONFIG)
        data['projects']['other'] = data['projects']['app']
        path.write_text(json.dumps(data))
        with self.assertRaises(m.MaintenanceError):
            m.policy(path)


@unittest.skipUnless(os.geteuid() == 0, 'Root-owned Linux lock verification')
class RealLockTests(unittest.TestCase):
    def test_handoff_and_conflict(self):
        with tempfile.TemporaryDirectory(dir='/root') as directory:
            path = Path(directory) / 'operation.lock'
            with m.lock(path, 'TEST_RETENTION_FD', wait=0) as fd:
                m.verify_fd(fd, path)
                with self.assertRaisesRegex(m.MaintenanceError, 'BUSY'):
                    with m.lock(path, 'ANOTHER_RETENTION_FD', wait=0):
                        pass
                with patch.dict(os.environ, {'TEST_RETENTION_FD': str(fd)}):
                    with m.lock(path, 'TEST_RETENTION_FD') as inherited:
                        self.assertEqual(inherited, fd)
            with self.assertRaises(m.MaintenanceError):
                fd = os.open(path, os.O_RDWR)
                try:
                    m.verify_fd(fd, path)
                finally:
                    os.close(fd)

    def test_direct_supervisor_reaps_writer_on_interrupt(self):
        with tempfile.TemporaryDirectory(dir='/root') as directory:
            root = Path(directory)
            marker = root/'writer.pid'
            writer = 'import os,time;open('+repr(str(marker))+',"w").write(str(os.getpid()));time.sleep(30)'
            supervisor = ('import sys;sys.path.insert(0,'+repr(str(Path(m.__file__).parent))+');'
                          'import image_maintenance as m;'
                          'm.supervise(['+repr(sys.executable)+',"-c",'+repr(writer)+'],int(sys.argv[1]),int(sys.argv[2]))')
            with m.lock(root/'app.lock', 'TEST_APP_FD') as app_fd:
                with m.lock(root/'image.lock', 'TEST_IMAGE_FD') as image_fd:
                    child = subprocess.Popen([sys.executable, '-c', supervisor, str(app_fd), str(image_fd)],
                        pass_fds=(app_fd, image_fd), stderr=subprocess.DEVNULL)
                    try:
                        deadline = time.monotonic()+5
                        while not marker.exists() and time.monotonic()<deadline:
                            time.sleep(.02)
                        self.assertTrue(marker.exists())
                        writer_pid = int(marker.read_text())
                        child.terminate()
                        child.wait(timeout=5)
                        with self.assertRaises(ProcessLookupError):
                            os.kill(writer_pid, 0)
                        m.verify_fd(app_fd, root/'app.lock')
                        m.verify_fd(image_fd, root/'image.lock')
                    finally:
                        if child.poll() is None:
                            child.kill()
                        child.wait(timeout=5)

    def test_untrusted_symlink(self):
        with tempfile.TemporaryDirectory(dir='/root') as directory:
            real = Path(directory) / 'real'
            real.write_text('{}')
            link = Path(directory) / 'link'
            link.symlink_to(real)
            with self.assertRaises(m.MaintenanceError):
                m.read(link)
