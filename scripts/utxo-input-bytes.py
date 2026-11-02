#!/usr/bin/env python3
"""Replay the UTXO address and Data-slice regressions in separate, offline XCTest processes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import signal
import subprocess
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BASE = '251d883f5095a42f2dff0f7ae9c6efed455afdb3'
PROBE = 'Packages/OathBitcoin/Tests/OathBitcoinTests/BitcoinSendOptionsTests.swift'
CASES = ('testRecipientAddressRequiresOriginalASCIIBytes','testSlicedSingleByteMessageReachesReviewedPlan','testByteLimitsAndPushdataBoundaries')

def classify(case, before, status, text):
    name = f'-[OathBitcoinTests.BitcoinSendOptionsTests {case}]'
    starts = text.count(f"Test Case '{name}' started.")
    if starts != 1:
        raise ValueError('Missing unique named test start')
    if before and case == CASES[0]:
        failures = re.findall(r'XCTAssertThrowsError failed: did not throw an error - (bitcoincash|litecoin)$',text,re.M)
        if status == 1 and sorted(failures) == ['bitcoincash','litecoin'] and 'Executed 1 test, with 2 failures' in text:
            return 'both non-ASCII aliases accepted'
    elif before and case == CASES[1]:
        if status in (-signal.SIGTRAP,-signal.SIGILL) and 'Executed 1 test' not in text:
            return 'named test terminated by trap'
    elif status == 0 and text.count(f"Test Case '{name}' passed (") == 1 and 'Executed 1 test, with 0 failures' in text:
        return 'passed'
    raise ValueError('Unexpected isolation result for '+case)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--before',action='store_true')
    parser.add_argument('--expected-commit')
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();src=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    pin=require_source_state(src,BASE if args.before else args.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    probe=(src/PROBE).read_bytes()
    if probe != subprocess.check_output(['git','-C',src,'show',BASE+':'+PROBE]):
        raise ValueError('Changed test code')
    cmd=['swift','build','--package-path',src/'Packages/OathBitcoin','--scratch-path',args.scratch.absolute(),'--build-system','native','--force-resolved-versions']
    with (out/'compile.log').open('w') as log:
        subprocess.run([*cmd,'--build-tests','--jobs','4'],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
    bundle=Path(subprocess.check_output([*cmd,'--show-bin-path'],text=True).strip())/'OathBitcoinPackageTests.xctest'
    rows=[]
    for case in CASES:
        proc=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',
                             'OathBitcoinTests.BitcoinSendOptionsTests/'+case,bundle],capture_output=True,timeout=60)
        raw=proc.stdout+proc.stderr
        verdict=classify(case,args.before,proc.returncode,raw.decode(errors='replace'))
        rows.append(dict(case=case,outcome=verdict,exit_code=proc.returncode,original_log_sha256=hashlib.sha256(raw).hexdigest()))
    result=dict(check='utxo-input-bytes',source_commit=pin,status='reproduced' if args.before else 'passed',results=rows,
                probe_sha256=hashlib.sha256(probe).hexdigest(),scope='Production public planner and recipient decoders. Synthetic, offline, without UI.')
    log=out/'utxo-input-bytes.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'utxo-input-bytes.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified three isolated public planner cases')

if __name__=='__main__':
    main()
