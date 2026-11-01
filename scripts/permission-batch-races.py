#!/usr/bin/env python3
"""Verify in-flight batch revocation with the actual vault and three imported-key signers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import time
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '976971f0ca3362cfba8c63bc738bd80d15abf096'
FIXTURES = ['Tools/CheckPermissionBatchRaces.swift', 'Tools/CheckMultiWallet.py']
EXPECTED_FAILURES = {f'{chain}/{action}: revoked grant produced a signature'
                     for chain in ['arbitrum','tron','solana'] for action in ['end','replace','expire']}


def outcome(text, code):
    summaries = re.findall(r'^BATCH_RACES checks=(\d+) failures=(\d+) scenarios=(\d+) chains=(\d+)$',text,re.M)
    failures = re.findall(r'^FAIL: (.+)$',text,re.M)
    if summaries == [('84','0','21','3')] and code == 0 and not failures:
        return 'passed'
    if summaries == [('84','9','21','3')] and code == 1 and len(failures)==9 and set(failures)==EXPECTED_FAILURES:
        return 'revocation-reproduced'
    return 'failed'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--before',action='store_true')
    p.add_argument('--expected-commit')
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve();scratch=a.scratch.resolve()
    expected=BEFORE if a.before else (a.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    if a.before and a.expected_commit and a.expected_commit!=BEFORE:p.error('Before requires the regression-only revision')
    sha=require_source_state(source,expected);out.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    env['OATH_VALIDATION_SCRATCH']=str(scratch)
    env['OATH_ELECTRUM_FIXTURES']=str(source/'Packages/OathBitcoin/Tests/OathBitcoinTests/Fixtures/electrum-reference.json')
    env['OATH_AEZEED_FIXTURES']=str(source/'Packages/OathAezeed/Tests/OathAezeedTests/Fixtures/lnd-production.json')
    env['OATH_TEST_WORDLISTS']=str(source/'OathApp/Resources/BIP39')
    env['OATH_TEST_LITECOIN_VECTORS']=str(source/'Packages/OathBitcoin/Tests/OathBitcoinTests/Fixtures/litecoin-vectors.json')
    env['OATH_TEST_DOGECOIN_VECTORS']=str(source/'Packages/OathBitcoin/Tests/OathBitcoinTests/Fixtures/dogecoin-vectors.json')
    start=time.monotonic()
    def run(command,name,timeout):
        path=out/(name+'.log');began=time.monotonic()
        with path.open('w') as log:
            code,timed_out=logged_command(command,stream=log,env=env,timeout=timeout)
        text=path.read_text(errors='replace')
        for old,new in [(str(source),'<SOURCE>'),(str(scratch),'<SCRATCH>'),(str(Path.home()),'<HOME>')]:text=text.replace(old,new)
        path.write_text(text)
        return dict(exit_code=code,timed_out=timed_out,duration_seconds=round(time.monotonic()-began,3),log=path.name,log_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),text
    toolchain,_=run(['xcrun','swift','--version'],'swift-version',30)
    xcode,_=run(['xcodebuild','-version'],'xcode-version',30)
    build,text=run(['python3',str(source/'Tools/CheckMultiWallet.py'),'--permission-batch-races'],'build-and-harness',900)
    build['status']=outcome(text,build['exit_code'])
    desired='revocation-reproduced' if a.before else 'passed'
    runs=[];binary_hash=None
    if build['status']==desired and not build['timed_out']:
        binary=scratch/(platform.machine()+'-apple-macosx/debug/WalletValidation')
        binary_hash=hashlib.sha256(binary.read_bytes()).hexdigest()
        for i in range(3):
            result,text=run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(binary)],f'run-{i+1}',180)
            result['status']=outcome(text,result['exit_code']);runs.append(result)
    require_source_state(source,sha)
    success=toolchain['exit_code']==0 and xcode['exit_code']==0 and len(runs)==3 and all(r['status']==desired and not r['timed_out'] for r in runs)
    result=dict(check='permission-batch-races',source_commit=sha,phase='before' if a.before else 'after',status=('expected-failure' if a.before else 'passed') if success else 'failed',build=build,toolchain=toolchain,xcode=xcode,runs=runs,
        fixture_sha256={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in FIXTURES},test_binary_sha256=binary_hash,
        duration_seconds=round(time.monotonic()-start,3),runtime_scope='macOS host; production vault, SQL and imported-key EVM/TRON/Solana signatures; substituted biometrics, HD derivation and grant clock; repeated executions deny network',
        limitation='No UI, real biometric, simulator, physical device, broadcast or App Store execution. A controllable monotonic grant clock changes only the permission deadline in the expiry fixture.')
    log=out/'permission-batch-races.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'permission-batch-races.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['phase']}: {result['status']}; {len(runs)} network-denied process runs")
    raise SystemExit(0 if success else 1)

if __name__=='__main__':main()
