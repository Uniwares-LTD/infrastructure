"""Version-2 plan routing. Called only by the installed trusted dispatcher."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from operation_plan import prepare, verify_token, hex_value, digest, CAPABILITIES
from operation_store import PlanStore, atomic, RetryableOperationFailure

TRUST=Path('/etc/uniwares-infrastructure/approval-trust.json')
MAX_BUNDLE=32*1024*1024
RUNTIME=Path('/etc')
RELEASES=Path('/opt')


def local_module(name):
    path=Path(__file__).with_name(name+'.py')
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def state(d,project,target):
    source,config,revision,hashed=d.installed_state(dict(version=2,project=project,environment=target,action='check',configurationHash='0'*64))
    observed=dict(installedRevision=revision,configurationHash=hashed)
    environment='production' if target=='prod' else target
    current=RELEASES/project/environment/'current/compose.env'
    if current.exists():
        d.trusted(current.resolve())
        values=dict(line.split('=',1) for line in current.read_text().splitlines() if '=' in line)
        observed['releaseIdentity']=digest({name:values.get(name) for name in ('RELEASE_COMMIT','IMAGE_DIGEST')})
    return source,config,observed


def names(before,after,prefix=''):
    if isinstance(before,dict) and isinstance(after,dict):
        result=[]
        for key in sorted(before.keys()|after.keys()):
            name=prefix+'.'+key if prefix else key
            if key not in before or key not in after:result.append(name)
            else:result.extend(names(before[key],after[key],name))
        return result
    return [] if before==after else [prefix]


def route(d,request):
    action=request.get('action')
    project=request.get('project');target=request.get('environment')
    # Validate common identity using the legacy validator, with no caller command/path.
    d.validate_request(dict(version=2,project=project,environment=target,action='check',configurationHash='0'*64))
    allowed={'version','project','environment','action'}
    extras={'capabilities':set(),'maintenance':set(),'status':{'planId'},'plan':{'candidate','bundle'},'apply':{'planId','token'},'backup':{'backupId','destination'},'restore':{'backupId','destination'}}
    if action not in extras or set(request)!=allowed|extras[action]:raise ValueError('INVALID_REQUEST')
    if action=='capabilities':return {'version':2,'capabilities':CAPABILITIES}
    with d.operation_lock(project) as fd:
        if action == 'maintenance':
            from image_maintenance import Maintenance, policy, lock, STATE
            engine = Maintenance(policy())
            with lock(STATE / 'image-maintenance.lock', 'UNIWARES_IMAGE_LOCK_FD'):
                result = engine.preview(project)
                previous = engine.apps / project / 'image-maintenance-status.json'
                from image_maintenance import read
                return {'version': 2, 'disk': result['disk'], 'snapshots': result['snapshots'],
                        'protected': result['protected'],
                        'lastMaintenance': read(previous) if previous.exists() else None}
        store=PlanStore(d.STATE/project/'operation-plans')
        if action=='status':
            result=store.status(request['planId'])
            recovery=store.path(request['planId'],'.recovery.json')
            if recovery.exists():result['recovery']=json.loads(recovery.read_text())
            return result
        if action in ('backup','restore'):
            return recovery_plan(d,store,request)
        if action=='plan':return stage(d,store,request)
        identity=request['planId']
        plan=store.read(identity)
        if plan['project']!=project or plan['environment']!=target:raise ValueError('PLAN_IDENTITY_MISMATCH')
        d.trusted(TRUST)
        trust=json.loads(TRUST.read_text())
        approval=verify_token(request['token'],trust,identity)
        source,current,observed=state(d,project,target)
        executor=Executor(d,store,fd,plan)
        return store.apply(identity,approval,observed,
                           {'configure':executor.configure,'deploy':executor.deploy,'check':executor.check,'backup':executor.recover,'restore':executor.recover,'controller':executor.controller},
                           {'configure':executor.configured,'deploy':executor.deployed,'check':executor.deployed,'controller':executor.controller_installed})


def stage(d,store,request):
    candidate=request['candidate']
    if not isinstance(candidate,dict) or candidate.get('project')!=request['project'] or candidate.get('environment')!=request['environment']:
        raise ValueError('PLAN_IDENTITY_MISMATCH')
    source,current,observed=state(d,request['project'],request['environment'])
    # Validate input shape before reading any caller-provided identity as a path.
    envelope=prepare(candidate,observed)
    if candidate['classification']=='controller':return stage_controller(d,store,request,observed)
    encoded=request['bundle']
    if not isinstance(encoded,str) or len(encoded)>MAX_BUNDLE*4//3+4:raise ValueError('BUNDLE_TOO_LARGE')
    raw=base64.b64decode(encoded,validate=True)
    if len(raw)>MAX_BUNDLE or hashlib.sha256(raw).hexdigest()!=candidate['bundleChecksum']:
        raise ValueError('BUNDLE_CHECKSUM_MISMATCH')
    bootstrap=local_module('bootstrap-deploy')
    with tempfile.TemporaryDirectory(prefix='.prepare-',dir=store.root) as temp:
        archive=Path(temp)/'bundle.tar';archive.write_bytes(raw)
        candidate_source=bootstrap.extract(archive,candidate['bundleChecksum'],Path(temp))
        if json.loads((candidate_source/'project.config.json').read_text())['slug']!=candidate['project']:
            raise ValueError('PROJECT_MISMATCH')
        d.require_lock_capability(candidate_source)
        target='production' if candidate['environment']=='prod' else 'staging'
        proposed=json.loads((candidate_source/f'deploy/environments/{target}.json').read_text())
        if digest(proposed)!=candidate['configurationHash']:raise ValueError('CONFIGURATION_MISMATCH')
        if candidate['image'].split('@')[0]!=proposed['deployment']['imageRepository']:
            raise ValueError('IMAGE_REPOSITORY_MISMATCH')
        metadata=json.loads((candidate_source/'deploy/bundle-source.json').read_text())
        if metadata.get('sourceCommit')!=candidate['sourceCommit'] or metadata.get('contractVersion')!=1:
            raise ValueError('SOURCE_IDENTITY_MISMATCH')
        changed=names(current,proposed)
        def controls(root):
            selected={}
            for directory in ['scripts/deploy','deploy']:
                for path in (root/directory).rglob('*'):
                    if path.is_file() and 'environments' not in path.parts and path.name!='bundle-source.json':
                        selected[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
            return selected
        if controls(source)!=controls(candidate_source):changed.append('control.bundle')
        expected_class='host-configuration' if changed else 'image-only'
        references=set()
        for field,reference in [('DIFY_ORCHESTRATORS_JSON','keyEnv'),('MCP_CLIENTS_JSON','tokenEnv')]:
            for item in json.loads(proposed['runtime'].get(field,'[]')):
                if item.get('enabled',True) and item.get(reference):references.add(item[reference])
        if proposed['runtime'].get('DIFY_MODE')=='live':references.update(['DIFY_MANAGEMENT_KEY','DIFY_CREDENTIAL_ENCRYPTION_KEY'])
        if proposed['runtime'].get('PERSONA_COMPLETION_MODE')=='live':references.add('PERSONA_COMPLETION_API_KEY')
        candidate=dict(candidate,changedSettings=changed,classification=expected_class,credentialReferences=sorted(references))
        envelope=prepare(candidate,observed)
        other='staging' if target=='production' else 'production'
        from deployment_contract import load as load_contract, project as project_config
        contract=load_contract(candidate_source/'deploy/contract.json')
        if project_config(json.loads((source/f'deploy/environments/{other}.json').read_text()),contract)!=json.loads((candidate_source/f'deploy/environments/{other}.json').read_text()):
            raise ValueError('OTHER_ENVIRONMENT_CHANGED')
        # Preview using only Infrastructure code. No candidate application code runs here.
        updater=local_module('update-app-config')
        runtime=RUNTIME/candidate['project']/target/'runtime.env'
        d.trusted(runtime)
        try:
            values=updater.runtime_values(runtime.read_text())
            if any(not values.get(name) for name in references):raise ValueError('MISSING_CREDENTIAL_REFERENCE')
            updater.merge(current,proposed,runtime.read_text(),{},target=target)
        except ValueError:
            raise ValueError('OWNER_ACTION_REQUIRED') from None
        identity=envelope['digest']
        destination=store.path(identity,'.bundle')
        if not destination.exists():candidate_source.rename(destination)
        store.save(envelope)
        return dict(version=2,planId=identity,**envelope)


class Executor:
    def __init__(self,d,store,fd,plan):
        self.d,self.store,self.fd,self.plan=d,store,fd,plan
        self.identity=digest(plan)
        self.target='production' if plan['environment']=='prod' else 'staging'

    def controller(self,plan):
        installer=local_module('controller-install')
        installer.install(self.store.path(self.identity,'.controller.tar'),plan['bundleChecksum'],plan['controllerExpectedChecksum'])

    def controller_installed(self,plan):
        installer=local_module('controller-install')
        return str(installer.ROOT/plan['bundleChecksum']) in installer.DISPATCHER.read_text()

    def recover(self,plan):
        local_module('recovery').execute(plan,self.d)

    def configured(self,plan):
        _,_,observed=state(self.d,plan['project'],plan['environment'])
        return observed['installedRevision']==plan['bundleChecksum'] and observed['configurationHash']==plan['configurationHash'] and observed.get('releaseIdentity')==plan['expected'].get('releaseIdentity')

    def configure(self,plan):
        d=self.d
        old,public,observed=state(d,plan['project'],plan['environment'])
        source=self.store.path(self.identity,'.bundle')
        updater=local_module('update-app-config')
        proposed=json.loads((source/f'deploy/environments/{self.target}.json').read_text())
        runtime=RUNTIME/plan['project']/self.target/'runtime.env'
        d.trusted(runtime)
        content=updater.merge(public,proposed,runtime.read_text(),{},target=self.target)
        destination=d.CONTROL/plan['project']/plan['bundleChecksum']
        if destination.exists():
            if local_module('bootstrap-deploy').tree_contents(destination)!=local_module('bootstrap-deploy').tree_contents(source):
                raise ValueError('BUNDLE_CHANGED')
        else:
            with tempfile.TemporaryDirectory(prefix='.install-',dir=destination.parent) as temp:
                complete=Path(temp)/'complete';shutil.copytree(source,complete);complete.rename(destination)
        # Immutable selected bundle is the reviewed code authorized by this exact plan.
        with tempfile.TemporaryDirectory(prefix='.runtime-',dir=self.store.root) as temp:
            candidate=Path(temp)/'runtime.env';candidate.write_text(content);candidate.chmod(0o600)
            result=subprocess.run(['/usr/bin/python3','-IB',str(destination/'scripts/deploy/config.py'),
                                   str(runtime.parents[1]),self.target,str(candidate)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
            if result.returncode:raise ValueError('RUNTIME_VALIDATION_FAILED')
        journal=d.STATE/plan['project']/'config-update-pending'
        if journal.exists():raise ValueError('READBACK_REQUIRED')
        updater.apply_change(journal,runtime,d.REGISTRY/(plan['project']+'.json'),content,plan['bundleChecksum'])
        return state(d,plan['project'],plan['environment'])[2]

    def request(self,action):
        request=dict(version=2,project=self.plan['project'],environment=self.plan['environment'],
                     action=action,configurationHash=self.plan['configurationHash'])
        if action=='deploy':request.update(image=self.plan['image'],commit=self.plan['sourceCommit'])
        return request

    def deploy(self,plan):
        if self.d.execute_with_lock(self.request('deploy'),self.fd):
            observed=state(self.d,plan['project'],plan['environment'])[2]
            # Known nonzero exit is retryable only after the prior selected image is
            # proven healthy. Timeout/interruption exceptions never enter this path.
            prior=plan['expected'].get('releaseIdentity')
            if prior and observed.get('releaseIdentity')==prior and self.d.execute_with_lock(self.request('check'),self.fd)==0:
                raise RetryableOperationFailure('DEPLOYMENT_FAILED_PREVIOUS_RELEASE_VERIFIED')
            raise ValueError('READBACK_REQUIRED')
        return state(self.d,plan['project'],plan['environment'])[2]

    def check(self,plan):
        if self.d.execute_with_lock(self.request('check'),self.fd):raise RetryableOperationFailure('READINESS_FAILED')
        return state(self.d,plan['project'],plan['environment'])[2]

    def deployed(self,plan):
        # A readiness check alone does not prove the exact intended release was selected.
        current=RELEASES/plan['project']/self.target/'current/compose.env'
        self.d.trusted(current.resolve())
        values=dict(line.split('=',1) for line in current.read_text().splitlines() if '=' in line)
        if values.get('RELEASE_COMMIT')!=plan['sourceCommit'] or values.get('IMAGE_DIGEST')!=plan['image']:
            return False
        return self.d.execute_with_lock(self.request('check'),self.fd)==0


def recovery_plan(d,store,request):
    source,config,observed=state(d,request['project'],request['environment'])
    target='production' if request['environment']=='prod' else 'staging'
    current=RELEASES/request['project']/target/'current/compose.env'
    d.trusted(current.resolve())
    values=dict(line.split('=',1) for line in current.read_text().splitlines() if '=' in line)
    destination=request['destination'] or config['runtime']['MONGODB_DATABASE']
    if request['action']=='restore' and not request['destination']:raise ValueError('EXPLICIT_RECOVERY_DESTINATION_REQUIRED')
    candidate=dict(project=request['project'],environment=request['environment'],sourceCommit=values['RELEASE_COMMIT'],
        image=values['IMAGE_DIGEST'],bundleChecksum=observed['installedRevision'],configurationHash=observed['configurationHash'],
        classification=request['action'],changedSettings=[],credentialReferences=['RECOVERY_CONFIGURATION'],
        recoveryRequest={'backupId':request['backupId'],'destination':destination})
    envelope=prepare(candidate,observed);identity=store.save(envelope)
    return dict(version=2,planId=identity,**envelope)


def stage_controller(d,store,request,observed):
    candidate=request['candidate']
    installer=local_module('controller-install')
    current=hashlib.sha256(installer.DISPATCHER.read_bytes()).hexdigest()
    if candidate['controllerExpectedChecksum']!=current:raise ValueError('CONTROLLER_CHANGED')
    encoded=request['bundle']
    if not isinstance(encoded,str) or len(encoded)>MAX_BUNDLE*4//3+4:raise ValueError('BUNDLE_TOO_LARGE')
    raw=base64.b64decode(encoded,validate=True)
    envelope=prepare(candidate,observed)
    with tempfile.TemporaryDirectory(prefix='.controller-plan-',dir=store.root) as temp:
        archive=Path(temp)/'bundle.tar';archive.write_bytes(raw)
        extracted=Path(temp)/'source';extracted.mkdir()
        installer.extract(archive,candidate['bundleChecksum'],extracted)
        metadata=json.loads((extracted/'config/controller-source.json').read_text())
        if metadata.get('sourceCommit')!=candidate['sourceCommit']:raise ValueError('SOURCE_IDENTITY_MISMATCH')
        destination=store.path(envelope['digest'],'.controller.tar')
        if not destination.exists():archive.rename(destination)
    identity=store.save(envelope)
    return dict(version=2,planId=identity,**envelope)
