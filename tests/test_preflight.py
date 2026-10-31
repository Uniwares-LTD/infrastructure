"""Read-only preflight, rejection privacy and execution-boundary regression tests."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('dispatch', Path(__file__).resolve().parents[1] / 'scripts/deploy-dispatch.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
TRUSTED = d.trusted


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        registry = root / 'registry'
        registry.mkdir()
        self.source = root / 'control' / 'unibase' / ('b'*64)
        (self.source / 'deploy/environments').mkdir(parents=True)
        self.config = {'runtime': {'MCP_CLIENTS_JSON': '["public"]'},
                       'deployment': {'imageRepository': 'ghcr.io/test/unibase'}}
        self.file = self.source / 'deploy/environments/staging.json'
        self.file.write_text(json.dumps(self.config))
        (self.source / 'project.config.json').write_text('{"slug":"unibase"}')
        (registry / 'unibase.json').write_text(json.dumps({'revision': 'b'*64}))
        self.request = dict(version=1, project='unibase', environment='staging', action='preflight',
                            configurationHash=self.hash())
        for name, value in [('REGISTRY', registry), ('CONTROL', root/'control'), ('trusted', lambda path: None)]:
            mock = patch.object(d, name, value)
            mock.start(); self.addCleanup(mock.stop)

    def hash(self):
        return hashlib.sha256(json.dumps(self.config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def call(self, request):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = d.handle(request)
        return status, json.loads(output.getvalue())

    def test_preflight_reads_only_and_reports_exact_hashes(self):
        before = self.file.read_bytes()
        with patch.object(d.subprocess, 'run') as run:
            status, result = self.call(self.request)
            run.assert_not_called()
        self.assertEqual(status, 0)
        self.assertTrue(result['compatible'])
        self.assertEqual(result['installedConfigurationHash'], self.hash())
        self.assertEqual(self.file.read_bytes(), before)

    def test_permission_mismatch_rejects_before_any_execution(self):
        with patch.object(d.subprocess, 'run') as run:
            status, result = self.call({**self.request, 'configurationHash': 'c'*64})
            run.assert_not_called()
        self.assertEqual(status, 2)
        self.assertEqual(result['code'], 'CONFIGURATION_MISMATCH')
        self.assertEqual(result['installedRevision'], 'b'*64)

    def test_deploy_revalidates_after_prior_successful_preflight(self):
        self.assertEqual(self.call(self.request)[0], 0)
        self.config['runtime']['MCP_CLIENTS_JSON'] = '["public","artifact:write"]'
        self.file.write_text(json.dumps(self.config))
        request = {**self.request, 'action': 'deploy', 'commit': 'd'*40,
                   'image': 'ghcr.io/test/unibase@sha256:'+'e'*64}
        with patch.object(d.subprocess, 'run') as run:
            self.assertEqual(self.call(request)[1]['code'], 'CONFIGURATION_MISMATCH')
            run.assert_not_called()

    def test_old_operations_remain_accepted(self):
        for action in ('check', 'rollback', 'deploy'):
            request = {**self.request, 'action': action}
            if action == 'deploy': request.update(commit='d'*40, image='ghcr.io/test/unibase@sha256:'+'e'*64)
            with patch.object(d.subprocess, 'run') as run:
                run.return_value.returncode = 0
                self.assertEqual(d.handle(request), 0)
                self.assertEqual(run.call_args.args[0][2], action)

    def test_safe_error_codes_and_no_private_exception_text(self):
        for error, code in [(FileNotFoundError('private'), 'MISSING_REGISTRATION'),
                            (d.Rejection('UNTRUSTED_CONTROL'), 'UNTRUSTED_CONTROL'),
                            (RuntimeError('private-password'), 'INTERNAL_FAILURE')]:
            with patch.object(d, 'trusted', side_effect=error):
                status, result = self.call(self.request)
                self.assertNotEqual(status, 0)
                self.assertEqual(result['code'], code)
                self.assertNotIn('private', json.dumps(result))
        for request in ([], {**self.request, 'command': 'sh'}, {**self.request, 'version': True}):
            self.assertEqual(self.call(request)[1]['code'], 'INVALID_REQUEST')

    def test_trust_checks_reject_symlinks_writable_paths_and_foreign_owners(self):
        for mode, uid in [(stat.S_IFLNK | 0o700, 0), (stat.S_IFDIR | 0o777, 0),
                          (stat.S_IFDIR | 0o700, 1000)]:
            path = SimpleNamespace(parents=[], lstat=lambda: SimpleNamespace(st_mode=mode, st_uid=uid))
            with self.assertRaises(d.Rejection): TRUSTED(path)
        parent = SimpleNamespace(lstat=lambda: SimpleNamespace(st_mode=stat.S_IFDIR | 0o777, st_uid=0))
        path = SimpleNamespace(parents=[parent], lstat=lambda: SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0))
        with self.assertRaises(d.Rejection): TRUSTED(path)

    def test_requested_retention_rejects_old_bundle_without_executing(self):
        contract = self.source / 'deploy/contract.json'
        contract.write_text(json.dumps({'version': 1, 'requiredCapabilities': ['operation-lock-v1']}))
        request = dict(self.request, version=2, requiredCapabilities=['operation-lock-v1', 'image-retention-v1'])
        with patch.object(d.subprocess, 'run') as execute:
            status, value = self.call(request)
            self.assertEqual(status, 2)
            self.assertEqual(value['code'], 'UNSUPPORTED_CAPABILITY')
            execute.assert_not_called()
        # Existing clients remain supported and do not silently claim the new capability.
        request.pop('requiredCapabilities')
        self.assertEqual(self.call(request)[1]['code'], 'COMPATIBLE')

    def test_new_bundle_enrollment_required_and_capability_rechecked(self):
        import image_maintenance as maintenance
        contract = self.source / 'deploy/contract.json'
        contract.write_text(json.dumps({'version': 1, 'requiredCapabilities': ['operation-lock-v1', 'image-retention-v1']}))
        request = dict(self.request, version=2, requiredCapabilities=['operation-lock-v1', 'image-retention-v1'])
        with patch.object(maintenance, 'policy', return_value={'projects': {'unibase': {}}}):
            self.assertEqual(self.call(request)[1]['code'], 'COMPATIBLE')
            contract.write_text(json.dumps({'version': 1, 'requiredCapabilities': ['operation-lock-v1']}))
            with self.assertRaises(d.Rejection) as error:
                d.command(dict(request, action='deploy', image='ghcr.io/test/unibase@sha256:'+'d'*64, commit='e'*40))
            self.assertEqual(error.exception.code, 'UNSUPPORTED_CAPABILITY')
