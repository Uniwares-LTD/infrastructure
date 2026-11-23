"""Data-operation catalog, fixed Docker boundary and authoritative activation evidence."""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tempfile
import time
import uuid
from operation_plan import digest, hex_value, prepare
from operation_store import atomic

CAPABILITY='data-operations-v1'
MAX_REPORT=8*1024*1024

def identity(value):
    # Match Unibase's UTF-8 canonical JSON, including non-ASCII descriptions.
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def catalog(manifest,project):
    if not isinstance(manifest,dict) or set(manifest)!={'version','project','enabledOwners','migrations','runnerSha256'} or manifest['version']!=1 or manifest['project']!=project or not hex_value(manifest['runnerSha256'],64):raise ValueError('INVALID_MIGRATION_MANIFEST')
    owners=manifest['enabledOwners'];rows=manifest['migrations']
    if not isinstance(owners,list) or 'core' not in owners or len(set(owners))!=len(owners) or any(not isinstance(o,str) or not re.fullmatch('[a-z][a-z0-9-]{1,39}',o) for o in owners):raise ValueError('INVALID_MIGRATION_MANIFEST')
    if not isinstance(rows,list) or len(rows)>1000:raise ValueError('OWNER_ACTION_REQUIRED')
    seen=set();last={}
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'id','description','releasePhase','checksum','hasVerifier'}:raise ValueError('INVALID_MIGRATION_MANIFEST')
        match=re.fullmatch(r'(core|[a-z][a-z0-9-]{1,39}):(\d{4})-[a-z0-9-]+',row['id'])
        if not match or row['id'] in seen or int(match[2])<=last.get(match[1],0) or not hex_value(row['checksum'],64) or row['releasePhase'] not in ('before-release','after-release','bespoke') or type(row['hasVerifier']) is not bool or not isinstance(row['description'],str) or len(row['description'])>2000:raise ValueError('INVALID_MIGRATION_MANIFEST')
        seen.add(row['id']);last[match[1]]=int(match[2])
    return manifest


def review(manifest,ledger):
    known={m['id']:m for m in manifest['migrations']};recorded={}
    for row in ledger:
        if not isinstance(row,dict) or set(row)!={'id','checksum','appliedAt','durationMs'} or not isinstance(row['id'],str) or row['id'] in recorded or not hex_value(row['checksum'],64) or not isinstance(row['appliedAt'],str) or not isinstance(row['durationMs'],(int,float)):raise ValueError('INVALID_MIGRATION_LEDGER')
        recorded[row['id']]=row
    ledger=sorted(ledger,key=lambda x:x['id'])
    disabled=[m['id'] for m in known.values() if m['id'].split(':')[0] not in manifest['enabledOwners']]
    pending=[m for m in known.values() if m['id'] not in recorded and m['id'] not in disabled]
    changed=[m['id'] for m in known.values() if m['id'] in recorded and recorded[m['id']]['checksum']!=m['checksum']]
    unknown=[key for key in recorded if key not in known]
    bespoke=[m['id'] for m in pending if m['releasePhase']=='bespoke' or not m['hasVerifier']]
    required=[m['id'] for m in pending if m['releasePhase']=='before-release']
    decision='owner-action-required' if changed or unknown or bespoke else 'blocked-migrations' if required else 'proceed'
    return dict(version=1,project=manifest['project'],ledger=ledger,ledgerDigest=identity(ledger),applied=list(recorded),pending=pending,disabled=disabled,changed=changed,unknown=unknown,bespoke=bespoke,required=required,activationDecision=decision,
        nextAction='Review candidate/ledger compatibility with the data owner.' if decision=='owner-action-required' else 'Prepare and approve backup and migration before activation.' if required else 'Compatible backfills may be prepared separately.' if pending else 'No pending migrations.')


