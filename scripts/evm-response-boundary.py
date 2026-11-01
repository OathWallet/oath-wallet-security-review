#!/usr/bin/env python3
"""Reproduce the EVM pre-broadcast response-size gap with the production regression."""
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
BEFORE = '04a239277b3b7a90ff5737b682cf2183bc5616fb'
SELECTOR = 'OathAnkrTests.EVMSendResponseBoundaryTests'
FIXTURE = 'Packages/OathAnkr/Tests/OathAnkrTests/EVMSendResponseBoundaryTests.swift'


CASES = {
    'testOversizedStandaloneChainReplyPreventsBroadcast',
    'testExactStandaloneLimitRemainsAccepted',
    'testBatchBoundaryStillRejectsOneByteOverAndAcceptsExactLimit',
}


def outcome(text, code):
    events = re.findall(r"^Test Case '-\[OathAnkrTests.EVMSendResponseBoundaryTests (\w+)\]' (started|passed|skipped|failed)(?:\.| \()", text, re.M)
    if len(events) != 6 or set(n for n, _ in events) != CASES:
        return 'failed'
    states = {name: [state for n, state in events if n == name] for name in CASES}
    if code == 0 and all(value == ['started', 'passed'] for value in states.values()):
        return 'passed'
    broken = 'testOversizedStandaloneChainReplyPreventsBroadcast'
    if (code == 1 and states[broken] == ['started', 'failed']
        and all(value == ['started', 'passed'] for name, value in states.items() if name != broken)
        and 'Oversized standalone chain reply must be rejected before broadcast' in text
        and 'Oversized standalone chain reply must not admit a broadcast' in text):
        return 'boundary-reproduced'
    return 'failed'


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
            result,text = run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',
                               '/usr/bin/xcrun','xctest','-XCTest',SELECTOR,str(bundle)],f'case-{i+1:02}',120)
            result['status'] = outcome(text,result['exit_code'])
            runs.append(result)
    require_source_state(source,sha)
    reproduced = sum(r['status']=='boundary-reproduced' for r in runs)
    passed = sum(r['status']=='passed' for r in runs)
    success = toolchain['exit_code']==0 and xcode['exit_code']==0 and build['exit_code']==0 and len(runs)==3 and not any(r['status']=='failed' for r in runs) and (reproduced==3 if args.before else passed==3)
    result = dict(check='evm-response-boundary',source_commit=sha,phase='before' if args.before else 'after',
        status=('expected-failure' if args.before else 'passed') if success else 'failed',
        toolchain=toolchain,xcode=xcode,runs=runs,boundary_reproduced=reproduced,process_runs_passed=passed,tests_passed=passed*3+reproduced*2,build=build,duration_seconds=round(time.monotonic()-start,3),
        selector=SELECTOR,fixture_sha256=hashlib.sha256((source/FIXTURE).read_bytes()).hexdigest(),
        test_binary_sha256=binary_hash,runtime_scope='macOS host; synthetic oversized RPC responses; network denied; no simulator or device',
        limitation='Three deterministic repetitions. Does not demonstrate fund loss, denial of service, or a streaming transport memory limit; default transport separately caps replies at 64 MiB.')
    # A compact log binds the summary; individual compiler/process logs retain
    # their own checksums and are not replaced by an exit-code-only verdict.
    log=out/'evm-response-boundary.log'
    log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'evm-response-boundary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['phase']}: {result['status']}; {reproduced} boundary reproductions, {passed} passes out of {len(runs)}")
    raise SystemExit(0 if success else 1)


if __name__=='__main__': main()
