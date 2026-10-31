import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'));result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
builder=module('build-controller-bundle');installer=module('controller-install')
class ControllerBundleTests(unittest.TestCase):
 def test_immutable_controller_archive_uses_actual_installer(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);repo=root/'repo';(repo/'scripts').mkdir(parents=True)
   (repo/'scripts/deploy-dispatch.py').write_text('raise SystemExit(0)')
   (repo/'requirements-controller.txt').write_text('PyJWT==2.15.1')
   def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
   git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-m','fixture')
   revision=git('rev-parse','HEAD');archive=root/'controller.tar';manifest=builder.build(repo,revision,archive)
   destination=root/'extracted';destination.mkdir();installer.extract(archive,manifest['bundleChecksum'],destination)
   import json
   self.assertEqual(json.loads((destination/'config/controller-source.json').read_text())['sourceCommit'],revision)
   with self.assertRaises(ValueError):installer.extract(archive,'0'*64,root/'wrong')
   with self.assertRaises(ValueError):builder.build(repo,'HEAD',root/'mutable.tar')
