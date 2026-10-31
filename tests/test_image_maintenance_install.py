"""Operator installation is explicit and never activates scheduling."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_image_maintenance import CONFIG
import image_maintenance as m

spec = importlib.util.spec_from_file_location('retention_installer',
    Path(__file__).resolve().parents[1]/'scripts/install-image-maintenance.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_preview_apply_predecessor_policy_binding_and_disabled_timer(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            root = Path(directory)
            for name in ('bin', 'config', 'units', 'source'):
                (root/name).mkdir()
            for name, path in {'COMMAND': root/'bin/maintenance', 'POLICY': root/'config/policy.json',
                'UNITS': root/'units', 'STATE': root/'state', 'INSTALL_ROOT': root/'installed'}.items():
                stack.enter_context(patch.object(installer, name, path))
            stack.enter_context(patch.object(installer, 'trusted'))
            stack.enter_context(patch.object(m, 'trusted'))
            stack.enter_context(patch.object(installer.os, 'geteuid', return_value=0))
            stack.enter_context(patch.object(installer, 'lock', return_value=contextlib.nullcontext()))
            command = stack.enter_context(patch.object(installer.subprocess, 'run'))
            source = root/'source/image_maintenance.py'
            source.write_text('print("fixture")\n')
            config = root/'source/policy.json'
            config.write_text(json.dumps(CONFIG))
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            args = ['installer', '--source', str(source), '--sha256', checksum, '--policy', str(config)]
            def invoke(extra=()):
                with patch.object(sys, 'argv', args + list(extra)), contextlib.redirect_stdout(io.StringIO()):
                    installer.main()
            invoke()
            self.assertFalse(installer.COMMAND.exists())
            self.assertFalse(installer.POLICY.exists())
            command.assert_not_called()
            invoke(['--apply'])
            self.assertTrue(installer.COMMAND.exists())
            self.assertTrue((root/'units/uniwares-image-maintenance.timer').exists())
            self.assertIn('03:00:00 UTC', (root/'units/uniwares-image-maintenance.timer').read_text())
            self.assertIn('Persistent=true', (root/'units/uniwares-image-maintenance.timer').read_text())
            command.assert_called_once_with(['systemctl', 'daemon-reload'], check=True)
            old = installer.COMMAND.read_bytes()
            source.write_text('print("next fixture")\n')
            args[args.index('--sha256')+1] = hashlib.sha256(source.read_bytes()).hexdigest()
            invoke(['--apply'])
            predecessor = installer.COMMAND.with_name('maintenance.previous-'+hashlib.sha256(old).hexdigest())
            self.assertEqual(predecessor.read_bytes(), old)
            changed = json.loads(config.read_text())
            changed['keepDays'] = 21
            config.write_text(json.dumps(changed))
            with self.assertRaisesRegex(m.MaintenanceError, 'EXPECTED_POLICY_CHECKSUM_REQUIRED'):
                invoke(['--apply'])
