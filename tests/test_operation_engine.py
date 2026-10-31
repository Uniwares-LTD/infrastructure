"""Prepared plans apply the reviewed profile through the actual updater journal."""
import base64
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import operation_engine as engine
from operation_plan import digest
from operation_store import PlanStore
from deployment_contract import load,project

def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
builder=module('engine_builder','build-control-bundle.py')
d=module('engine_dispatch','deploy-dispatch.py')

@unittest.skipUnless(os.name=='posix','Protected engine requires Linux filesystem semantics')
class EngineTests(unittest.TestCase):
 def test_real_archive_plan_apply_and_replay(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);repo=root/'repo';repo.mkdir();fixtures=ROOT/'tests/fixtures/application'
   import shutil
   shutil.copytree(fixtures,repo,dirs_exist_ok=True)
   for name in ['scripts','src','messages']:(repo/name).mkdir();(repo/name/'fixture.txt').write_text('fixture')
   def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
   git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-m','fixture');revision=git('rev-parse','HEAD')
   archive=root/'bundle.tar';manifest=builder.build(repo,revision,archive)
   state=root/'state';(state/'unibase').mkdir(parents=True,mode=0o700)
   registry=root/'registry';registry.mkdir();(registry/'unibase.json').write_text(json.dumps({'revision':'a'*64}))
   control=root/'control';old=control/'unibase'/('a'*64);(old/'deploy/environments').mkdir(parents=True)
   contract=load(repo/'deploy/contract.json')
   proposed=project(json.loads((repo/'deploy/environments/staging.json').read_text()),contract)
   prior=copy.deepcopy(proposed);clients=json.loads(prior['runtime']['MCP_CLIENTS_JSON']);clients[0]['permissions']=[p for p in clients[0]['permissions'] if p not in ('run:read','artifact:read','artifact:write')];prior['runtime']['MCP_CLIENTS_JSON']=json.dumps(clients,separators=(',',':'))
   (old/'deploy/environments/staging.json').write_text(json.dumps(prior))
   production=project(json.loads((repo/'deploy/environments/production.json').read_text()),contract)
   (old/'deploy/environments/production.json').write_text(json.dumps(production));(old/'project.config.json').write_text('{"slug":"unibase"}')
   runtime=root/'etc/unibase/staging/runtime.env';runtime.parent.mkdir(parents=True)
   runtime.write_text(''.join(k+'='+v+'\n' for k,v in prior['runtime'].items())+'DIFY_MANAGEMENT_KEY=fixture\nDIFY_CREDENTIAL_ENCRYPTION_KEY='+'e'*64+'\nDIFY_KEY_DOCUMENT_SUMMARY=fixture\nMCP_TOKEN_DIFY=fixture\n')
   candidate=dict(project='unibase',environment='staging',sourceCommit=revision,image=proposed['deployment']['imageRepository']+'@sha256:'+'b'*64,bundleChecksum=manifest['bundleChecksum'],configurationHash=manifest['configurationHashes']['staging'],classification='host-configuration',changedSettings=[],credentialReferences=[])
   request=dict(version=2,action='plan',project='unibase',environment='staging',candidate=candidate,bundle=base64.b64encode(archive.read_bytes()).decode())
   with patch.object(d,'STATE',state),patch.object(d,'REGISTRY',registry),patch.object(d,'CONTROL',control),patch.object(d,'trusted',lambda path:None),patch.object(engine,'RUNTIME',root/'etc'):
    store=PlanStore(state/'unibase/operation-plans');prepared=engine.stage(d,store,request);plan=prepared['plan']
    self.assertEqual(plan['changedSettings'],['runtime.MCP_CLIENTS_JSON','control.bundle'])
    self.assertNotIn('fixture',json.dumps(prepared))
    executor=engine.Executor(d,store,7,plan);calls=[]
    with patch.object(engine.subprocess,'run',return_value=SimpleNamespace(returncode=0)),patch.object(d,'execute_with_lock',side_effect=lambda request,fd:calls.append(request) or 0):
     result=store.apply(prepared['digest'],'c'*64,plan['expected'],{'configure':executor.configure,'deploy':executor.deploy,'check':executor.check},{})
    self.assertEqual(result['status'],'completed')
    self.assertEqual(calls[0]['image'],candidate['image'])
    self.assertEqual(json.loads((registry/'unibase.json').read_text())['revision'],candidate['bundleChecksum'])
    self.assertIn('DIFY_CREDENTIAL_ENCRYPTION_KEY='+'e'*64,runtime.read_text())
    self.assertTrue((state/'unibase'/('config-previous-'+candidate['bundleChecksum'])).exists())
    with self.assertRaisesRegex(ValueError,'APPROVAL_REPLAY'):store.apply(prepared['digest'],'c'*64,result['expectedAfter'],{}, {})
