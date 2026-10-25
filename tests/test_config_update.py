"""Synthetic update/recovery boundaries, no services or provider access."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('update', Path(__file__).resolve().parents[1] / 'scripts/update-app-config.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class ConfigUpdateTests(unittest.TestCase):
    def setUp(self):
        self.public = {'runtime': {'APP_ENV': 'staging', 'APP_ORIGIN': 'https://app.example',
                                  'DIFY_MODE': 'disabled', 'PAYMENTS_MODE': 'disabled', 'ASSET_STORE': 'mongo'},
                       'deployment': {'port': 35001}}
        self.raw = 'APP_ENV=staging\nMONGODB_URI=existing-private\nREDIS_URL=existing-redis\n'

    def test_keeps_existing_provider_credentials_and_merges_ai(self):
        target = copy.deepcopy(self.public)
        target['runtime']['PERSONA_COMPLETION_MODE'] = 'live'
        result = update.runtime_values(update.merge(self.public, target, self.raw, {'PERSONA_COMPLETION_API_KEY': 'synthetic'}))
        self.assertEqual(result['MONGODB_URI'], 'existing-private')
        self.assertEqual(result['REDIS_URL'], 'existing-redis')
        self.assertEqual(result['PERSONA_COMPLETION_MODE'], 'live')

    def test_identity_changes_refused(self):
        for section, key, value in [('runtime', 'APP_ORIGIN', 'https://other.example'), ('deployment', 'port', 35002),
                                    ('runtime', 'PAYMENTS_MODE', 'simulation')]:
            target = copy.deepcopy(self.public)
            target[section][key] = value
            with self.assertRaises(ValueError):
                update.merge(self.public, target, self.raw, {'PERSONA_COMPLETION_API_KEY': 'synthetic'})

    def test_private_input_does_not_accept_local_config_or_provider_replacement(self):
        for key in ['APP_ENV', 'FIREBASE_AUTH_EMULATOR_HOST', 'MONGODB_URI', 'REDIS_URL', 'UNRELATED_SECRET']:
            with self.assertRaises(ValueError):
                update.merge(self.public, self.public, self.raw, {key: 'forbidden'})
        for value in ['', 'x\ny', 'x\0y', 7]:
            with self.assertRaises(ValueError):
                update.merge(self.public, self.public, self.raw, {'DIFY_MANAGEMENT_KEY': value})

    def test_live_dify_requires_dedicated_encryption_and_referenced_key(self):
        target = copy.deepcopy(self.public)
        target['runtime'].update(DIFY_MODE='live', DIFY_ORCHESTRATORS_JSON=json.dumps([{'keyEnv':'DIFY_KEY_STAGE'}]))
        private = {'DIFY_MANAGEMENT_KEY':'synthetic', 'DIFY_CREDENTIAL_ENCRYPTION_KEY':'a'*64}
        with self.assertRaises(ValueError):
            update.merge(self.public, target, self.raw, private)
        private['DIFY_KEY_STAGE'] = 'synthetic'
        self.assertIn('DIFY_MODE=live', update.merge(self.public, target, self.raw, private))
        private['DIFY_CREDENTIAL_ENCRYPTION_KEY'] = 'bad'
        with self.assertRaises(ValueError):
            update.merge(self.public, target, self.raw, private)

    def test_encryption_rotation_refused_while_writers_enabled(self):
        with self.assertRaises(ValueError):
            update.check_encryption_state('synthetic', 'DIFY_MODE=live\n', 'DIFY_CREDENTIAL_ENCRYPTION_KEY='+'b'*64+'\n')

    def test_failure_restores_both_files_at_every_mutation_boundary(self):
        for failed in ['disabled', 'runtime', 'registration']:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp); runtime = root/'runtime.env'; registration = root/'registration.json'; journal = root/'pending'
                runtime.write_bytes(b'OLD=private\n'); registration.write_bytes(b'{"revision":"old"}\n')
                def checkpoint(name):
                    if name == failed:
                        raise RuntimeError('synthetic interruption')
                with self.assertRaises(RuntimeError):
                    update.apply_change(journal, runtime, registration, 'NEW=private\n', 'new', checkpoint)
                self.assertEqual(runtime.read_bytes(), b'OLD=private\n')
                self.assertEqual(registration.read_bytes(), b'{"revision":"old"}\n')
                self.assertFalse(journal.exists())

    def test_success_retains_backup_and_crash_journal_can_be_recovered(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); runtime = root/'runtime.env'; registration = root/'registration.json'; journal = root/'pending'
            runtime.write_bytes(b'OLD=private\n'); registration.write_bytes(b'{"revision":"old"}\n')
            update.apply_change(journal, runtime, registration, 'NEW=private\n', 'new')
            self.assertEqual(json.loads(registration.read_text())['revision'], 'new')
            backup = root/'config-previous-new'
            self.assertEqual((backup/'runtime.env').read_bytes(), b'OLD=private\n')
            backup.rename(journal)
            registration.write_bytes(b'{"revision":"update-in-progress"}\n')
            self.assertTrue(update.recover(journal, runtime, registration))
            self.assertEqual(runtime.read_bytes(), b'OLD=private\n')
            self.assertEqual(json.loads(registration.read_text())['revision'], 'old')


if __name__ == '__main__':
    unittest.main()
