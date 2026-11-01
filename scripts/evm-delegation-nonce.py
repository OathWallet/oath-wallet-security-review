#!/usr/bin/env python3
"""Reproduce delegation nonce boundaries against the production serializer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '3cfa6168aac85b5e7c7c42daa4bf7b37e23276ce'
SELECTOR = 'OathAnkrTests.EVMDelegationNonceBoundaryTests'
FIXTURE = 'Packages/OathAnkr/Tests/OathAnkrTests/EVMDelegationNonceBoundaryTests.swift'


CASES = [
    'testMaximumNonceThrowsInsteadOfOverflowing',
    'testReservedAuthorizationNonceIsRejected',
    'testValidDelegationSizingDoesNotRequireFundedPlan',
    'testOrdinaryTransactionsDoNotAddAuthorizationNonce',
]


def outcome(text, code, name):
    events = re.findall(r"^Test Case '-\[OathAnkrTests.EVMDelegationNonceBoundaryTests (\w+)\]' (started|passed|skipped|failed)(?:\.| \()", text, re.M)
    if events == [(name, 'started'), (name, 'passed')] and code == 0:
        return 'passed'
    if (name == CASES[0] and events == [(name, 'started')] and code == -5):
        return 'trap-needs-stack-verification'
    if (name == CASES[1] and code == 1 and events == [(name, 'started'), (name, 'failed')]
        and 'XCTAssertThrowsError failed: did not throw an error' in text):
        return 'invalid-nonce-accepted'
    return 'failed'


def proves_overflow(text):
    return all(marker in text for marker in [
        'stop reason = Swift runtime failure: arithmetic overflow',
        'EVMSendCrypto.fields(', 'EVMSendCrypto.swift:31:',
        'testMaximumNonceThrowsInsteadOfOverflowing', 'plan.nonce+1',
    ])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--before', action='store_true')
    p.add_argument('--expected-commit')
    args = p.parse_args()
    source, out, scratch = args.source.resolve(), args.output.resolve(), args.scratch.resolve()
    expected = BEFORE if args.before else (args.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    if args.before and args.expected_commit and args.expected_commit != BEFORE:
        p.error('Before evidence must use the exact regression-only commit')
    sha = require_source_state(source, expected)
    out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    prefix = ['--package-path',str(source/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(scratch)]
    start = time.monotonic()

    def run(command, name, timeout):
        path = out/(name+'.log')
        began = time.monotonic()
        with path.open('w') as log:
            code,timed_out = logged_command(command,stream=log,env=env,timeout=timeout)
        text = path.read_text(errors='replace')
        for old,new in [(str(source),'<SOURCE>'),(str(scratch),'<SCRATCH>'),(str(Path.home()),'<HOME>')]:
            text = text.replace(old,new)
        path.write_text(text)
        return dict(exit_code=code,timed_out=timed_out,duration_seconds=round(time.monotonic()-began,3),
                    log=path.name,log_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),text

    toolchain,_ = run(['xcrun','swift','--version'],'swift-version',30)
    xcode,_ = run(['xcodebuild','-version'],'xcode-version',30)
    build,_ = run(['swift','build',*prefix,'--force-resolved-versions','--build-tests','--jobs','4'],'build',900)
    runs = []
    binary_hash = None
    if build['exit_code'] == 0:
        directory = Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],env=env,text=True).strip())
        bundle = directory/'OathAnkrPackageTests.xctest'
        binary_hash = hashlib.sha256((bundle/'Contents/MacOS/OathAnkrPackageTests').read_bytes()).hexdigest()
        for i in range(3):
            for name in CASES:
                result,text = run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',
                                  '/usr/bin/xcrun','xctest','-XCTest',SELECTOR+'/'+name,str(bundle)],f'case-{i+1:02}-{name}',120)
                result.update(case=name, status=outcome(text,result['exit_code'],name))
                runs.append(result)
        stack = None
        if args.before:
            xctest = subprocess.check_output(['xcrun','--find','xctest'],env=env,text=True).strip()
            stack,text = run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',
                              '/usr/bin/xcrun','lldb','--batch','-o','run','-k','thread backtrace','--',
                              xctest,'-XCTest',SELECTOR+'/'+CASES[0],str(bundle)],'overflow-backtrace',120)
            stack['overflow_verified'] = not stack['timed_out'] and proves_overflow(text)
    else:
        stack = None
    require_source_state(source,sha)
    passed = sum(r['status']=='passed' for r in runs)
    traps = sum(r['status']=='trap-needs-stack-verification' for r in runs)
    invalid = sum(r['status']=='invalid-nonce-accepted' for r in runs)
    expected = (passed==6 and traps==3 and invalid==3 and stack and stack['overflow_verified']) if args.before else passed==12
    success = toolchain['exit_code']==0 and xcode['exit_code']==0 and build['exit_code']==0 and len(runs)==12 and not any(r['timed_out'] for r in runs) and bool(expected)
    result = dict(check='evm-delegation-nonce',source_commit=sha,phase='before' if args.before else 'after',
        status=('expected-failure' if args.before else 'passed') if success else 'failed',
        toolchain=toolchain,xcode=xcode,runs=runs,stack=stack,traps=traps,invalid_nonce_accepted=invalid,tests_passed=passed,build=build,duration_seconds=round(time.monotonic()-start,3),
        selector=SELECTOR,fixture_sha256=hashlib.sha256((source/FIXTURE).read_bytes()).hexdigest(),
        test_binary_sha256=binary_hash,runtime_scope='macOS host; synthetic direct serialization calls; network denied; no simulator or device',
        limitation='The public helper crashes on a direct malformed call. Existing app quote/sign/verify paths already validate the nonce; no reachable application exploit established.')
    # A compact log binds the summary; individual compiler/process logs retain
    # their own checksums and are not replaced by an exit-code-only verdict.
    log=out/'evm-delegation-nonce.log'
    log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'evm-delegation-nonce.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['phase']}: {result['status']}; {traps} traps, {invalid} invalid acceptances, {passed} passes")
    raise SystemExit(0 if success else 1)


if __name__=='__main__': main()
