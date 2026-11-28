"""Disposable fixed-protocol/state tests: no Docker daemon or live database."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import data_operations as data
from operation_plan import prepare,digest
from operation_store import PlanStore,atomic

ROW={'id':'core:0001-test','checksum':'a'*64}
MANIFEST=dict(version=1,project='fixture',enabledOwners=['core'],runnerSha256='b'*64,migrations=[dict(**ROW,description='fixture',releasePhase='before-release',hasVerifier=True)])
LEDGER=[dict(**ROW,appliedAt='2026-11-21T00:00:00.000Z',durationMs=1)]

def plan():
 return prepare(dict(project='fixture',environment='staging',sourceCommit='c'*40,image='ghcr.io/test/fixture@sha256:'+'d'*64,bundleChecksum='e'*64,configurationHash='f'*64,classification='data-migration',changedSettings=[],credentialReferences=[],requestId='11111111-1111-4111-8111-111111111111',migrationRequest=dict(database='fixture_staging',manifestDigest=data.identity(MANIFEST),ledgerDigest=data.identity([]),pending=[ROW],backupPolicy={'mode':'create','verification':'archive'})),dict(installedRevision='e'*64,configurationHash='f'*64))

class DataTests(unittest.TestCase):
 def test_pure_review_reports_disabled_unknown_drift_and_pages_without_changing_inputs(self):
  manifest=copy.deepcopy(MANIFEST);manifest['migrations'].append({**manifest['migrations'][0],'id':'notes:0001-note'})
  report=data.review(data.catalog(manifest,'fixture'),[])
  self.assertEqual(report['activationDecision'],'blocked-migrations')
  self.assertEqual(data.public_page(report)['pending'],manifest['migrations'][:1]);self.assertEqual(report['disabled'],['notes:0001-note'])
  ledger=copy.deepcopy(LEDGER);ledger[0]['checksum']='0'*64
  self.assertEqual(data.review(manifest,ledger)['changed'],[ROW['id']])
  ledger.append(dict(id='removed:0001-old',checksum='1'*64,appliedAt='2026-11-21T00:00:00.000Z',durationMs=2))
  self.assertEqual(data.review(manifest,ledger)['unknown'],['removed:0001-old'])
  with self.assertRaises(ValueError):data.public_page(report,-1)
  with self.assertRaises(ValueError):data.catalog({**manifest,'command':'no'},'fixture')

 def test_executor_success_backup_failure_interruption_and_failed_final_copy(self):
  from recovery import BackupSession
  for failure in (None,'backup','response','health','report','ingress'):
   with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);(root/'fixture').mkdir();store=PlanStore(root/'fixture/plans');env=plan();key=store.save(env);original=env['plan']
    state={'ledger':[],'running':['app','worker'],'messages':[],'ingress_refreshed':False}
    class Host:
     def __init__(self,*args):self.database='fixture_staging';self.observed=original['expected']
     def serving(self):return {"imageMatches":True,"ready":True}
     def candidate(self,*args):return MANIFEST
     def probe(self,action,**kwargs):
      if action=='report' and failure=='report':raise ValueError('copy unavailable')
      return state['ledger'] if action=='ledger' else {'recorded':True}
    class Session:
     def __init__(self,*args):self.compose=['compose']
     writers = BackupSession.writers
     running_services = BackupSession.running_services
     resume_writers = BackupSession.resume_writers
     def backup(self,database):
      if failure=='backup':raise ValueError('backup failure')
      return dict(backupId='2'*64,database=database,sha256='3'*64,verified=True)
    def run(args,*_):
     if 'stop' in args:state['running']=[]
     if 'start' in args:state['running']=['app','worker']
     if 'ps' in args:return ('\n'.join(state['running']+['ingress'])).encode()
     if args[-2:]==['-s','reload']:
      if failure=='ingress':raise ValueError('reload failed')
      state['ingress_refreshed']=True
    class Process:
     pid=99999999;returncode=0
     def __init__(self):self.stdin=io.BytesIO();self.stdout=io.BytesIO()
     def poll(self):return 0
     def wait(self,**kwargs):return 0
    def start(executor,*args,**kwargs):executor.process=Process()
    responses=[{'type':'ready','planId':key},{'type':'migrate'},{'type':'verify'},{'type':'completed','applied':[ROW['id']],'verification':[dict(id=ROW['id'],warnings=[])]}]
    def receive(executor):
     value=responses.pop(0)
     if value['type']=='verify' and failure=='response':raise ValueError('lost response')
     if value['type']=='completed':state['ledger']=LEDGER
     return value
    d=SimpleNamespace(STATE=root,ENV={},execute_with_lock=lambda *args:0 if state['ingress_refreshed'] and failure!='health' else 1)
    with patch.object(data,'Host',Host),patch('recovery.BackupSession',Session),patch('recovery.run',run),patch.object(data,'command',return_value=b''),patch.object(data.DataExecutor,'start',start),patch.object(data.DataExecutor,'receive',receive):
     executor=data.DataExecutor(d,store,3,original)
     try:
      try:store.apply(key,'4'*64,original['expected'],{'backup':executor.backup,'migrate':executor.migrate,'verify':executor.verify},{})
      finally:executor.close()
     except ValueError:
      self.assertIn(failure,('backup','response','health','ingress'))
     result=data.evidence(store,original)
     if failure in (None,'report'):
      self.assertTrue(data.completed(original,result));self.assertEqual(state['running'],['app','worker'])
      self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'proceed')
     elif failure=='backup':
      self.assertFalse(result['writeIntent']);self.assertEqual(result['status'],'failed');self.assertEqual(state['running'],['app','worker'])
     else:
      self.assertTrue(result['writeIntent']);self.assertEqual(result['status'],'unknown')
      self.assertEqual(data.activation(store,MANIFEST,LEDGER if failure in ('health','ingress') else [],'staging','fixture_staging')['activationDecision'],'blocked-recovery')
      if failure=='response':self.assertEqual(state['running'],[])

 def test_resolution_binds_original_history_rejects_drift_and_tamper_and_is_idempotent(self):
  spec=importlib.util.spec_from_file_location('resolution',Path(data.__file__).with_name('data-operation-resolution.py'))
  utility=importlib.util.module_from_spec(spec);spec.loader.exec_module(utility)
  with tempfile.TemporaryDirectory() as temp:
   store=PlanStore(Path(temp)/'plans');envelope=plan();key=store.save(envelope);original=envelope['plan']
   journal=dict(planId=key,status='unknown',active='verify',completed=['backup','migrate']);atomic(store.path(key,'.journal.json'),journal)
   saved=dict(version=1,planId=key,database='fixture_staging',status='unknown',phase='verify',writeIntent=True,backup={'verified':True,'backupId':'2'*64,'sha256':'3'*64,'database':'fixture_staging'},writers=['app'],writersRestored=False,health=False,verification=[],applied=[ROW]);atomic(store.path(key,'.data.json'),saved)
   self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'blocked-recovery')
   snapshot=dict(recorded=[ROW],verification=[ROW],verifierResults=[dict(id=ROW["id"],warnings=[])],predecessorGone=True,leaseAcquired=True,writersRestored=True,health=True,backupVerified=True)
   with self.assertRaisesRegex(ValueError,'STATE_CHANGED'):utility.record(store,original,saved,snapshot,'0'*64,'verified-complete','operator','verified recovery')
   with self.assertRaises(ValueError):utility.record(store,original,saved,{**snapshot,'predecessorGone':False},data.identity({**snapshot,'predecessorGone':False}),'verified-complete','operator','reason')
   with self.assertRaises(ValueError):utility.record(store,original,saved,snapshot,data.identity(snapshot),'safe-to-retry','operator','reason')
   value=utility.record(store,original,saved,snapshot,data.identity(snapshot),'verified-complete','operator','verified recovery')
   with patch.object(data,'secure_record'):
    self.assertEqual(utility.record(store,original,saved,snapshot,data.identity(snapshot),'verified-complete','operator','verified recovery'),value)
    self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'proceed')
    self.assertEqual(store.status(key),journal);self.assertEqual(data.evidence(store,original),saved)
    altered={**value,'reason':'altered'};atomic(store.path(key,'.resolution.json'),altered)
    self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'blocked-recovery')
    with self.assertRaises(ValueError):utility.record(store,original,saved,snapshot,data.identity(snapshot),'verified-complete','operator','another reason')


class PreparationTests(unittest.TestCase):
 def test_lost_prepare_response_is_bound_to_request_and_zero_pending_respects_recovery(self):
  with tempfile.TemporaryDirectory() as temp:
   store=PlanStore(Path(temp)/'plans');source=plan()['plan'];observed=source['expected'];calls=[];ledger=[]
   class Host:
    database='fixture_staging';values={'IMAGE_DIGEST':source['image'],'RELEASE_COMMIT':source['sourceCommit']}
    def __init__(self,*args):self.observed=observed
    def serving(self):return {"imageMatches":True,"ready":True}
    def approval_observed(self):return self.observed
    def candidate(self,*args):calls.append('candidate');return MANIFEST
    def probe(self,*args):return ledger
   request=dict(version=2,project='fixture',environment='staging',action='migrate',requiredCapabilities=['data-operations-v1'],configurationHash=source['configurationHash'],image=source['image'],commit=source['sourceCommit'],requestId=source['requestId'])
   with patch.object(data,'Host',Host):
    save=store.save
    with patch.object(store,'save',side_effect=OSError('lost local finalization')):
     with self.assertRaises(OSError):data.route(None,store,request)
    recovered=data.route(None,store,request);self.assertEqual(len(calls),1)
    self.assertEqual(data.route(None,store,request)['planId'],recovered['planId']);self.assertEqual(len(calls),1)
    with self.assertRaisesRegex(ValueError,'REQUEST_ID_REUSED'):data.route(None,store,{**request,'commit':'0'*40})
    fresh=data.route(None,store,{**request,'requestId':'22222222-2222-4222-8222-222222222222'})
    self.assertNotEqual(fresh['planId'],recovered['planId'])
    original=store.read(recovered['planId'])
    atomic(store.path(recovered['planId'],'.data.json'),dict(planId=recovered['planId'],database='fixture_staging',status='unknown',writeIntent=True,verification=[],applied=[]))
    ledger[:]=LEDGER
    blocked=data.route(None,store,{**request,'requestId':'33333333-3333-4333-8333-333333333333'})
    self.assertEqual(blocked['activationDecision'],'blocked-recovery');self.assertNotIn('plan',blocked)
    empty=PlanStore(Path(temp)/'empty')
    nothing=data.route(None,empty,{**request,'requestId':'44444444-4444-4444-8444-444444444444'})
    self.assertEqual(nothing['migrationOutcome'],'not-required');self.assertFalse(list(empty.root.glob('*.plan.json')))


class FirstDeploymentTests(unittest.TestCase):
 def route(self,ledger,action='migrations',**extra):
  source=plan()['plan']
  class Host:
   first=True;database='fixture_staging';values={}
   def __init__(self,*args):self.observed=source['expected']
   def serving(self):return {'imageMatches':False,'ready':False,'sourceCommit':None,'image':None,'firstDeployment':True}
   def candidate(self,*args):return MANIFEST
   def probe(self,*args):return ledger
  request=dict(version=2,project='fixture',environment='staging',action=action,requiredCapabilities=['data-operations-v1'],configurationHash=source['configurationHash'],image=source['image'],commit=source['sourceCommit'],**extra)
  with tempfile.TemporaryDirectory() as temp,patch.object(data,'Host',Host):
   return data.route(None,PlanStore(Path(temp)/'plans'),request)

 def test_report_without_a_release_proceeds_only_when_required_migrations_are_applied(self):
  ready=self.route(LEDGER)
  self.assertEqual(ready['activationDecision'],'proceed');self.assertTrue(ready['serving']['firstDeployment'])
  blocked=self.route([])
  self.assertEqual(blocked['activationDecision'],'owner-action-required');self.assertIn('First deployment',blocked['nextAction'])

 def test_migration_plans_and_implicit_images_are_refused_without_a_release(self):
  with self.assertRaisesRegex(ValueError,'OWNER_ACTION_REQUIRED'):
   self.route([],action='migrate',requestId='55555555-5555-4555-8555-555555555555')
  with self.assertRaisesRegex(ValueError,'IMMUTABLE_IMAGE_REQUIRED'):
   source=plan()['plan']
   class Host:
    first=True;values={}
    def __init__(self,*args):self.observed=source['expected']
   with tempfile.TemporaryDirectory() as temp,patch.object(data,'Host',Host):
    data.route(None,PlanStore(Path(temp)/'plans'),dict(version=2,project='fixture',environment='staging',action='migrations',requiredCapabilities=['data-operations-v1'],configurationHash=source['configurationHash'],image=None,commit=None))

 def test_probe_uses_only_the_verified_candidate_on_the_default_bridge(self):
  host=object.__new__(data.Host)
  host.first=True;host.values={};host.verified_image=None;host.project='fixture';host.target='staging';host.environment='staging';host.database='fixture_staging';host.runtime=Path('/etc/fixture/staging/runtime.env')
  host.d=SimpleNamespace(trusted=lambda path:None,ENV={})
  with self.assertRaisesRegex(ValueError,'IMMUTABLE_IMAGE_REQUIRED'):host.probe('ledger')
  host.verified_image='ghcr.io/test/fixture@sha256:'+'d'*64;calls=[]
  with patch.object(data,'command',lambda args,*rest,**kw:calls.append(args) or b'[]'):
   self.assertEqual(host.probe('ledger'),[])
  args=calls[0];self.assertEqual(args[args.index('--network')+1],'bridge');self.assertEqual(args[-2],host.verified_image)
  self.assertEqual(host.serving()['firstDeployment'],True)


class FirstDeploymentHostTests(unittest.TestCase):
 def host(self,link):
  import operation_engine
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source';(source/'deploy').mkdir(parents=True)
   (source/'deploy/contract.json').write_text(json.dumps({'requiredCapabilities':['operation-lock-v1','data-operations-v1']}))
   runtime=root/'etc/fixture/staging';runtime.mkdir(parents=True);(runtime/'runtime.env').write_text('');(runtime/'runtime.env').chmod(0o600)
   releases=root/'opt/fixture/staging';(releases/'releases/r1').mkdir(parents=True);(releases/'releases/r1/compose.env').write_text('IMAGE_DIGEST=x'+chr(10)+'RELEASE_COMMIT=y'+chr(10))
   if link=='valid':(releases/'current').symlink_to(releases/'releases/r1')
   elif link=='dangling':(releases/'current').symlink_to(releases/'releases/missing')
   d=SimpleNamespace(trusted=lambda path:None,ENV={})
   with patch.object(operation_engine,'state',lambda *a:(source,{'runtime':{'MONGODB_DATABASE':'fixture_staging'}},{})),patch.object(operation_engine,'RELEASES',root/'opt'),patch.object(operation_engine,'RUNTIME',root/'etc'):
    return data.Host(d,'fixture','staging')

 @unittest.skipIf(sys.platform=='win32','POSIX symlink and mode semantics')
 def test_only_a_missing_current_link_is_a_first_deployment(self):
  first=self.host(None);self.assertTrue(first.first);self.assertIsNone(first.compose);self.assertEqual(first.values,{})
  deployed=self.host('valid');self.assertFalse(deployed.first);self.assertEqual(deployed.values['IMAGE_DIGEST'],'x')
  with self.assertRaises(OSError):self.host('dangling')

 def test_first_deployment_decision_is_shared_with_the_activation_gate(self):
  self.assertEqual(data.first_deployment({'activationDecision':'blocked-migrations','nextAction':''})['activationDecision'],'owner-action-required')
  self.assertEqual(data.first_deployment({'activationDecision':'proceed'})['activationDecision'],'proceed')
  gate=(Path(data.__file__).with_name('data-operation-gate.py')).read_text()
  self.assertIn('if host.first:first_deployment(report)',gate)


class ConfigurationIdentityTests(unittest.TestCase):
 def test_private_input_and_controller_identity_is_bound_without_exposing_secrets(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);private=root/'fixture/staging';private.mkdir(parents=True)
   runtime=private/'runtime.env';runtime.write_text('MONGODB_URI=mongodb://user:private-password@fixture\n');runtime.chmod(0o600)
   password=private/'password';password.write_text('private-recovery-password');password.chmod(0o600)
   recovery=private/'recovery.json';recovery.write_text(json.dumps({'passwordFile':str(password)}));recovery.chmod(0o600)
   host=data.Host.__new__(data.Host);host.project='fixture';host.target='staging';host.runtime=runtime;host.d=SimpleNamespace(trusted=lambda _:None);host.observed={'installedRevision':'a'*64,'configurationHash':'b'*64}
   with patch('recovery.RUNTIME',root):
    first=host.approval_observed();runtime.write_text('MONGODB_URI=mongodb://user:changed-password@fixture\n')
    second=host.approval_observed();self.assertNotEqual(first['configurationHash'],second['configurationHash'])
    self.assertNotIn('private-password',json.dumps(first));self.assertNotIn('private-recovery-password',json.dumps(first))


class AuthoritativeJournalTests(unittest.TestCase):
 def test_missing_or_contradictory_journal_blocks_despite_complete_ledger_and_report(self):
  with tempfile.TemporaryDirectory() as temp:
   store=PlanStore(Path(temp)/'plans');envelope=plan();key=store.save(envelope);original=envelope['plan']
   saved=dict(version=1,planId=key,database='fixture_staging',status='completed',phase='health',writeIntent=True,backup=dict(verified=True,backupId='2'*64,sha256='3'*64,database='fixture_staging'),writers=['app'],writersRestored=True,health=True,runnerGone=True,verification=[ROW],applied=[ROW])
   atomic(store.path(key,'.data.json'),saved)
   self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'blocked-recovery')
   atomic(store.path(key,'.journal.json'),dict(planId=key,status='completed',active=None,completed=['backup','migrate','verify']))
   self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'proceed')
   atomic(store.path(key,'.journal.json'),dict(planId=key,status='failed',active=None,completed=['backup']))
   self.assertEqual(data.activation(store,MANIFEST,LEDGER,'staging','fixture_staging')['activationDecision'],'blocked-recovery')
