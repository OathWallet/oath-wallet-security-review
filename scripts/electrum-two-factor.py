#!/usr/bin/env python3
"""Reproduce the same cosigner regression on clean public application commits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from source_state import require_source_state

BASE = '6ff120198e46111cbe05f4bd76a7e94dd7a001e2'
CASE = 'ElectrumMnemonicTests.testTwoFactorCJKSeedBoundaries'
PROBE = 'Packages/OathBitcoin/Tests/OathBitcoinTests/ElectrumMnemonicTests.swift'
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--before',action='store_true')
    parser.add_argument('--expected-commit')
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source=args.source.resolve()
    pin=require_source_state(source, BASE if args.before else args.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    probe=(source/PROBE).read_bytes()
    if subprocess.check_output(['git','-C',source,'show',BASE+':'+PROBE]) != probe:
        raise ValueError('Paired package tests must use the identical checked-in probe')
    args.output.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR','SDKROOT','CI')}
    cmd=['swift','test','--build-system','native','--jobs','4','--package-path',source/'Packages/OathBitcoin','--scratch-path',args.scratch,'--filter',CASE]
    began=time.monotonic()
    result=subprocess.run(cmd,cwd=source,env=env,capture_output=True,text=True,timeout=1200)
    text=result.stdout+'\n'+result.stderr
    name='-[OathBitcoinTests.ElectrumMnemonicTests testTwoFactorCJKSeedBoundaries]'
    state='failed' if args.before else 'passed'
    if result.returncode!=int(args.before) or text.count("Test Case '"+name+"' started.")!=1 or text.count("Test Case '"+name+"' "+state+" (")!=1:
        raise ValueError('Missing named real test outcome, empty selection or build failure')
    failures=4 if args.before else 0
    if not re.search(rf'Executed 1 test, with {failures} failures \(0 unexpected\)',text):
        raise ValueError('Unexpected number of cosigner assertion failures')
    if args.before and (text.count('ElectrumMnemonicTests.swift:28: error:')!=2 or text.count('ElectrumMnemonicTests.swift:29: error:')!=2):
        raise ValueError('Unexpected failure locations')
    # Do not ship arbitrary Swift diagnostics or crash dumps. Retain a hash of the original stream.
    data=dict(check='electrum-two-factor',source_commit=pin,phase='before' if args.before else 'after',
              status='reproduced' if args.before else 'passed',selector=CASE,failures=failures,exit_code=result.returncode,
              suite_sha256=hashlib.sha256(probe).hexdigest(),raw_stream_sha256=hashlib.sha256(text.encode()).hexdigest(),
              duration_seconds=round(time.monotonic()-began,3),scope='Host decoder. Separate evidence checks the encrypted wallet and receive address.')
    log=args.output/'electrum-two-factor.log'
    log.write_text(json.dumps(data,indent=2)+'\n')
    data.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (args.output/'electrum-two-factor.json').write_text(json.dumps(data,indent=2)+'\n')
    print(f'{CASE}: {state} with {failures} assertions failing')

if __name__=='__main__':
    main()