def command(args,d,stdin=None,timeout=60,limit=MAX_REPORT,env=None):
    """Bounded output and complete process-group cleanup, without raw stderr."""
    process=None
    try:
        with tempfile.TemporaryFile() as output:
            process=subprocess.Popen(args,env=env or d.ENV,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,stdout=output,stderr=subprocess.DEVNULL,start_new_session=True)
            process.communicate(stdin,timeout=timeout)
            if process.returncode:raise ValueError('DATA_OPERATION_PREREQUISITE_FAILED')
            output.seek(0);raw=output.read(limit+1)
            if len(raw)>limit:raise ValueError('OWNER_ACTION_REQUIRED')
            return raw
    except BaseException:
        if process is not None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()
        raise


class Host:
    def __init__(self,d,project,environment):
        from operation_engine import state, RELEASES, RUNTIME
        self.d,self.project,self.environment=d,project,environment
        self.source,self.config,self.observed=state(d,project,environment)
        if CAPABILITY not in json.loads((self.source/'deploy/contract.json').read_text()).get('requiredCapabilities',[]):raise ValueError('UNSUPPORTED_CAPABILITY')
        target='production' if environment=='prod' else environment
        self.target=target
        self.release=(RELEASES/project/target/'current').resolve();d.trusted(self.release)
        if not self.release.is_relative_to(RELEASES/project/target/'releases'):raise ValueError('UNTRUSTED_RELEASE')
        self.values=dict(line.split('=',1) for line in (self.release/'compose.env').read_text().splitlines() if '=' in line)
        self.runtime=RUNTIME/project/target/'runtime.env';d.trusted(self.runtime)
        self.database=self.config['runtime']['MONGODB_DATABASE']
        if self.runtime.stat().st_mode & 0o077:raise ValueError('UNTRUSTED_RUNTIME')
        self.compose=['docker','compose','--project-name',project+'-'+target,'--env-file',str(self.release/'compose.env'),'-f',str(self.release/'compose.yml')]

    def serving(self):
        containers=command(self.compose+['ps','--all','--quiet','app'],self.d).decode().split()
        matches=False
        if len(containers)==1 and re.fullmatch('[a-f0-9]{12,64}',containers[0]):
            running=json.loads(command(['docker','inspect','--format','{{json .}}',containers[0]],self.d))
            matches=running.get('Config',{}).get('Image')==self.values['IMAGE_DIGEST']
        ready=False
        try:
            port=int(self.values['APP_PORT'])
            if not 1<=port<=65535:raise ValueError()
            status=json.loads(command(['curl','--fail','--silent','--max-time','10','http://127.0.0.1:'+str(port)+'/api/health/ready'],self.d,timeout=15))
            ready=status.get('status')=='ready' and status.get('commit')==self.values['RELEASE_COMMIT']
        except Exception:pass
        return {'imageMatches':matches,'ready':ready,'sourceCommit':self.values['RELEASE_COMMIT'],'image':self.values['IMAGE_DIGEST']}

    def approval_observed(self):
        # Keep the v2 plan shape: expected.configurationHash binds private host
        # inputs as well as the public configuration for this new capability.
        from recovery import RUNTIME,file_hash
        private=RUNTIME/self.project/self.target/'recovery.json';self.d.trusted(private)
        if private.stat().st_mode & 0o077:raise ValueError('RECOVERY_CREDENTIAL_PERMISSIONS')
        config=json.loads(private.read_text());password=Path(config['passwordFile']);self.d.trusted(password)
        if password.stat().st_mode & 0o077:raise ValueError('RECOVERY_CREDENTIAL_PERMISSIONS')
        return dict(self.observed,configurationHash=digest({'public':self.observed['configurationHash'],'runtime':file_hash(self.runtime),'recovery':file_hash(private),'password':file_hash(password),'controller':{item.name:file_hash(item) for item in sorted(Path(__file__).parent.iterdir()) if item.suffix in ('.py','.cjs')}}))

    def base(self,image):
        return ['docker','run','--rm','-i','--user','1001:1001','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network',self.project+'-'+self.target+'_application','--env-file',str(self.runtime),'--entrypoint','node',image]

    def probe(self,action,**values):
        script=Path(__file__).with_name('data-operation-probe.cjs');self.d.trusted(script)
        request=dict(action=action,database=self.database,project=self.project,environment=self.environment,**values)
        content=script.read_bytes()+b'\nprobe('+json.dumps(request).encode()+b').then(x=>console.log(JSON.stringify(x))).catch(()=>process.exitCode=1);\n'
        return json.loads(command(self.base(self.values['IMAGE_DIGEST'])+['-'],self.d,content,timeout=30))

    def candidate(self,image,commit):
        if not isinstance(image,str) or not re.fullmatch(re.escape(self.config['deployment']['imageRepository'])+r'@sha256:[a-f0-9]{64}',image) or not hex_value(commit,40):raise ValueError('IMMUTABLE_IMAGE_REQUIRED')
        with tempfile.TemporaryDirectory(prefix='.candidate-',dir=self.d.STATE/self.project) as temp:
            root=Path(temp);env=dict(self.d.ENV,DOCKER_CONFIG=str(root/'docker'))
            command(['docker','pull',image],self.d,env=env,timeout=300)
            labels=json.loads(command(['docker','image','inspect','--format','{{json .Config.Labels}}',image],self.d))
            if labels.get('org.opencontainers.image.revision')!=commit or labels.get('org.opencontainers.image.source')!='https://github.com/'+image.split('@')[0].removeprefix('ghcr.io/'):
                raise ValueError('SOURCE_IDENTITY_MISMATCH')
            container=command(['docker','create','--entrypoint','/bin/false',image],self.d).decode().strip()
            if not re.fullmatch('[a-f0-9]{64}',container):raise ValueError('INVALID_CONTAINER_ID')
            try:
                for name in ('migration-manifest.json','migration-runner.cjs'):
                    command(['docker','cp',container+':/app/'+name,str(root/name)],self.d)
                    path=root/name
                    if path.is_symlink() or not path.is_file() or path.stat().st_size>64*1024*1024:raise ValueError('INVALID_MIGRATION_PACKAGE')
                manifest=catalog(json.loads((root/'migration-manifest.json').read_text()),self.project)
                from recovery import file_hash
                if file_hash(root/'migration-runner.cjs')!=manifest['runnerSha256']:raise ValueError('RUNNER_DIGEST_MISMATCH')
                return manifest
            finally:command(['docker','rm','-f','-v',container],self.d)


