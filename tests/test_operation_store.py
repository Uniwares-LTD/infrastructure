import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import os
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from operation_store import PlanStore, RetryableOperationFailure
from operation_plan import digest

@unittest.skipUnless(os.name == 'posix', 'Protected store requires POSIX permissions')
class StoreTests(unittest.TestCase):
    def test_replay_changed_state_and_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            store=PlanStore(Path(temp)/'plans')
            observed={'installedRevision':'a'*64,'configurationHash':'b'*64}
            plan={'operations':['configure','deploy','check'],'expected':observed}
            identity=store.save({'plan':plan,'digest':digest(plan)})
            with self.assertRaisesRegex(ValueError,'HOST_STATE_CHANGED'):
                store.apply(identity,'1'*64,{}, {}, {})
            calls=[]
            def configure(plan): calls.append('configure');return observed
            def deploy(plan): calls.append('deploy');raise RuntimeError('interrupted')
            executors={'configure':configure,'deploy':deploy,'check':lambda plan:calls.append('check')}
            with self.assertRaises(RuntimeError): store.apply(identity,'1'*64,observed,executors,{})
            self.assertEqual(store.status(identity)['active'],'deploy')
            with self.assertRaisesRegex(ValueError,'APPROVAL_REPLAY'):
                store.apply(identity,'1'*64,observed,executors,{})
            with self.assertRaisesRegex(ValueError,'READBACK_REQUIRED'):
                store.apply(identity,'2'*64,observed,executors,{})
            status=store.apply(identity,'3'*64,observed,executors,{'deploy':lambda plan:True})
            self.assertEqual(status['status'],'completed')
            self.assertEqual(calls,['configure','deploy','check'])
            with self.assertRaisesRegex(ValueError,'APPROVAL_REPLAY'):
                store.apply(identity,'3'*64,observed,executors,{})

    def test_known_failure_resumes_without_repeating_completed_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            store=PlanStore(Path(temp)/'plans')
            observed={'installedRevision':'a'*64,'configurationHash':'b'*64}
            plan={'operations':['configure','deploy'],'expected':observed}
            identity=store.save({'plan':plan,'digest':digest(plan)})
            calls=[]
            def failed(plan):raise RetryableOperationFailure('verified previous release')
            with self.assertRaises(RetryableOperationFailure):
                store.apply(identity,'1'*64,observed,{'configure':lambda plan:calls.append('configure'),'deploy':failed},{})
            self.assertEqual(store.status(identity)['status'],'failed')
            result=store.apply(identity,'2'*64,observed,{'configure':lambda plan:calls.append('incorrect repeat'),'deploy':lambda plan:calls.append('deploy')},{})
            self.assertEqual(result['status'],'completed')
            self.assertEqual(calls,['configure','deploy'])
