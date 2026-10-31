import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('plans',Path(__file__).resolve().parents[1]/'scripts/operation_plan.py')
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.candidate=dict(project='fixture',environment='staging',sourceCommit='a'*40,
            image='ghcr.io/test/fixture@sha256:'+'b'*64,bundleChecksum='c'*64,configurationHash='d'*64,
            classification='host-configuration',changedSettings=['runtime.MCP_CLIENTS_JSON'],credentialReferences=['MCP_TOKEN_DIFY'])
        self.observed=dict(installedRevision='e'*64,configurationHash='f'*64)
        self.trust=dict(repositoryId='1',ownerId='2',ref='refs/heads/main',executorRef='test/infra/.github/workflows/executor.yml@'+'a'*40,executorSha='a'*40,adminIds=['3'])
        self.claims=dict(iss=p.ISSUER,aud='uniwares:plan:'+'b'*64,repository_id='1',repository_owner_id='2',ref='refs/heads/main',job_workflow_ref=self.trust['executorRef'],job_workflow_sha='a'*40,event_name='workflow_dispatch',run_attempt='1',actor_id='3',jti='fixture-unique',iat=100,nbf=100,exp=400)

    def test_digest_binds_exact_candidate_and_expected_state(self):
        prepared=p.prepare(self.candidate,self.observed)
        self.assertEqual(prepared['digest'],p.digest(prepared['plan']))
        changed={**self.observed,'installedRevision':'0'*64}
        self.assertNotEqual(prepared['digest'],p.prepare(self.candidate,changed)['digest'])
        for field in ['command','privateValues']:
            with self.assertRaises(ValueError): p.prepare({**self.candidate,field:'canary'},self.observed)
        for classification in ['provider','data-migration','arbitrary']:
            with self.assertRaises(ValueError): p.prepare({**self.candidate,'classification':classification},self.observed)

    def test_claims_reject_wrong_identity_digest_or_time(self):
        self.assertEqual(len(p.verify_claims(self.claims,self.trust,'b'*64,200)),64)
        for field in ['actor_id','repository_id','repository_owner_id','ref','job_workflow_ref','job_workflow_sha','event_name','run_attempt','iss','aud']:
            with self.subTest(field=field),self.assertRaises(ValueError):
                p.verify_claims({**self.claims,field:'wrong'},self.trust,'b'*64,200)
        for now in [99,400,401]:
            with self.assertRaises(ValueError): p.verify_claims(self.claims,self.trust,'b'*64,now)
        with self.assertRaises(ValueError): p.verify_claims(self.claims,self.trust,'c'*64,200)

    def test_setting_values_are_not_a_plan_input(self):
        for value in [['MCP_TOKEN_DIFY=secret'],['\nprivate'],{'token':'secret'}]:
            with self.assertRaises(ValueError): p.prepare({**self.candidate,'credentialReferences':value},self.observed)
