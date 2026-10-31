"""Manual MongoDB/GridFS recovery. Runs only under an approved application lock."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


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
            status=process.wait(timeout=900)
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


def execute(plan,d):
    project=plan['project'];target='production' if plan['environment']=='prod' else 'staging'
    credentials=RUNTIME/project/target/'recovery.json'
    d.trusted(credentials)
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
    recovery=plan['recoveryRequest'];destination=recovery['destination']
    if destination!=config['database'] and not re.fullmatch(re.escape(config['database'])+r'_rehearsal_[a-z0-9]+',destination):
        raise ValueError('EXPLICIT_RECOVERY_DESTINATION_REQUIRED')
    env=dict(d.ENV,RESTIC_REPOSITORY=config['repository'],RESTIC_PASSWORD_FILE=str(password),
             AWS_ACCESS_KEY_ID=config['accessKeyId'],AWS_SECRET_ACCESS_KEY=config['secretAccessKey'])
    current=RELEASES/project/target/'current'
    resolved=current.resolve();d.trusted(resolved)
    if not resolved.is_relative_to(RELEASES/project/target/'releases'):raise ValueError('UNTRUSTED_RELEASE')
    compose=['docker','compose','--project-name',project+'-'+target,'--env-file',str(resolved/'compose.env'),'-f',str(resolved/'compose.yml')]
    with tempfile.TemporaryDirectory(prefix='.recovery-',dir=d.STATE/project) as temp:
        directory=Path(temp)
        # MongoDB tools accept a protected config file; URI never appears in argv/logs.
        mongo=directory/'mongo.yml';mongo.write_text('uri: '+json.dumps(config['mongoUri'])+'\n');mongo.chmod(0o600)
        def backup(database):
            archive=directory/'database.archive';manifest=directory/'manifest.json'
            run(['mongodump','--config',str(mongo),'--db',database,'--archive='+str(archive),'--gzip'])
            manifest.write_text(json.dumps({'version':1,'project':project,'environment':plan['environment'],
                'database':database,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
            lines=run(['restic','backup','--json','--tag',project+'-'+target,str(archive),str(manifest)],env).splitlines()
            summaries=[json.loads(line) for line in lines if json.loads(line).get('message_type')=='summary']
            if len(summaries)!=1 or not re.fullmatch('[a-f0-9]{64}',summaries[0].get('snapshot_id','')):
                raise ValueError('BACKUP_ID_UNVERIFIED')
            run(['restic','check'],env)
            return summaries[0]['snapshot_id']
        running=run(compose+['ps','--status','running','--services']).decode().split()
        writers=[name for name in ('app','worker','ai-worker') if name in running]
        restore_started=False
        restore_completed=False
        from operation_store import atomic
        from operation_plan import digest
        result_path=d.STATE/project/'operation-plans'/(digest(plan)+'.recovery.json')
        try:
            if writers:run(compose+['stop',*writers])
            if plan['classification']=='backup':
                snapshot=backup(config['database'])
                result={'backupId':snapshot,'database':config['database']}
            else:
                snapshot=recovery['backupId']
                if not re.fullmatch('[a-f0-9]{64}',snapshot or ''):raise ValueError('EXPLICIT_BACKUP_ID_REQUIRED')
                # Preserve the actual destination before any destructive restore.
                prior=backup(destination)
                restored=directory/'restored';restored.mkdir()
                run(['restic','restore',snapshot,'--target',str(restored)],env)
                manifests=list(restored.rglob('manifest.json'))
                if len(manifests)!=1:raise ValueError('BACKUP_MANIFEST_INVALID')
                manifest=json.loads(manifests[0].read_text());archive=manifests[0].with_name('database.archive')
                if manifest.get('project')!=project or manifest.get('environment')!=plan['environment'] or manifest.get('database')!=config['database'] or hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest.get('sha256'):
                    raise ValueError('BACKUP_IDENTITY_MISMATCH')
                atomic(result_path,{'backupId':snapshot,'destination':destination,'preRestoreBackupId':prior,'status':'restore-outcome-unknown','writersStopped':writers})
                restore_started=True
                run(['mongorestore','--config',str(mongo),'--archive='+str(archive),'--gzip','--drop',
                     '--nsFrom='+config['database']+'.*','--nsTo='+destination+'.*'])
                restore_completed=True
                result={'backupId':snapshot,'destination':destination,'preRestoreBackupId':prior}
            atomic(result_path,result)
        finally:
            # A partially restored database must not receive application writes.
            # Preserve the journal/backup identity for explicit operator recovery.
            if writers and (not restore_started or restore_completed):run(compose+['start',*writers])
