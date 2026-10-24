import importlib.util
import hashlib
import pathlib
import unittest
from unittest.mock import patch

path = pathlib.Path(__file__).parents[1] / "scripts" / "srv1-discovery.py"
spec = importlib.util.spec_from_file_location("discovery", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiscoveryTests(unittest.TestCase):
    def test_installer_pins_current_helper(self):
        installer = path.with_name("install-discovery.sh").read_text()
        self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), installer)

    def test_arguments_rejected_before_probes(self):
        with patch.object(module.sys, "argv", ["helper", "--anything"]), patch.object(module, "collect") as collect:
            self.assertEqual(module.main(), 2)
            collect.assert_not_called()

    def test_nonroot_rejected(self):
        with patch.object(module.sys, "argv", ["helper"]), patch.object(module.os, "geteuid", return_value=1003, create=True), patch.object(module, "collect") as collect:
            self.assertEqual(module.main(), 1)
            collect.assert_not_called()

    def test_environment_and_stdin_are_not_inherited(self):
        with patch.object(module.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "safe"
            self.assertEqual(module.probe(("/usr/bin/docker", "ps")), {"output": "safe"})
            options = run.call_args.kwargs
            self.assertEqual(options["env"], module.ENV)
            self.assertEqual(options["stdin"], module.subprocess.DEVNULL)
            self.assertFalse(options.get("shell", False))

    def test_network_ids_cannot_inject_options(self):
        with patch.object(module, "probe", side_effect=[{"output": ""}, {"output": "--help"}, {"output": ""}]) as probe:
            report = module.collect()
            self.assertEqual(probe.call_count, 3)
            self.assertEqual(report["networks"], [{"error": "invalid network ID"}])

    def test_errors_do_not_echo_command_output(self):
        with patch.object(module.subprocess, "run") as run:
            run.return_value.returncode = 1
            run.return_value.stdout = "secret"
            self.assertNotIn("secret", str(module.probe(("/usr/bin/docker", "ps"))))


if __name__ == "__main__":
    unittest.main()
