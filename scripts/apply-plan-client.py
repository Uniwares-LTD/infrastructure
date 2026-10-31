"""Infrastructure Actions client: obtain plan-bound OIDC and send fixed apply JSON."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote
from urllib.request import Request,urlopen


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project');parser.add_argument('environment',choices=['staging','prod'])
    parser.add_argument('plan_id')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}',args.project) or not re.fullmatch('[a-f0-9]{64}',args.plan_id):raise ValueError('INVALID_IDENTITY')
    targets=json.loads((Path(__file__).resolve().parents[1]/'config/approval-targets.json').read_text())
    host=targets[args.project][args.environment]
    if not re.fullmatch('[A-Za-z0-9.-]+',host):raise ValueError('INVALID_HOST')
    url=os.environ['ACTIONS_ID_TOKEN_REQUEST_URL']+'&audience='+quote('uniwares:plan:'+args.plan_id,safe='')
    with urlopen(Request(url,headers={'Authorization':'Bearer '+os.environ['ACTIONS_ID_TOKEN_REQUEST_TOKEN']}),timeout=20) as response:
        token=json.load(response)['value']
    request=dict(version=2,action='apply',project=args.project,environment=args.environment,planId=args.plan_id,token=token)
    with tempfile.TemporaryDirectory(prefix='approved-operation-') as temp:
        root=Path(temp);key=root/'key';known=root/'known_hosts'
        key.write_text(os.environ['DEPLOY_SSH_PRIVATE_KEY']+'\n');key.chmod(0o600)
        # The exact host key comes from the reviewed Infrastructure secret, not ssh-keyscan.
        host_key=os.environ['DEPLOY_SSH_HOST_KEY'].strip()
        if host_key.startswith(host+' '):host_key=host_key[len(host)+1:]
        if '\n' in host_key or not re.fullmatch(r'(ssh-ed25519|ecdsa-sha2-nistp256|ssh-rsa) [A-Za-z0-9+/=]+(?: [^\r\n]+)?',host_key):
            raise ValueError('INVALID_PINNED_HOST_KEY')
        known.write_text(host+' '+host_key+'\n');known.chmod(0o600)
        with tempfile.TemporaryFile() as output:
            result=subprocess.run(['ssh','-i',str(key),'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
                '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),
                '-o','ConnectTimeout=10','uniwares-deploy-user@'+host,'operate'],
                input=json.dumps(request).encode(),stdout=output,stderr=subprocess.DEVNULL,timeout=1300)
            if result.returncode:raise ValueError('APPLY_FAILED_OR_UNKNOWN')
            output.seek(0);raw=output.read(65537)
        if len(raw)>65536:raise ValueError('INVALID_RESPONSE')
        status=json.loads(raw.splitlines()[-1])
        if status.get('planId')!=args.plan_id or status.get('status')!='completed':raise ValueError('OUTCOME_UNKNOWN')
        print('Approved plan completed: '+args.plan_id)

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Approved operation did not confirm completion; inspect plan status before retrying. Private details suppressed.') from None
