import json
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from operation_plan import verify_token,ISSUER
try:
 import jwt
 from cryptography.hazmat.primitives.asymmetric import rsa
except ImportError:
 jwt=None

@unittest.skipIf(jwt is None,'Install requirements-controller.txt for signed JWT acceptance')
class SignedApprovalTests(unittest.TestCase):
 def test_signature_expiry_algorithm_and_identity(self):
  key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
  wrong=rsa.generate_private_key(public_exponent=65537,key_size=2048)
  now=int(time.time())
  trust=dict(repositoryId='1',ownerId='2',ref='refs/heads/main',executorRef='test/infra/.github/workflows/executor.yml@'+'a'*40,executorSha='a'*40,adminIds=['3'])
  claims=dict(iss=ISSUER,aud='uniwares:plan:'+'b'*64,sub='repo:test/infra:ref:refs/heads/main',repository_id='1',repository_owner_id='2',ref=trust['ref'],job_workflow_ref=trust['executorRef'],job_workflow_sha=trust['executorSha'],event_name='workflow_dispatch',run_attempt='1',actor_id='3',jti='signed-fixture',iat=now,nbf=now,exp=now+300)
  with patch.object(jwt.PyJWKClient,'get_signing_key_from_jwt',return_value=SimpleNamespace(key=key.public_key())):
   self.assertEqual(len(verify_token(jwt.encode(claims,key,algorithm='RS256'),trust,'b'*64)),64)
   for token in [jwt.encode(claims,wrong,algorithm='RS256'),jwt.encode({**claims,'exp':now-1},key,algorithm='RS256'),jwt.encode({**claims,'actor_id':'4'},key,algorithm='RS256'),jwt.encode(claims,'canary-secret-at-least-thirty-two-bytes',algorithm='HS256')]:
    with self.assertRaises(Exception):verify_token(token,trust,'b'*64)