def evidence(store,plan):
    key=digest(plan);path=store.path(key,'.data.json')
    if not path.exists():return None
    value=json.loads(path.read_text())
    required={'version','planId','database','status','phase','writeIntent','backup','writers','writersRestored','health','verification','applied'}
    if not required<=value.keys() or type(value['version']) is not int or value['version']!=1 or value['status'] not in ('running','completed','failed','unknown') or value['phase'] not in ('backup','migrate','verify','health') or any(type(value[key]) is not bool for key in ('writeIntent','writersRestored','health')):raise ValueError('INVALID_DATA_EVIDENCE')
    if not isinstance(value['writers'],list) or len(set(value['writers']))!=len(value['writers']) or any(name not in ('app','worker','ai-worker') for name in value['writers']):raise ValueError('INVALID_DATA_EVIDENCE')
    expected=plan['migrationRequest']['pending']
    for field in ('applied','verification'):
        if not isinstance(value[field],list) or any(row not in expected for row in value[field]) or len({row['id'] for row in value[field]})!=len(value[field]):raise ValueError('INVALID_DATA_EVIDENCE')
    backup=value['backup']
    if backup is not None and (not isinstance(backup,dict) or backup.get('database')!=value['database'] or type(backup.get('verified')) is not bool or any(not hex_value(backup.get(key),64) for key in ('backupId','sha256'))):raise ValueError('INVALID_DATA_EVIDENCE')
    if value.get('planId')!=key or value.get('database')!=plan['migrationRequest']['database']:raise ValueError('INVALID_DATA_EVIDENCE')
    return value


def completed(plan,data):
    expected=plan['migrationRequest']['pending']
    return bool(data and data.get('status')=='completed' and data.get('backup',{}).get('verified') is True and
        data.get('writersRestored') is True and data.get('health') is True and data.get('runnerGone') is True and data.get('verification')==expected and data.get('applied')==expected)


