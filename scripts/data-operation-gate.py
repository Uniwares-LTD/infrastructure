#!/usr/bin/python3 -IB
"""Validate an exact candidate immediately before activation under an inherited lock."""
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from data_operations import Host,activation,public_page
from operation_store import PlanStore

def main():
    if os.geteuid()!=0 or len(sys.argv)!=5:raise ValueError('ROOT_AND_IDENTITY_REQUIRED')
    project,environment,image,commit=sys.argv[1:]
    environment='prod' if environment=='production' else environment
    if not re.fullmatch('[a-z][a-z0-9-]{2,39}',project) or environment not in ('staging','prod'):raise ValueError('INVALID_IDENTITY')
    path=Path(__file__).with_name('deploy-dispatch.py')
    spec=importlib.util.spec_from_file_location('data_gate_dispatch',path);d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d);d.trusted(path)
    fd=int(os.environ['UNIWARES_OPERATION_LOCK_FD']);actual=os.fstat(fd);expected=(d.STATE/project/'operation.lock').stat()
    import fcntl
    if (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino) or actual.st_uid!=0 or actual.st_mode & 0o077:raise ValueError('APPLICATION_LOCK_REQUIRED')
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    host=Host(d,project,environment);manifest=host.candidate(image,commit)
    report=activation(PlanStore(d.STATE/project/'operation-plans'),manifest,host.probe('ledger'),environment,host.database)
    print(json.dumps(public_page(report),separators=(',',':')))
    return 0 if report['activationDecision']=='proceed' else 3

if __name__=='__main__':
    try:sys.exit(main())
    except Exception:raise SystemExit('Data activation gate unavailable; owner action required. Activation was not attempted.') from None
