"""Manual MongoDB/GridFS recovery. Runs only under an approved application lock."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

DEADLINE = None


RUNTIME=Path('/etc')
RELEASES=Path('/opt')


def run(args,env=None):
    import signal
    def interrupted(signum,frame):raise InterruptedError('RECOVERY_INTERRUPTED')
    previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGTERM,signal.SIGINT)}
    process=None
    try:
        with tempfile.TemporaryFile() as output:
            process=subprocess.Popen(args,env=env or {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','LC_ALL':'C'},stdout=output,stderr=subprocess.DEVNULL,start_new_session=True)
            status=process.wait(timeout=min(900, max(0.01, DEADLINE-time.monotonic())) if DEADLINE else 900)
            if status:raise ValueError('RECOVERY_OPERATION_FAILED')
            output.seek(0);result=output.read(1024*1024+1)
            if len(result)>1024*1024:raise ValueError('RECOVERY_OUTPUT_TOO_LARGE')
            return result
    except BaseException:
        if process is not None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()
        raise
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)


def file_hash(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


class BackupSession:
    """One configured database/archive identity; caller owns locks and writers."""
    def __init__(self,plan,d,directory):
        self.plan,self.d,self.directory=plan,d,Path(directory)
        project=plan['project'];target='production' if plan['environment']=='prod' else 'staging'
        self.target=target
        credentials=RUNTIME/project/target/'recovery.json';d.trusted(credentials)
        if credentials.stat().st_mode & 0o077:raise ValueError('RECOVERY_CREDENTIAL_PERMISSIONS')
        config=json.loads(credentials.read_text())
        required={'repository','passwordFile','accessKeyId','secretAccessKey','mongoUri','database'}
        if set(config)!=required or not config['repository'].startswith('s3:https://'):
            raise ValueError('RECOVERY_CONFIGURATION_REQUIRED')
        password=Path(config['passwordFile']);d.trusted(password)
        if password.stat().st_mode & 0o077:raise ValueError('RECOVERY_CREDENTIAL_PERMISSIONS')
        if not re.fullmatch(re.escape(project.replace('-','_'))+r'_[A-Za-z0-9_]+',config['database']):
            raise ValueError('RECOVERY_DATABASE_IDENTITY')
        source=d.CONTROL/project/plan['expected']['installedRevision']
        public=json.loads((source/f'deploy/environments/{target}.json').read_text())
        if config['database']!=public['runtime']['MONGODB_DATABASE']:raise ValueError('RECOVERY_DATABASE_IDENTITY')
        if plan.get('requestId'):
            # Different credentials are expected; a different cluster endpoint is not.
            runtime=RUNTIME/project/target/'runtime.env';d.trusted(runtime)
            values=dict(line.split('=',1) for line in runtime.read_text().splitlines() if '=' in line)
            from urllib.parse import urlsplit,parse_qs
            def destination(uri):
                parsed=urlsplit(uri);options=parse_qs(parsed.query)
                return (parsed.scheme,tuple(sorted(parsed.netloc.rsplit('@',1)[-1].lower().split(','))),tuple((key,tuple(options.get(key,[]))) for key in ('replicaSet','srvServiceName','loadBalanced','directConnection')))
            if destination(config['mongoUri'])!=destination(values.get('MONGODB_URI','')):raise ValueError('RECOVERY_DATABASE_IDENTITY')
        self.config=config
        self.env=dict(d.ENV,RESTIC_REPOSITORY=config['repository'],RESTIC_PASSWORD_FILE=str(password),
                 AWS_ACCESS_KEY_ID=config['accessKeyId'],AWS_SECRET_ACCESS_KEY=config['secretAccessKey'])
        current=RELEASES/project/target/'current';resolved=current.resolve();d.trusted(resolved)
        if not resolved.is_relative_to(RELEASES/project/target/'releases'):raise ValueError('UNTRUSTED_RELEASE')
        self.compose=['docker','compose','--project-name',project+'-'+target,'--env-file',str(resolved/'compose.env'),'-f',str(resolved/'compose.yml')]
        self.mongo=self.directory/'mongo.yml'
        self.mongo.write_text('uri: '+json.dumps(config['mongoUri'])+'\n');self.mongo.chmod(0o600)

    def writers(self):
        running=run(self.compose+['ps','--status','running','--services']).decode().split()
        return sorted(name for name in ('app','worker','ai-worker') if name in running)

    def retrieve(self,snapshot,database,expected_hash=None):
        if not re.fullmatch('[a-f0-9]{64}',snapshot or ''):raise ValueError('EXPLICIT_BACKUP_ID_REQUIRED')
        with tempfile.TemporaryDirectory(prefix='verify-',dir=self.directory) as temp:
            restored=Path(temp)
            run(['restic','restore',snapshot,'--target',str(restored)],self.env)
            manifests=list(restored.rglob('manifest.json'))
            if len(manifests)!=1:raise ValueError('BACKUP_MANIFEST_INVALID')
            manifest_path=manifests[0];archive=manifest_path.with_name('database.archive')
            if manifest_path.is_symlink() or archive.is_symlink() or not archive.is_file():raise ValueError('BACKUP_MANIFEST_INVALID')
            manifest=json.loads(manifest_path.read_text())
            actual=file_hash(archive)
            if (manifest.get('project')!=self.plan['project'] or manifest.get('environment')!=self.plan['environment'] or
                manifest.get('database')!=database or actual!=manifest.get('sha256') or (expected_hash and expected_hash!=actual)):
                raise ValueError('BACKUP_IDENTITY_MISMATCH')
            # Copy only the verified archive, never arbitrary restored files.
            import shutil
            destination=self.directory/'verified.archive';shutil.copyfile(archive,destination);destination.chmod(0o600)
            return destination,actual

    def backup(self,database):
        archive=self.directory/'database.archive';manifest=self.directory/'manifest.json'
        run(['mongodump','--config',str(self.mongo),'--db',database,'--archive='+str(archive),'--gzip'])
        hashed=file_hash(archive)
        manifest.write_text(json.dumps({'version':1,'project':self.plan['project'],'environment':self.plan['environment'],
            'database':database,'sha256':hashed}))
        lines=run(['restic','backup','--json','--tag',self.plan['project']+'-'+self.target,str(archive),str(manifest)],self.env).splitlines()
        summaries=[json.loads(line) for line in lines if json.loads(line).get('message_type')=='summary']
        if len(summaries)!=1 or not re.fullmatch('[a-f0-9]{64}',summaries[0].get('snapshot_id','')):raise ValueError('BACKUP_ID_UNVERIFIED')
        snapshot=summaries[0]['snapshot_id'];run(['restic','check'],self.env)
        self.retrieve(snapshot,database,hashed)
        return {'backupId':snapshot,'database':database,'sha256':hashed,'verified':True}


def execute(plan,d):
    from operation_store import atomic
    from operation_plan import digest
    project=plan['project']
    with tempfile.TemporaryDirectory(prefix='.recovery-',dir=d.STATE/project) as temp:
        session=BackupSession(plan,d,temp);config=session.config;recovery=plan['recoveryRequest'];destination=recovery['destination']
        if destination!=config['database'] and not re.fullmatch(re.escape(config['database'])+r'_rehearsal_[a-z0-9]+',destination):
            raise ValueError('EXPLICIT_RECOVERY_DESTINATION_REQUIRED')
        writers=session.writers();restore_started=False;restore_completed=False
        result_path=d.STATE/project/'operation-plans'/(digest(plan)+'.recovery.json')
        try:
            if writers:run(session.compose+['stop',*writers])
            if plan['classification']=='backup':result=session.backup(config['database'])
            else:
                snapshot=recovery['backupId'];prior=session.backup(destination)['backupId']
                archive,_=session.retrieve(snapshot,config['database'])
                atomic(result_path,{'backupId':snapshot,'destination':destination,'preRestoreBackupId':prior,'status':'restore-outcome-unknown','writersStopped':writers})
                restore_started=True
                run(['mongorestore','--config',str(session.mongo),'--archive='+str(archive),'--gzip','--drop',
                     '--nsFrom='+config['database']+'.*','--nsTo='+destination+'.*'])
                restore_completed=True
                result={'backupId':snapshot,'destination':destination,'preRestoreBackupId':prior}
            atomic(result_path,result)
        finally:
            if writers and (not restore_started or restore_completed):run(session.compose+['start',*writers])
