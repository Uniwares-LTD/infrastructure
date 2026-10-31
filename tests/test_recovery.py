"""Recovery command boundaries with disposable data and no provider access."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import recovery
from operation_plan import digest

class RecoveryTests(unittest.TestCase):
 def test_staging_and_production_backup_preserve_writers_and_hide_credentials(self):
  for target,action,failure in [('staging','backup',False),('production','backup',False),('staging','restore',False),('production','restore',False),('staging','restore',True),('production','restore',True)]:
   with self.subTest(target=target,action=action,failure=failure),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);etc=root/'etc';control=root/'control';state=root/'state';releases=root/'releases'
    private=etc/'fixture'/target;private.mkdir(parents=True)
    password=private/'restic-password';password.write_text('synthetic-restic-secret');password.chmod(0o600)
    credentials=dict(repository='s3:https://backup.example/bucket',passwordFile=str(password),accessKeyId='synthetic-access',secretAccessKey='synthetic-secret',mongoUri='mongodb://user:synthetic-password@database',database='fixture_'+target)
    path=private/'recovery.json';path.write_text(json.dumps(credentials));path.chmod(0o600)
    source=control/'fixture'/('a'*64)/'deploy/environments';source.mkdir(parents=True)
    (source/(target+'.json')).write_text(json.dumps({'runtime':{'MONGODB_DATABASE':'fixture_'+target}}))
    release=releases/'fixture'/target/'releases/one';release.mkdir(parents=True)
    for name in ['compose.env','compose.yml']:(release/name).write_text('fixture')
    (release.parent.parent/'current').symlink_to(release,target_is_directory=True)
    (state/'fixture/operation-plans').mkdir(parents=True)
    plan=dict(project='fixture',environment='prod' if target=='production' else target,expected={'installedRevision':'a'*64},classification=action,recoveryRequest={'backupId':'a'*64 if action=='restore' else None,'destination':'fixture_'+target+('_rehearsal_test' if action=='restore' else '')})
    calls=[]
    def run(args,env=None):
     calls.append(args)
     self.assertNotIn('synthetic-password',' '.join(args));self.assertNotIn('synthetic-secret',' '.join(args))
     if 'ps' in args:return b'app\nworker\n'
     if args[0]=='mongodump':
      archive=Path(next(x.split('=',1)[1] for x in args if x.startswith('--archive=')));archive.write_bytes(b'synthetic MongoDB and GridFS archive')
      return b''
     if args[:2]==['restic','restore']:
      restored=Path(args[-1]);archive=restored/'database.archive';archive.write_bytes(b'restored synthetic data')
      import hashlib
      (restored/'manifest.json').write_text(json.dumps(dict(project='fixture',environment=plan['environment'],database='fixture_'+target,sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
     if args[0]=='mongorestore' and failure:
      saved=json.loads((state/'fixture/operation-plans'/(digest(plan)+'.recovery.json')).read_text())
      self.assertEqual(saved['preRestoreBackupId'],'b'*64)
      raise ValueError('synthetic partial restore failure')
     if args[:2]==['restic','backup']:return json.dumps({'message_type':'summary','snapshot_id':'b'*64}).encode()
     return b''
    d=SimpleNamespace(CONTROL=control,STATE=state,ENV={'PATH':'/usr/bin'},trusted=lambda path:None)
    with patch.object(recovery,'RUNTIME',etc),patch.object(recovery,'RELEASES',releases),patch.object(recovery,'run',run):
     if failure:
      with self.assertRaisesRegex(ValueError,'partial restore'):recovery.execute(plan,d)
     else:recovery.execute(plan,d)
    self.assertEqual(next(c for c in calls if 'stop' in c)[-3:],['stop','app','worker'])
    if failure:
     self.assertFalse(any('start' in c for c in calls))
    else:self.assertEqual(calls[-1][-3:],['start','app','worker'])
    result=json.loads((state/'fixture/operation-plans'/(digest(plan)+'.recovery.json')).read_text())
    self.assertEqual(result['backupId'],('a' if action=='restore' else 'b')*64)
    if failure:
     self.assertEqual(result['status'],'restore-outcome-unknown')
     self.assertEqual(result['writersStopped'],['app','worker'])
    if action=='restore':
     self.assertEqual(result['preRestoreBackupId'],'b'*64)
     self.assertTrue(any('--nsTo=fixture_'+target+'_rehearsal_test.*' in c for c in calls))
    self.assertFalse(any('forget' in c or 'prune' in c for c in calls))
