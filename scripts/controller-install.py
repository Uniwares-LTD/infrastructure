"""One-time reviewed controller installation and checksum-bound replacement."""
import argparse
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile

ROOT=Path('/opt/uniwares-infrastructure/controllers')
DISPATCHER=Path('/usr/local/sbin/uniwares-deploy')
TRUST=Path('/etc/uniwares-infrastructure/approval-trust.json')


def validate_trust(trust):
    required={'repositoryId','ownerId','ref','executorRef','executorSha','adminIds'}
    if set(trust)!=required or trust['ref']!='refs/heads/main':raise ValueError('INVALID_TRUST')
    if not all(re.fullmatch('[0-9]+',trust[name]) for name in ('repositoryId','ownerId')):raise ValueError('INVALID_TRUST')
    if not re.fullmatch('[a-f0-9]{40}',trust['executorSha']) or not trust['executorRef'].endswith('@'+trust['executorSha']):raise ValueError('IMMUTABLE_EXECUTOR_REQUIRED')
    if not trust['adminIds'] or any(not re.fullmatch('[0-9]+',identity) for identity in trust['adminIds']):raise ValueError('ENROLLED_ADMINS_REQUIRED')


def extract(archive,checksum,destination):
    raw=Path(archive).read_bytes()
    if len(raw)>32*1024*1024 or hashlib.sha256(raw).hexdigest()!=checksum:raise ValueError('CONTROLLER_CHECKSUM_MISMATCH')
    import io
    with tarfile.open(fileobj=io.BytesIO(raw)) as bundle:
        seen=set();total=0
        for item in bundle:
            path=PurePosixPath(item.name)
            if not path.parts or path.is_absolute() or '..' in path.parts or path.parts[0] not in ('scripts','requirements-controller.txt','config') or any(part.startswith('.') for part in path.parts) or item.name in seen or not (item.isfile() or item.isdir()):raise ValueError('UNSAFE_CONTROLLER_ARCHIVE')
            total+=item.size
            if total>64*1024*1024:raise ValueError('CONTROLLER_TOO_LARGE')
            seen.add(item.name);target=destination.joinpath(*path.parts)
            if item.isdir():target.mkdir(parents=True,exist_ok=True,mode=0o700)
            else:
                target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                with target.open('xb') as out:shutil.copyfileobj(bundle.extractfile(item),out)
                target.chmod(0o600)
    if not (destination/'scripts/deploy-dispatch.py').is_file():raise ValueError('MISSING_DISPATCHER')


def install(archive,checksum,expected,trust=None):
    import fcntl
    ROOT.mkdir(parents=True,mode=0o700,exist_ok=True)
    for path in [ROOT, *ROOT.parents, DISPATCHER]:
        info=path.lstat()
        import stat
        if stat.S_ISLNK(info.st_mode) or info.st_uid!=0 or info.st_mode & 0o022:
            raise ValueError('UNTRUSTED_CONTROLLER_PATH')
    fd=os.open(ROOT/'operation.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return install_locked(archive,checksum,expected,trust)
    finally:os.close(fd)


def install_locked(archive,checksum,expected,trust=None):
    from operation_store import atomic
    if hashlib.sha256(DISPATCHER.read_bytes()).hexdigest()!=expected:raise ValueError('CONTROLLER_CHANGED')
    ROOT.mkdir(parents=True,mode=0o700,exist_ok=True)
    destination=ROOT/checksum
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix='.controller-',dir=ROOT) as temp:
            complete=Path(temp)/'complete';complete.mkdir(mode=0o700)
            extract(archive,checksum,complete)
            complete.rename(destination)
    if not (destination/'dependencies-ready').exists():
        subprocess.run(['/usr/bin/python3','-m','venv',str(destination/'venv')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run([str(destination/'venv/bin/python'),'-m','pip','install','--disable-pip-version-check','-r',str(destination/'requirements-controller.txt')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=300)
    subprocess.run([str(destination/'venv/bin/python'),'-I','-c','import jwt,cryptography'],check=True)
    atomic(destination/'dependencies-ready',{'checksum':checksum})
    if hashlib.sha256(DISPATCHER.read_bytes()).hexdigest()!=expected:raise ValueError('CONTROLLER_CHANGED')
    if trust is not None:
        validate_trust(trust);TRUST.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
        if TRUST.exists() and json.loads(TRUST.read_text())!=trust:raise ValueError('TRUST_CHANGE_REQUIRES_SEPARATE_REVIEW')
        atomic(TRUST,trust)
    previous=DISPATCHER.with_name(DISPATCHER.name+'.previous-'+expected)
    if not previous.exists():shutil.copyfile(DISPATCHER,previous);previous.chmod(0o700)
    wrapper=('#!'+str(destination/'venv/bin/python')+' -I\nimport runpy\nrunpy.run_path('+repr(str(destination/'scripts/deploy-dispatch.py'))+',run_name="__main__")\n').encode()
    fd,name=tempfile.mkstemp(prefix='.controller-',dir=DISPATCHER.parent)
    try:
        with os.fdopen(fd,'wb') as out:out.write(wrapper);out.flush();os.fsync(out.fileno());os.fchmod(out.fileno(),0o755)
        os.replace(name,DISPATCHER)
        directory=os.open(DISPATCHER.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(name):os.unlink(name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--expected-dispatcher-sha256',required=True);parser.add_argument('--trust',type=Path,required=True)
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if os.geteuid()!=0 or any(not re.fullmatch('[a-f0-9]{64}',value) for value in (args.sha256,args.expected_dispatcher_sha256)):raise ValueError('ROOT_AND_CHECKSUMS_REQUIRED')
    trust=json.loads(args.trust.read_text());validate_trust(trust)
    if hashlib.sha256(DISPATCHER.read_bytes()).hexdigest()!=args.expected_dispatcher_sha256:raise ValueError('CONTROLLER_CHANGED')
    with tempfile.TemporaryDirectory() as temp:extract(args.bundle,args.sha256,Path(temp))
    print('Controller bundle and explicit trust preview validated; existing account/key/sudo rules remain unchanged')
    if args.apply:install(args.bundle,args.sha256,args.expected_dispatcher_sha256,trust)

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    try:main()
    except Exception:raise SystemExit('Controller installation stopped; inspect retained predecessor and expected checksums. Details suppressed.') from None