def resolution(store,plan,data):
    path=store.path(digest(plan),'.resolution.json')
    if not path.exists():return None
    secure_record(path)
    value=json.loads(path.read_text());record=dict(value);hashed=record.pop('recordDigest',None)
    if hashed!=digest(record) or value.get('planId')!=digest(plan) or value.get('journalDigest')!=digest(store.status(digest(plan))) or value.get('dataDigest')!=digest(data) or value.get('project')!=plan['project'] or value.get('environment')!=plan['environment'] or value.get('database')!=plan['migrationRequest']['database'] or identity(value.get('inspection'))!=value.get('stateHash'):
        raise ValueError('INVALID_RESOLUTION')
    if not isinstance(value.get('operator'),str) or not value['operator'].strip() or not isinstance(value.get('reason'),str) or not value['reason'].strip():raise ValueError('INVALID_RESOLUTION')
    validate_resolution(plan,data,value['inspection'],value['disposition'])
    return value


def validate_resolution(plan,data,inspection,disposition):
    expected=plan['migrationRequest']['pending'];recorded=inspection['recorded'];verified=inspection['verification']
    if disposition not in ('safe-to-retry','verified-complete') or not inspection['predecessorGone'] or not inspection['writersRestored'] or not inspection['health'] or not inspection['leaseAcquired']:
        raise ValueError('UNSAFE_RESOLUTION')
    if any(row not in expected for row in recorded) or verified!=recorded or [row.get('id') for row in inspection.get('verifierResults',[])]!=[row['id'] for row in recorded]:raise ValueError('VERIFICATION_REQUIRED')
    if disposition=='verified-complete':
        if recorded!=expected or not inspection['backupVerified']:raise ValueError('VERIFICATION_REQUIRED')
    elif data.get('writeIntent') and recorded==expected:
        raise ValueError('VERIFIED_COMPLETION_REQUIRED')


def activation(store,manifest,ledger,environment,database,exclude=None):
    result=review(manifest,ledger);covered=set();written=set();resolved=[]
    try:
        for path in store.root.glob('*.plan.json'):
            key=path.name.removesuffix('.plan.json')
            if key==exclude:continue
            plan=store.read(key)
            if plan.get('classification')!='data-migration' or plan['environment']!=environment or plan['migrationRequest']['database']!=database:continue
            data=evidence(store,plan);journal=store.status(key)
            if data is None:
                if journal['status']!='prepared':raise ValueError('MISSING_DATA_EVIDENCE')
                continue
            if data.get('writeIntent'):written.update(row['id'] for row in plan['migrationRequest']['pending'])
            if successful_evidence(store,plan,data):covered.update((row['id'],row['checksum']) for row in data['verification']);continue
            settled=resolution(store,plan,data)
            if settled:
                covered.update((row['id'],row['checksum']) for row in settled['inspection']['verification']);resolved.append({'planId':key,'disposition':settled['disposition'],'observedAt':settled['observedAt']});continue
            if not (data.get('status')=='failed' and not data.get('writeIntent') and data.get('writersRestored') and data.get('health')):
                raise ValueError('UNRESOLVED_DATA_OPERATION')
        required_recorded={(m['id'],m['checksum']) for m in manifest['migrations'] if m['releasePhase']=='before-release' and m['id'] in result['applied'] and m['id'] in written}
        if required_recorded-covered:raise ValueError('MISSING_VERIFICATION')
    except (ValueError,KeyError,TypeError,OSError):
        result.update(activationDecision='blocked-recovery',nextAction='Inspect the original host journal and use the root-only recovery acknowledgment after authorized recovery.')
    result['resolutions']=resolved
    return result


