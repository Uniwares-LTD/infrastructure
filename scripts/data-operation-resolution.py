#!/usr/bin/python3 -IB
"""Root-only inspection/acknowledgment. No migrations, database restore or restart."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from data_operations import Host,DataExecutor,identity,evidence,resolution,validate_resolution,process_start,command,completed,successful_evidence
from operation_plan import digest
from operation_store import PlanStore,atomic


@contextmanager
def inspect(d,store,plan):
    from recovery import BackupSession
    key=digest(plan);data=evidence(store,plan)
    if not data:raise ValueError('NO_UNRESOLVED_OPERATION')
    if successful_evidence(store,plan,data):raise ValueError('NO_UNRESOLVED_OPERATION')
    host=Host(d,plan['project'],plan['environment'])
    if host.database!=plan['migrationRequest']['database']:raise ValueError('PLAN_IDENTITY_MISMATCH')
    manifest=host.candidate(plan['image'],plan['sourceCommit'])
    if identity(manifest)!=plan['migrationRequest']['manifestDigest']:raise ValueError('ORIGINAL_IMAGE_REQUIRED')
    process=None
    with tempfile.TemporaryDirectory(prefix='.inspect-',dir=d.STATE/plan['project']) as temp:
        session=BackupSession(plan,d,temp)
        try:
            # Reuse only the fixed pipe reader/runner launcher, never executor close/finalization.
            runner=DataExecutor.__new__(DataExecutor)
            runner.d,runner.store,runner.plan,runner.key,runner.host=d,store,plan,key,host
            runner.name=plan['project']+'-inspection-'+key
            runner.deadline=runner.phase_deadline=time.monotonic()+1800;runner.buffer=b'';runner.process=None
            runner.start(verify=True);process=runner.process
            result=runner.receive()
            if result.get('type')!='inspection-ready':raise ValueError('VERIFICATION_REQUIRED')
            original_name=plan['project']+'-data-'+key
            active=command(['docker','ps','-q','--filter','name=^/'+original_name+'$'],d).strip()
            pid=data.get('runnerPid');start=data.get('runnerStart')
            predecessor_gone=not active and bool(pid and start and process_start(pid)!=start)
            writers=session.writers();backup=data.get('backup');backup_verified=False
            if backup and backup.get('verified'):
                session.retrieve(backup['backupId'],host.database,backup['sha256']);backup_verified=True
            healthy=d.execute_with_lock(dict(version=2,project=plan['project'],environment=plan['environment'],action='check',configurationHash=host.observed['configurationHash']),int(os.environ['UNIWARES_RESOLUTION_LOCK_FD']))==0
            # Renew/revalidate under the same lease after archive and health readback.
            runner.send({'type':'validate','planId':key});result=runner.receive()
            if result.get('type')!='inspection-ready':raise ValueError('INSPECTION_LEASE_LOST')
            expected=plan['migrationRequest']['pending'];recorded={r['id']:r for r in result['ledger']}
            recorded_batch=[row for row in expected if row['id'] in recorded and recorded[row['id']]['checksum']==row['checksum']]
            verified_ids=[row['id'] for row in result['verification']]
            verified=[row for row in recorded_batch if row['id'] in verified_ids]
            snapshot=dict(planDigest=key,journalDigest=digest(store.status(key)),dataDigest=digest(data),project=plan['project'],environment=plan['environment'],database=host.database,manifestDigest=identity(manifest),current=dict(host.observed,dataConfigurationHash=host.approval_observed()['configurationHash']),ledger=result['ledger'],recorded=recorded_batch,verification=verified,verifierResults=result['verification'],predecessorGone=predecessor_gone,leaseAcquired=True,writers=writers,writersRestored=writers==data['writers'],health=healthy,backupVerified=backup_verified,backup=backup)
            yield snapshot,data
            runner.send({'type':'release','planId':key});process.stdin.close();process.wait(timeout=30)
            if process.returncode:raise ValueError('INSPECTION_LEASE_LOST')
        finally:
            if process is not None:
                if process.poll() is None:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                process.wait();process.stdout.close()
                if not process.stdin.closed:process.stdin.close()
                try:command(['docker','rm','-f',runner.name],d,timeout=30)
                except Exception:pass


def record(store,plan,data,snapshot,expected,disposition,operator,reason):
    successful_evidence(store,plan,data)
    if identity(snapshot)!=expected:raise ValueError('INSPECTED_STATE_CHANGED')
    if not operator.strip() or not reason.strip() or len(operator)>200 or len(reason)>2000:raise ValueError('OPERATOR_AND_REASON_REQUIRED')
    validate_resolution(plan,data,snapshot,disposition)
    path=store.path(digest(plan),'.resolution.json')
    value=dict(version=1,planId=digest(plan),journalDigest=digest(store.status(digest(plan))),dataDigest=digest(data),project=plan['project'],environment=plan['environment'],database=plan['migrationRequest']['database'],stateHash=expected,inspection=snapshot,disposition=disposition,operator=operator,reason=reason,observedAt=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    value['recordDigest']=digest(value)
    if path.exists():
        previous=resolution(store,plan,data)
        if any(previous[k]!=value[k] for k in value if k not in ('recordDigest','observedAt')):raise ValueError('RESOLUTION_CONFLICT')
        return previous
    atomic(path,value)
    return value


def main():
    if os.geteuid()!=0:raise ValueError('ROOT_REQUIRED')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True);parser.add_argument('--environment',choices=['staging','prod'],required=True)
    parser.add_argument('--plan-id',required=True)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--inspect',action='store_true');mode.add_argument('--record',action='store_true')
    parser.add_argument('--expected-state-hash');parser.add_argument('--disposition',choices=['safe-to-retry','verified-complete']);parser.add_argument('--operator');parser.add_argument('--reason')
    args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{2,39}',args.project) or not re.fullmatch('[a-f0-9]{64}',args.plan_id):raise ValueError('INVALID_IDENTITY')
    path=Path(__file__).with_name('deploy-dispatch.py')
    spec=importlib.util.spec_from_file_location('data_resolution_dispatch',path);d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
    d.trusted(path)
    with d.operation_lock(args.project) as fd:
        os.environ['UNIWARES_RESOLUTION_LOCK_FD']=str(fd)
        store=PlanStore(d.STATE/args.project/'operation-plans');plan=store.read(args.plan_id)
        if plan['project']!=args.project or plan['environment']!=args.environment or plan.get('classification')!='data-migration':raise ValueError('PLAN_IDENTITY_MISMATCH')
        if args.record and store.path(args.plan_id,'.resolution.json').exists():
            previous=resolution(store,plan,evidence(store,plan))
            if previous['stateHash']!=args.expected_state_hash or previous['disposition']!=args.disposition or previous['operator']!=args.operator or previous['reason']!=args.reason:raise ValueError('RESOLUTION_CONFLICT')
            print(json.dumps({'planId':args.plan_id,'stateHash':previous['stateHash'],'disposition':previous['disposition'],'recorded':True}));return
        with inspect(d,store,plan) as (snapshot,data):
            state_hash=identity(snapshot)
            if args.inspect:result={'planId':args.plan_id,'stateHash':state_hash,'inspection':snapshot}
            else:
                if not all((args.expected_state_hash,args.disposition,args.operator,args.reason)):raise ValueError('RECORD_ARGUMENTS_REQUIRED')
                settled=record(store,plan,data,snapshot,args.expected_state_hash,args.disposition,args.operator,args.reason)
                result={'planId':args.plan_id,'stateHash':state_hash,'disposition':settled['disposition'],'recorded':True}
                # Optional copy metadata only; original outcome is immutable.
                from data_operations import terminal_report
                try:Host(d,args.project,args.environment).probe('report',report=terminal_report(plan,data),resolution={k:settled[k] for k in ('disposition','operator','reason','observedAt')})
                except Exception:pass
        print(json.dumps(result,separators=(',',':')))

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Recovery acknowledgment refused. Inspect original identity, evidence and writer/process safety; private details suppressed.') from None
