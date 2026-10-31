"""Package a reviewed Infrastructure commit; no candidate code is executed."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile


def build(checkout,revision,output):
    if not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('FULL_COMMIT_REQUIRED')
    output=Path(output);manifest=output.with_suffix(output.suffix+'.manifest.json')
    if output.exists() or manifest.exists():raise ValueError('OUTPUT_EXISTS')
    raw=subprocess.check_output(['git','-C',str(checkout),'archive','--format=tar',revision,'scripts','requirements-controller.txt'])
    content=io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw)) as source,tarfile.open(fileobj=content,mode='w') as target:
        for item in source:
            if not (item.isfile() or item.isdir()) or any(part.startswith('.') for part in Path(item.name).parts):raise ValueError('UNSAFE_CONTROLLER_MEMBER')
            target.addfile(item,source.extractfile(item) if item.isfile() else None)
        metadata=(json.dumps({'sourceCommit':revision})+'\n').encode()
        member=tarfile.TarInfo('config/controller-source.json');member.size=len(metadata);member.mode=0o600
        target.addfile(member,io.BytesIO(metadata))
    archive=content.getvalue()
    if len(archive)>32*1024*1024:raise ValueError('CONTROLLER_TOO_LARGE')
    result={'version':1,'sourceCommit':revision,'bundleChecksum':hashlib.sha256(archive).hexdigest(),'classification':'controller'}
    with output.open('xb') as stream:stream.write(archive)
    with manifest.open('x') as stream:json.dump(result,stream,indent=2)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout');parser.add_argument('revision');parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.checkout,args.revision,args.output)))
