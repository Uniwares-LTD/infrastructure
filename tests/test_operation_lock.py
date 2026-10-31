"""Linux lock boundary regression tests; no services or production paths."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('locked_dispatch',ROOT/'scripts/deploy-dispatch.py')
d=importlib.util.module_from_spec(spec); spec.loader.exec_module(d)

@unittest.skipUnless(sys.platform=='linux','Linux flock/process-group tests')
class LockTests(unittest.TestCase):
    def test_registration_is_read_after_lock_and_handed_to_child(self):
        events=[]
        @contextlib.contextmanager
        def lock(project):
            events.append('locked'); yield 7; events.append('unlocked')
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp); (source/'deploy').mkdir()
            (source/'deploy/contract.json').write_text(json.dumps({'version':1,'requiredCapabilities':['operation-lock-v1']}))
            def state(request):
                self.assertEqual(events[-1],'locked'); events.append('read'); return source,{},'a'*64,'b'*64
            class Process:
                def wait(self,timeout): events.append('completed'); return 0
            with patch.object(d,'operation_lock',lock),patch.object(d,'installed_state',state),patch.object(d,'command',return_value=['true']),patch.object(d,'record_operation'),patch.object(d.subprocess,'Popen',return_value=Process()) as run:
                self.assertEqual(d.execute_locked({'project':'fixture','configurationHash':'a'*64,'action':'check'}),0)
                self.assertEqual(run.call_args.kwargs['pass_fds'],(7,))
            self.assertEqual(events,['locked','read','completed','unlocked'])

    def test_real_lock_contention_and_stale_request(self):
        import fcntl
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); state=root/'fixture'; state.mkdir(); lock=state/'operation.lock'; lock.touch(mode=0o600)
            with lock.open('r+') as held:
                fcntl.flock(held,fcntl.LOCK_EX)
                with patch.object(d,'STATE',root),patch.object(d,'trusted',lambda _:None),patch.object(d,'LOCK_WAIT',0.05),patch.object(d.os,'fstat',side_effect=lambda fd: type('Info',(),dict(st_mode=0o100600,st_uid=0))()):
                    with self.assertRaises(d.Rejection) as error:
                        with d.operation_lock('fixture'): self.fail('Entered held lock')
                    self.assertEqual(error.exception.code,'LOCK_TIMEOUT')

    def test_real_operator_update_finishes_before_waiting_deployment_reads(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); state=root/'fixture'; state.mkdir(); lock=state/'operation.lock'; lock.touch(mode=0o600)
            source=root/'control'/'fixture'/('a'*64)
            (source/'deploy/environments').mkdir(parents=True)
            (source/'project.config.json').write_text('{"slug":"fixture"}')
            (source/'deploy/contract.json').write_text(json.dumps({'version':1,'requiredCapabilities':['operation-lock-v1']}))
            config=source/'deploy/environments/staging.json'
            config.write_text('{"runtime":{"MCP_ENABLED":"false"}}')
            old=hashlib.sha256(json.dumps(json.loads(config.read_text()),sort_keys=True,separators=(',',':')).encode()).hexdigest()
            registry=root/'registry'; registry.mkdir(); (registry/'fixture.json').write_text(json.dumps({'revision':'a'*64}))
            code="import fcntl,sys,time; f=open(sys.argv[1],'r+'); fcntl.flock(f,fcntl.LOCK_EX); print('locked',flush=True); time.sleep(.2); open(sys.argv[2],'w').write('{\"runtime\":{\"MCP_ENABLED\":\"true\"}}')"
            child=subprocess.Popen([sys.executable,'-c',code,str(lock),str(config)],stdout=subprocess.PIPE,text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(),'locked')
                with patch.object(d,'STATE',root),patch.object(d,'CONTROL',root/'control'),patch.object(d,'REGISTRY',registry),patch.object(d,'trusted',lambda _:None),patch.object(d.os,'fstat',side_effect=lambda fd:type('Info',(),dict(st_mode=0o100600,st_uid=0))()),patch.object(d.subprocess,'Popen') as execute:
                    with self.assertRaises(d.Rejection) as error:
                        d.execute_locked(dict(version=2,project='fixture',environment='staging',action='check',configurationHash=old))
                    self.assertEqual(error.exception.code,'CONFIGURATION_MISMATCH')
                    execute.assert_not_called()
            finally:
                child.wait(timeout=5); child.stdout.close()

    def test_timeout_reaps_process_before_unlock(self):
        events=[]
        @contextlib.contextmanager
        def lock(project):
            try: yield 7
            finally: events.append('unlocked')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'fixture').mkdir(); (root/'deploy').mkdir()
            (root/'deploy/contract.json').write_text(json.dumps({'version':1,'requiredCapabilities':['operation-lock-v1']}))
            class Process:
                pid=123
                def wait(self,timeout=None):
                    if timeout is not None: raise subprocess.TimeoutExpired('fixture',timeout)
                    events.append('reaped'); return -9
            with patch.object(d,'STATE',root),patch.object(d,'operation_lock',lock),patch.object(d,'installed_state',return_value=(root,{},None,None)),patch.object(d,'command',return_value=['true']),patch.object(d.subprocess,'Popen',return_value=Process()),patch.object(d.os,'killpg',side_effect=lambda *args:events.append('killed')):
                with self.assertRaises(subprocess.TimeoutExpired): d.execute_locked({'project':'fixture','action':'deploy','configurationHash':'a'*64})
            self.assertEqual(events,['killed','reaped','unlocked'])
            self.assertEqual(json.loads((root/'fixture/operation-status.json').read_text())['status'],'unknown')
