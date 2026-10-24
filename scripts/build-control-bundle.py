"""Build a credential-free bundle from a reviewed Git revision, not the working tree."""
import argparse
import hashlib
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('checkout', type=Path)
parser.add_argument('revision')
parser.add_argument('output', type=Path)
args = parser.parse_args()
revision = subprocess.check_output(['git', '-C', str(args.checkout), 'rev-parse', '--verify', args.revision + '^{commit}'], text=True).strip()
if args.output.exists():
    raise SystemExit('Output already exists; do not overwrite reviewed bundles')
subprocess.run(['git', '-C', str(args.checkout), 'archive', '--format=tar', '--output=' + str(args.output.resolve()), revision,
                'package.json', 'package-lock.json', 'project.config.json', 'tsconfig.json', 'src', 'scripts', 'deploy', 'messages'], check=True)
print('source=' + revision)
print('sha256=' + hashlib.sha256(args.output.read_bytes()).hexdigest())
