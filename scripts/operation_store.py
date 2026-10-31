"""Protected immutable plans, one-use approvals, and checkpointed fixed operations."""
import json
import os
from pathlib import Path
import re
import tempfile
from operation_plan import canonical, digest, hex_value


def atomic(path,value):
    fd,temp=tempfile.mkstemp(prefix='.operation-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600)
            stream.write(canonical(value)+b'\n');stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(temp): os.unlink(temp)


class PlanStore:
    """Caller holds the application's operation lock for every method."""
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(mode=0o700,parents=False,exist_ok=True)
        if self.root.is_symlink() or self.root.stat().st_mode & 0o077:
            raise ValueError('UNTRUSTED_PLAN_STORE')

    def path(self,identity,suffix):
        if not hex_value(identity,64): raise ValueError('INVALID_PLAN_ID')
        return self.root/(identity+suffix)

    def save(self,envelope):
        identity=envelope['digest']
        if digest(envelope['plan'])!=identity: raise ValueError('PLAN_DIGEST_MISMATCH')
        path=self.path(identity,'.plan.json')
        if path.exists():
            if json.loads(path.read_text())!=envelope: raise ValueError('PLAN_CHANGED')
        else: atomic(path,envelope)
        return identity

    def read(self,identity):
        envelope=json.loads(self.path(identity,'.plan.json').read_text())
        if envelope['digest']!=identity or digest(envelope['plan'])!=identity:
            raise ValueError('PLAN_DIGEST_MISMATCH')
        return envelope['plan']

    def status(self,identity):
        self.read(identity)
        path=self.path(identity,'.journal.json')
        if not path.exists(): return dict(planId=identity,status='prepared',completed=[],active=None)
        return json.loads(path.read_text())

    def apply(self,identity,approval_id,observed,executors,readbacks):
        plan=self.read(identity)
        journal=self.status(identity)
        # A consumed approval cannot authorize another attempt, including completed plans.
        replay=self.path(approval_id,'.approval-used')
        if replay.exists(): raise ValueError('APPROVAL_REPLAY')
        if journal['status']=='prepared' and observed!=plan['expected']:
            raise ValueError('HOST_STATE_CHANGED')
        active=journal.get('active')
        if journal.get('expectedAfter',plan['expected'])!=observed:
            if active not in ('configure','deploy','check') or active not in readbacks or not readbacks[active](plan):
                raise ValueError('HOST_STATE_CHANGED')
            journal['expectedAfter']=observed
        if any(name not in executors for name in plan['operations']):
            raise ValueError('OWNER_ACTION_REQUIRED')
        atomic(replay,{'planId':identity})
        if journal['status']=='completed': return journal
        active=journal.get('active')
        if active:
            # Never replay a possibly completed mutation without conclusive readback.
            if active not in readbacks or not readbacks[active](plan):
                raise ValueError('READBACK_REQUIRED')
            journal['completed'].append(active);journal['active']=None
            atomic(self.path(identity,'.journal.json'),journal)
        for name in plan['operations']:
            if name in journal['completed']: continue
            journal.update(status='unknown',active=name)
            atomic(self.path(identity,'.journal.json'),journal)
            result=executors[name](plan)
            journal['completed'].append(name);journal['active']=None
            if result is not None: journal['expectedAfter']=result
            atomic(self.path(identity,'.journal.json'),journal)
        journal['status']='completed'
        atomic(self.path(identity,'.journal.json'),journal)
        return journal
