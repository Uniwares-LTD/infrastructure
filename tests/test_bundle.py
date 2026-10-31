"""Real archive -> existing updater -> dispatcher compatibility regression."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
builder=module('builder','build-control-bundle.py')
updater=module('updater','update-app-config.py')
dispatch=module('bundle_dispatch','deploy-dispatch.py')
bootstrap=module('bundle_bootstrap','bootstrap-deploy.py')

class BundleTests(unittest.TestCase):
    def test_permission_only_bundle_matches_updater_and_dispatcher(self):
        app=ROOT/'tests/fixtures/application'  # Fixed permission-correction regression, not mutable application state.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); repo=root/'repo'; repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
            git('init'); git('config','user.name','Fixture'); git('config','user.email','fixture@example.invalid')
            for name in ['package.json','package-lock.json','project.config.json','tsconfig.json','deploy/contract.json','deploy/environments/staging.json']:
                target=repo/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes((app/name).read_bytes())
            for name in ['src','scripts','messages']:
                (repo/name).mkdir(); (repo/name/'fixture.txt').write_text('fixture')
            git('add','.'); git('commit','-m','fixture'); revision=git('rev-parse','HEAD')
            archive=root/'bundle.tar'; manifest=builder.build(repo,revision,archive)
            with tarfile.open(archive) as tar:
                projected=json.load(tar.extractfile('deploy/environments/staging.json'))
            self.assertNotIn('DIAGNOSTICS_ENABLED',projected['runtime'])
            self.assertEqual(manifest['bundleChecksum'],hashlib.sha256(archive.read_bytes()).hexdigest())
            before=copy.deepcopy(projected)
            clients=json.loads(before['runtime']['MCP_CLIENTS_JSON'])
            clients[0]['permissions']=[p for p in clients[0]['permissions'] if p not in ['run:read','artifact:read','artifact:write']]
            before['runtime']['MCP_CLIENTS_JSON']=json.dumps(clients,separators=(',',':'))
            self.assertEqual(manifest['configurationHashes']['staging'],'3be35b4456ec3086cb65ed82bc8a8bc3ecd7d634fc0dabaebae5974dce2f0d1c')
            self.assertEqual(hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'c13b8b81304490c768c07b769f1b650215d04211d4ce5504a1029dfa85aac91c')
            runtime=''.join(k+'='+v+'\n' for k,v in before['runtime'].items())
            runtime+='DIFY_MANAGEMENT_KEY=canary\nDIFY_CREDENTIAL_ENCRYPTION_KEY='+'a'*64+'\nDIFY_KEY_DOCUMENT_SUMMARY=canary\nMCP_TOKEN_DIFY=canary\n'
            merged=updater.merge(before,projected,runtime,{'MCP_TOKEN_DIFY':'canary'})
            self.assertIn('DIFY_CREDENTIAL_ENCRYPTION_KEY='+'a'*64,merged)
            digest=manifest['bundleChecksum']; source=root/'control'/'unibase'/digest
            extracted=root/'extract'; extracted.mkdir()
            staged=bootstrap.extract(archive,digest,extracted)
            source.parent.mkdir(parents=True)
            staged.rename(source)
            registry=root/'registry'; registry.mkdir(); (registry/'unibase.json').write_text(json.dumps({'revision':digest}))
            request=dict(version=1,project='unibase',environment='staging',action='preflight',configurationHash=manifest['configurationHashes']['staging'])
            with patch.object(dispatch,'CONTROL',root/'control'), patch.object(dispatch,'REGISTRY',registry), patch.object(dispatch,'trusted',lambda _:None):
                self.assertTrue(dispatch.preflight(request)['compatible'])
            with self.assertRaises(ValueError): builder.build(repo,'HEAD',root/'mutable.tar')
            self.assertNotIn('canary',archive.read_bytes().decode(errors='replace'))

if __name__=='__main__': unittest.main()
