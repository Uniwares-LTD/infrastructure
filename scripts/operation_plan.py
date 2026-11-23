"""Strict public operation plans and GitHub approval verification.

This module has no arbitrary command interface. Installed executors are selected
by fixed operation names; caller-supplied paths or shell text are never accepted.
"""
import hashlib
import json
import re
import time

ISSUER='https://token.actions.githubusercontent.com'
CAPABILITIES=['operation-lock-v1','plans-v2','github-oidc-v1','image-retention-v1','data-operations-v1']
OPERATIONS={'image-only':['deploy','check'], 'host-configuration':['configure','deploy','check'],
            'controller':['controller','check'], 'backup':['backup'], 'restore':['restore'], 'provider':[], 'data-migration':['backup','migrate','verify']}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def hex_value(value,length):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{'+str(length)+'}',value) is not None


def prepare(candidate,observed):
    required={'project','environment','sourceCommit','image','bundleChecksum','configurationHash','classification','changedSettings','credentialReferences'}
    if isinstance(candidate,dict) and candidate.get('classification')=='controller':
        required.add('controllerExpectedChecksum')
        if not hex_value(candidate.get('controllerExpectedChecksum'),64):raise ValueError('CONTROLLER_CHECKSUM_REQUIRED')
    if isinstance(candidate,dict) and candidate.get('classification') in ('backup','restore'):
        required.add('recoveryRequest')
        recovery=candidate.get('recoveryRequest')
        if not isinstance(recovery,dict) or set(recovery)!={'backupId','destination'} or not isinstance(recovery['destination'],str) or not re.fullmatch(r'[A-Za-z0-9_]{1,64}',recovery['destination']):
            raise ValueError('INVALID_RECOVERY_TARGET')
        if candidate['classification']=='restore' and not hex_value(recovery['backupId'],64):
            raise ValueError('EXPLICIT_BACKUP_ID_REQUIRED')
        if candidate['classification']=='backup' and recovery['backupId'] is not None:
            raise ValueError('INVALID_BACKUP_REQUEST')
    if isinstance(candidate,dict) and 'requestId' in candidate:
        import uuid
        required.add('requestId')
        try:
            if str(uuid.UUID(candidate['requestId']))!=candidate['requestId']:raise ValueError()
        except (ValueError,TypeError,AttributeError):raise ValueError('INVALID_REQUEST_ID') from None
    if isinstance(candidate,dict) and candidate.get('classification')=='data-migration':
        required.update({'migrationRequest','requestId'})
        request=candidate.get('migrationRequest')
        if not isinstance(request,dict) or set(request)!={'database','manifestDigest','ledgerDigest','pending','backupPolicy'} or not re.fullmatch('[A-Za-z0-9_]{1,64}',request.get('database','')) or not hex_value(request.get('manifestDigest'),64) or not hex_value(request.get('ledgerDigest'),64) or request.get('backupPolicy')!={'mode':'create','verification':'archive'}:raise ValueError('INVALID_MIGRATION_REQUEST')
        pending=request['pending']
        if not isinstance(pending,list) or not pending or len(pending)>1000 or any(not isinstance(row,dict) or set(row)!={'id','checksum'} or not isinstance(row['id'],str) or not re.fullmatch(r'(core|[a-z][a-z0-9-]{1,39}):\d{4}-[a-z0-9-]+',row['id']) or not hex_value(row['checksum'],64) for row in pending) or len({row['id'] for row in pending})!=len(pending):raise ValueError('INVALID_MIGRATION_REQUEST')
    if not isinstance(candidate,dict) or set(candidate)!=required:
        raise ValueError('INVALID_PLAN')
    if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}',candidate['project']) or candidate['environment'] not in ('staging','prod'):
        raise ValueError('INVALID_IDENTITY')
    if not hex_value(candidate['sourceCommit'],40) or any(not hex_value(candidate[key],64) for key in ('bundleChecksum','configurationHash')):
        raise ValueError('INVALID_IDENTITY')
    if not re.fullmatch(r'ghcr.io/[a-z0-9_.-]+/[a-z0-9_.-]+@sha256:[a-f0-9]{64}',candidate['image']):
        raise ValueError('IMMUTABLE_IMAGE_REQUIRED')
    classification=candidate['classification']
    if classification not in OPERATIONS or not OPERATIONS[classification]:
        raise ValueError('OWNER_ACTION_REQUIRED')
    for field in ('changedSettings','credentialReferences'):
        if not isinstance(candidate[field],list) or len(candidate[field])>128 or any(not isinstance(name,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]{0,127}',name) for name in candidate[field]):
            raise ValueError('SETTING_NAMES_ONLY')
    if set(observed) not in ({'installedRevision','configurationHash'},{'installedRevision','configurationHash','releaseIdentity'}) or any(not hex_value(value,64) for value in observed.values()):
        raise ValueError('INVALID_OBSERVED_STATE')
    plan=dict(version=2,**candidate,expected=dict(observed),operations=OPERATIONS[classification],
              interruption='brief',verification=['controller','web','workers','readiness'],
              recovery='Inspect status; image/config rollback is separate from database restore')
    return dict(plan=plan,digest=digest(plan))


def verify_claims(claims,trust,plan_digest,now=None):
    now=time.time() if now is None else now
    expected={'iss':ISSUER,'aud':'uniwares:plan:'+plan_digest,'repository_id':trust['repositoryId'],
              'repository_owner_id':trust['ownerId'],'event_name':'workflow_dispatch',
              'ref':trust['ref'],'run_attempt':'1','job_workflow_ref':trust['executorRef'],
              'job_workflow_sha':trust['executorSha']}
    if any(claims.get(key)!=value for key,value in expected.items()):
        raise ValueError('APPROVAL_IDENTITY_REJECTED')
    if claims.get('actor_id') not in trust['adminIds']:
        raise ValueError('ADMIN_NOT_ENROLLED')
    if not isinstance(claims.get('jti'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',claims['jti']):
        raise ValueError('INVALID_APPROVAL_ID')
    for key in ('iat','nbf','exp'):
        if type(claims.get(key)) is not int: raise ValueError('INVALID_APPROVAL_TIME')
    if claims['nbf']>now or claims['iat']>now or claims['exp']<=now or claims['exp']-claims['iat']>600:
        raise ValueError('APPROVAL_EXPIRED')
    return hashlib.sha256(claims['jti'].encode()).hexdigest()


def verify_token(token,trust,plan_digest):
    # Import only for approved execution. Offline planning has no JWT dependency.
    import jwt
    if not isinstance(token,str) or len(token)>16384: raise ValueError('INVALID_APPROVAL')
    client=jwt.PyJWKClient(ISSUER+'/.well-known/jwks',timeout=10)
    key=client.get_signing_key_from_jwt(token)
    claims=jwt.decode(token,key.key,algorithms=['RS256'],issuer=ISSUER,
                      audience='uniwares:plan:'+plan_digest,
                      options={'require':['exp','iat','nbf','jti','iss','aud','sub']})
    return verify_claims(claims,trust,plan_digest)
