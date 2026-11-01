#!/usr/bin/env python3
"""Replay a single correlated response during each production relay write."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time

from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '439011c1774a5b5e22e75388ab59b67b3443b7a6'
TEST = 'Tools/WalletConnectSDKValidation/RelayEarlyResponseTests.swift'
INPUTS = ['Vendor/Reown/Sources', 'Vendor/Reown/Tests', 'Packages/OathDiagnostics',
          'Tools/WalletConnectSDKValidation', 'Tools/CheckWalletConnectSDK.py']
EARLY = {'testPublishCapturesEarlyAcknowledgement', 'testSubscribeCapturesEarlyID', 'testBatchCapturesEarlyIDs'}
CONTROLS = {'testPublishSendErrorWins', 'testSubscribeSendErrorWins', 'testBatchSendErrorWins'}
SUITE = 'RelayEarlyResponseTests'
MESSAGE = 'failed - Lost a matching relay reply delivered before protectedSend returned'

def verify(text, code, before):
    observed = re.findall(r"^Test Case '-\[SDKTests\.RelayEarlyResponseTests (test\w+)\]' (started|passed|failed|skipped)\b", text, re.M)
    expected_failures = EARLY if before else set()
    expected = [(case, state) for case in EARLY | CONTROLS
                for state in ('started', 'failed' if case in expected_failures else 'passed')]
    errors = [line.partition(': error: ')[2] for line in text.splitlines() if ': error:' in line]
    expected_errors = [f'-[SDKTests.{SUITE} {case}] : {MESSAGE}' for case in expected_failures]
    return (code == int(before) and sorted(observed) == sorted(expected)
            and sorted(errors) == sorted(expected_errors) and 'Fatal error:' not in text)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--expected-commit')
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    pin = require_source_state(source,args.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    fixture = (source/TEST).read_bytes()
    if fixture != subprocess.check_output(['git','-C',source,'show',BASELINE+':'+TEST]):
        raise ValueError('Fixture differs between source revisions')
    if set(re.findall(r'func (test\w+)\(',fixture.decode())) != EARLY | CONTROLS:
        raise ValueError('Unexpected fixture case list')
    out = args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    started = time.monotonic()
    rows = []
    for phase, revision in [('before', BASELINE), ('after', pin)]:
        archive = subprocess.check_output(['git','-C',source,'archive',revision,*INPUTS])
        with tempfile.TemporaryDirectory(prefix='oath-early-replies-') as directory:
            root = Path(directory)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(root,filter='data')
            harness = root/'Tools/CheckWalletConnectSDK.py'
            original = harness.read_text()
            token = "'/tmp/oath-sdk-warning-host'"
            if original.count(token) != 1: raise ValueError('Unexpected host scratch layout')
            harness.write_text(original.replace(token,repr(str(args.scratch.resolve()/phase))))
            log = out/(phase+'.log')
            cmd = ['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',
                   'python3',str(harness),'--build-system','native','--disable-sandbox','--filter',SUITE]
            with log.open('w') as stream:
                code, timeout = logged_command(cmd,stream=stream,env=env,timeout=360)
            ok = not timeout and verify(log.read_text(errors='replace'),code,phase=='before')
            rows.append(dict(phase=phase,source_commit=revision,matched_expected_outcomes=ok,
                             exit_code=code,timed_out=timeout,log=log.name,
                             log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                             source_archive_sha256=hashlib.sha256(archive).hexdigest()))
            print(phase,ok,flush=True)
    require_source_state(source,pin)
    passed = all(row['matched_expected_outcomes'] for row in rows)
    result = dict(check='relay-early-replies',status='passed' if passed else 'failed',
                  source_commit=pin,baseline_commit=BASELINE,fixture_sha256=hashlib.sha256(fixture).hexdigest(),
                  executions=rows,duration_seconds=round(time.monotonic()-started,3),
                  scope='Three real SDK timeouts and three send-error controls on the baseline; all six must pass on the repair. Single matching reply inside the synthetic write. No live socket.')
    log = out/'relay-early-replies.log'
    log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'relay-early-replies.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())