def public_page(report,offset=0):
    # Full identity/approval batches are never silently truncated.
    if type(offset) is not int or offset<0:raise ValueError('INVALID_PAGE')
    result={k:v for k,v in report.items() if k not in ('ledger','pending','applied','disabled','changed','unknown','bespoke','required')}
    rows=report['ledger'];result['ledger']=rows[offset:offset+100]
    result['ledgerPaging']={'offset':offset,'total':len(rows),'nextOffset':offset+100 if offset+100<len(rows) else None}
    for key in ('pending','applied','disabled','changed','unknown','bespoke','required'):
        result[key]=report[key][offset:offset+100]
    result['detailPaging']={'offset':offset,'total':max(len(report[k]) for k in ('pending','applied','disabled','changed','unknown','bespoke','required'))}
    result['detailPaging']['nextOffset']=offset+100 if offset+100<result['detailPaging']['total'] else None
    if len(json.dumps(result).encode())>65536:raise ValueError('OWNER_ACTION_REQUIRED')
    return result

class DataExecutor:
    """Fixed approved backup/migrate/verify checkpoints; never automatically resumed."""
    def __init__(self,d,store,fd,plan):
        self.d,self.store,self.fd,self.plan=d,store,fd,plan
        self.key=digest(plan);self.host=Host(d,plan['project'],plan['environment'])
        self.hard_deadline=time.monotonic()+3600;self.deadline=self.hard_deadline-120;self.phase_deadline=self.deadline
        self.started=False
        self.process=None;self.buffer=b'';self.directory=None;self.session=None
        self.name=plan['project']+'-data-'+self.key
        self.data=dict(version=1,planId=self.key,database=plan['migrationRequest']['database'],status='running',phase='backup',writeIntent=False,backup=None,writers=[],writersRestored=False,health=False,verification=[],applied=[])
        self.handlers={sig:signal.signal(sig,self.interrupted) for sig in (signal.SIGTERM,signal.SIGINT)}

    def interrupted(self,*_):raise InterruptedError('DATA_OPERATION_INTERRUPTED')
    def save(self):
        self.data['observedAt']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        atomic(self.store.path(self.key,'.data.json'),self.data)
    def phase(self,name):
        import recovery
        self.data['phase']=name;self.phase_deadline=min(self.deadline,time.monotonic()+1800)
        recovery.DEADLINE=self.phase_deadline;self.save()
    def remaining(self):
        value=min(self.deadline,self.phase_deadline)-time.monotonic()
        if value<=0:raise TimeoutError('DATA_OPERATION_TIMEOUT')
        return value
    def send(self,value):
        raw=json.dumps(value).encode()+b'\n'
        if len(raw)>65536:raise ValueError('OWNER_ACTION_REQUIRED')
        self.process.stdin.write(raw);self.process.stdin.flush()
    def receive(self):
        while b'\n' not in self.buffer:
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout,selectors.EVENT_READ)
                if not selector.select(self.remaining()):raise TimeoutError('DATA_OPERATION_TIMEOUT')
            chunk=os.read(self.process.stdout.fileno(),65537)
            if not chunk:raise ValueError('RUNNER_OUTCOME_UNKNOWN')
            self.buffer+=chunk
            if len(self.buffer)>MAX_REPORT:raise ValueError('RUNNER_OUTPUT_INVALID')
        line,self.buffer=self.buffer.split(b'\n',1)
        return json.loads(line)
    def start(self,verify=False):
        args=self.host.base(self.plan['image'])
        args[2:2]=['--name',self.name]
        self.process=subprocess.Popen(args+['/app/migration-runner.cjs','--verify' if verify else '--protected'],env=self.d.ENV,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
        if hasattr(self,'data'):
            self.data.update(runnerPid=self.process.pid,runnerStart=process_start(self.process.pid));self.save()
        request=self.plan['migrationRequest']
        self.send({'version':1,'planId':self.key,'migrationRequest':{key:request[key] for key in ('database','manifestDigest','ledgerDigest','pending')}})

    def backup(self,plan):
        self.started=True
        from recovery import BackupSession,run
        manifest=self.host.candidate(plan['image'],plan['sourceCommit'])
        report=activation(self.store,manifest,self.host.probe('ledger'),plan['environment'],self.host.database,exclude=self.key)
        serving=self.host.serving()
        if not serving['imageMatches'] or not serving['ready']:raise ValueError('HOST_STATE_CHANGED')
        if report['activationDecision'] in ('blocked-recovery','owner-action-required') or identity(manifest)!=plan['migrationRequest']['manifestDigest'] or report['ledgerDigest']!=plan['migrationRequest']['ledgerDigest'] or [{'id':m['id'],'checksum':m['checksum']} for m in report['pending']]!=plan['migrationRequest']['pending']:
            raise ValueError('HOST_STATE_CHANGED')
        self.directory=tempfile.TemporaryDirectory(prefix='.data-operation-',dir=self.d.STATE/plan['project'])
        self.session=BackupSession(plan,self.d,self.directory.name)
        self.phase('backup');self.start()
        if self.receive()!={'type':'ready','planId':self.key}:raise ValueError('RUNNER_NOT_READY')
        self.data['writers']=self.session.writers();self.save()
        if self.data['writers']:run(self.session.compose+['stop',*self.data['writers']])
        self.data['backup']=self.session.backup(self.host.database);self.save()

    def migrate(self,plan):
        self.phase('migrate')
        # This durable intent precedes the only message that permits data writes.
        self.data['writeIntent']=True;self.save()
        self.send({'type':'backup-verified','planId':self.key,'backupId':self.data['backup']['backupId']})
        if self.receive()!={'type':'migrate'}:raise ValueError('RUNNER_OUTCOME_UNKNOWN')
        if self.receive()!={'type':'verify'}:raise ValueError('RUNNER_OUTCOME_UNKNOWN')
        self.phase('verify')
        result=self.receive()
        expected=plan['migrationRequest']['pending']
        if result.get('type')!='completed' or result.get('applied')!=[m['id'] for m in expected] or [m.get('id') for m in result.get('verification',[])]!=[m['id'] for m in expected]:raise ValueError('VERIFICATION_REQUIRED')
        self.process.stdin.close();self.process.wait(timeout=self.remaining())
        if self.process.returncode:raise ValueError('RUNNER_OUTCOME_UNKNOWN')
        ledger=self.host.probe('ledger');recorded={r['id']:r for r in ledger}
        if any(recorded.get(m['id'],{}).get('checksum')!=m['checksum'] for m in expected):raise ValueError('VERIFICATION_REQUIRED')
        self.data.update(applied=expected,verification=expected,warnings=[w for row in result['verification'] for w in row['warnings']]);self.save()

    def verify(self,plan):
        self.phase('health')
        self.session.resume_writers(self.data['writers'])
        self.data['writersRestored']=self.session.writers()==self.data['writers'];self.save()
        self.data['health']=self.d.execute_with_lock(dict(version=2,project=plan['project'],environment=plan['environment'],action='check',configurationHash=plan['configurationHash']),self.fd,min(1200,self.remaining()))==0
        if not self.data['writersRestored'] or not self.data['health']:raise ValueError('READBACK_REQUIRED')
        self.data['status']='completed';self.save()

    def report(self):
        report=terminal_report(self.plan,self.data)
        atomic(self.store.path(self.key,'.report.json'),report)
        try:self.host.probe('report',report=report)
        except Exception:pass  # A missing copy never overrides complete host evidence.

    def close(self):
        if not self.started:
            for sig,handler in self.handlers.items():signal.signal(sig,handler)
            return
        import recovery
        clean=True
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    try:os.killpg(self.process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                self.process.wait()
                try:command(['docker','rm','-f',self.name],self.d,timeout=30)
                except Exception:
                    try:clean=not bool(command(['docker','ps','-aq','--filter','name=^/'+self.name+'$'],self.d,timeout=30).strip())
                    except Exception:clean=False
                self.process.stdout.close()
                if not self.process.stdin.closed:self.process.stdin.close()
            self.data['runnerGone']=clean
            if self.data['status']!='completed':
                recovery.DEADLINE=time.monotonic()+120
                if not self.data['writeIntent'] and clean and not self.session:
                    self.data['writersRestored']=True
                    try:self.data['health']=self.d.execute_with_lock(dict(version=2,project=self.plan['project'],environment=self.plan['environment'],action='check',configurationHash=self.plan['configurationHash']),self.fd,max(0.01,min(120,self.hard_deadline-time.monotonic())))==0
                    except Exception:pass
                if not self.data['writeIntent'] and clean and self.session:
                    try:
                        self.session.resume_writers(self.data['writers'])
                        self.data['writersRestored']=self.session.writers()==self.data['writers']
                        self.data['health']=self.d.execute_with_lock(dict(version=2,project=self.plan['project'],environment=self.plan['environment'],action='check',configurationHash=self.plan['configurationHash']),self.fd,max(0.01,min(120,self.hard_deadline-time.monotonic())))==0
                    except Exception:pass
                self.data['status']='failed' if not self.data['writeIntent'] and clean and self.data['writersRestored'] and self.data['health'] else 'unknown'
                self.save()
            if not clean:
                self.data.update(status='unknown',health=False);self.save()
            self.save();self.report()
        finally:
            recovery.DEADLINE=None
            if self.directory:self.directory.cleanup()
            for sig,handler in self.handlers.items():signal.signal(sig,handler)
        if self.data['status']=='unknown':raise ValueError('READBACK_REQUIRED')


def terminal_report(plan,data):
    return dict(version=1,operationId=digest(plan),planDigest=digest(plan),project=plan['project'],environment=plan['environment'],database=plan['migrationRequest']['database'],sourceCommit=plan['sourceCommit'],image=plan['image'],configurationHash=plan['configurationHash'],manifestDigest=plan['migrationRequest']['manifestDigest'],ledgerDigest=plan['migrationRequest']['ledgerDigest'],
        observedAt=data['observedAt'],state='unknown' if data['status']=='running' else data['status'],phase=data['phase'],deploymentOutcome='not-attempted',migrationOutcome='pending' if not data['writeIntent'] else 'completed' if data['status']=='completed' else 'failed' if data['status']=='failed' else 'unknown',
        backup=data['backup'],pending=plan['migrationRequest']['pending'],applied=data['applied'],verification=data['verification'],writersRestored=data['writersRestored'],health=data['health'],warnings=data.get('warnings',[]),resolution=None)


def route(d,store,request):
    from operation_engine import state
    project=request['project'];environment=request['environment']
    if request.get('requiredCapabilities')!=[CAPABILITY]:raise ValueError('UNSUPPORTED_CAPABILITY')
    allowed={'version','project','environment','action','requiredCapabilities','configurationHash','image','commit'}
    action=request['action']
    if action=='migrate':allowed.add('requestId')
    elif action=='migrations' and 'offset' in request:allowed.add('offset')
    if set(request)!=allowed:raise ValueError('INVALID_REQUEST')
    if action=='migrate':
        request_id=request['requestId']
        try:
            if str(uuid.UUID(request_id))!=request_id:raise ValueError()
        except (ValueError,TypeError,AttributeError):raise ValueError('INVALID_REQUEST_ID') from None
        path=store.root/('request-'+request_id+'.json')
        if path.exists():
            previous=json.loads(path.read_text())
            if previous['request']!=request:raise ValueError('REQUEST_ID_REUSED')
            store.save(previous['envelope'])
            return dict(version=2,planId=previous['envelope']['digest'],**previous['envelope'],**previous.get('report',{}))
    host=Host(d,project,environment)
    if request['configurationHash']!=host.observed['configurationHash']:raise ValueError('HOST_STATE_CHANGED')
    image=request['image'] or host.values['IMAGE_DIGEST'];commit=request['commit'] or host.values['RELEASE_COMMIT']
    if action=='migrate' and (not request['image'] or not request['commit']):raise ValueError('IMMUTABLE_IMAGE_REQUIRED')
    try:manifest=host.candidate(image,commit);ledger=host.probe('ledger')
    except (ValueError,OSError,KeyError,TypeError):
        return dict(version=1,project=project,environment=environment,database=host.database,sourceCommit=commit,image=image,deploymentOutcome='not-attempted',migrationOutcome='unknown',activationDecision='owner-action-required',nextAction='Verify the candidate package/source labels and the approved image Node/MongoDB probe prerequisite with Infrastructure.')
    result=activation(store,manifest,ledger,environment,host.database)
    serving=host.serving()
    if result['activationDecision']!='blocked-recovery' and (not serving['imageMatches'] or (not serving['ready'] and (result['required'] or action=='migrate'))):
        result.update(activationDecision='owner-action-required',nextAction='Reconcile the observed serving image/revision and readiness before preparing data work.')
    result['serving']=serving
    result.update(environment=environment,database=host.database,sourceCommit=commit,image=image,manifestDigest=identity(manifest),deploymentOutcome='not-attempted',migrationOutcome='pending' if result['pending'] else 'not-required')
    if action=='migrations':return public_page(result,request.get('offset',0))
    if result['activationDecision'] in ('blocked-recovery','owner-action-required'):return public_page(result)
    if not result['pending']:return public_page(result)
    candidate=dict(project=project,environment=environment,sourceCommit=commit,image=image,bundleChecksum=host.observed['installedRevision'],configurationHash=host.observed['configurationHash'],classification='data-migration',changedSettings=[],credentialReferences=['RECOVERY_CONFIGURATION'],requestId=request_id,
        migrationRequest=dict(database=host.database,manifestDigest=identity(manifest),ledgerDigest=result['ledgerDigest'],pending=[{'id':m['id'],'checksum':m['checksum']} for m in result['pending']],backupPolicy={'mode':'create','verification':'archive'}))
    envelope=prepare(candidate,host.approval_observed())
    if len(json.dumps(envelope).encode())>60000:raise ValueError('OWNER_ACTION_REQUIRED')
    metadata={name:result[name] for name in ('activationDecision','nextAction','deploymentOutcome','migrationOutcome')}
    atomic(path,{'request':request,'envelope':envelope,'report':metadata});key=store.save(envelope)
    return dict(version=2,planId=key,**envelope,**metadata)


def secure_record(path):
    import stat
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode & 0o077:raise ValueError('UNTRUSTED_RESOLUTION')


def process_start(pid):
    try:return Path('/proc/'+str(int(pid))+'/stat').read_text().rsplit(')',1)[1].split()[19]
    except FileNotFoundError:
        if not Path('/proc/self/stat').is_file():raise ValueError('PROCESS_EVIDENCE_UNAVAILABLE')
        return None
    except (OSError,ValueError,IndexError):raise ValueError('PROCESS_EVIDENCE_UNAVAILABLE') from None


def quiet_database(store,environment,database):
    for path in store.root.glob('*.plan.json'):
        plan=store.read(path.name.removesuffix('.plan.json'))
        if plan.get('classification')!='data-migration' or plan['environment']!=environment or plan['migrationRequest']['database']!=database:continue
        saved=evidence(store,plan)
        if saved is None:
            if store.status(digest(plan))['status']!='prepared':raise ValueError('READBACK_REQUIRED')
        elif not successful_evidence(store,plan,saved) and not resolution(store,plan,saved) and not (saved.get('status')=='failed' and not saved.get('writeIntent') and saved.get('writersRestored') and saved.get('health')):raise ValueError('READBACK_REQUIRED')


def successful_evidence(store,plan,data):
    key=digest(plan);journal=store.status(key)
    if not store.path(key,'.journal.json').exists() or journal.get('planId')!=key or journal.get('status') not in ('completed','unknown','failed') or journal.get('completed') not in ([],['backup'],['backup','migrate'],['backup','migrate','verify']):raise ValueError('INVALID_DATA_JOURNAL')
    safe=journal.get('status')=='completed' and journal.get('active') is None and journal['completed']==plan['operations'] or journal.get('status')=='unknown' and journal.get('active')=='verify' and journal['completed']==['backup','migrate']
    return completed(plan,data) and safe
