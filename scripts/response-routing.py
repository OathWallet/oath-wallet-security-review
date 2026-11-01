#!/usr/bin/env python3
"""Compare session response topic, origin and method validation with an identical synthetic corpus."""
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
BASELINE = '42846f9f9b9ff66ff8407700aa77539e70f963c5'
TEST = 'Tools/WalletConnectSDKValidation/SessionResponseRoutingTests.swift'
INPUTS = ['Vendor/Reown/Sources', 'Vendor/Reown/Tests', 'Packages/OathDiagnostics', 'Tools/WalletConnectSDKValidation', 'Tools/CheckWalletConnectSDK.py']
ASSERTIONS = {'testLinkRejectsLocallyOriginatedRequest': ['XCTAssertTrue failed - '
                                             'Mismatched pending request must '
                                             'be rejected',
                                             'XCTAssertTrue failed - '
                                             'Mismatched pending request must '
                                             'not open a response link',
                                             'XCTAssertNotNil failed - '
                                             'Mismatched pending request must '
                                             'remain pending'],
 'testLinkRejectsOtherProtocolMethod': ['XCTAssertTrue failed - Mismatched '
                                        'pending request must be rejected',
                                        'XCTAssertTrue failed - Mismatched '
                                        'pending request must not open a '
                                        'response link',
                                        'XCTAssertNotNil failed - Mismatched '
                                        'pending request must remain pending'],
 'testLinkRejectsOtherSessionExpiredRequest': ['XCTAssertTrue failed - '
                                               'Mismatched pending request '
                                               'must not open a response link',
                                               'XCTAssertNotNil failed - '
                                               'Mismatched pending request '
                                               'must remain pending'],
 'testLinkRejectsOtherSessionRequest': ['XCTAssertTrue failed - Mismatched '
                                        'pending request must be rejected',
                                        'XCTAssertTrue failed - Mismatched '
                                        'pending request must not open a '
                                        'response link',
                                        'XCTAssertNotNil failed - Mismatched '
                                        'pending request must remain pending'],
 'testRelayRejectsLocallyOriginatedRequest': ['XCTAssertTrue failed - '
                                              'Mismatched pending request must '
                                              'be rejected',
                                              'XCTAssertNil failed: '
                                              '"synthetic-session" - '
                                              'Mismatched pending request must '
                                              'not reach relay response'],
 'testRelayRejectsOtherProtocolMethod': ['XCTAssertTrue failed - Mismatched '
                                         'pending request must be rejected',
                                         'XCTAssertNil failed: '
                                         '"synthetic-session" - Mismatched '
                                         'pending request must not reach relay '
                                         'response'],
 'testRelayRejectsOtherSessionExpiredRequest': ['XCTAssertFalse failed - '
                                                'Mismatched pending request '
                                                'must not send a relay expiry '
                                                'response'],
 'testRelayRejectsOtherSessionRequest': ['XCTAssertTrue failed - Mismatched '
                                         'pending request must be rejected',
                                         'XCTAssertNil failed: '
                                         '"synthetic-session" - Mismatched '
                                         'pending request must not reach relay '
                                         'response']}
TRAPS = {}
CONTROLS = ['testLinkValidResponseCompletesHistory', 'testRelayValidResponseReachesEndpoint', 'testLinkExpiredRequestSendsExpiryError', 'testRelayExpiredRequestSendsExpiryError']
CASES = CONTROLS + list(ASSERTIONS) + list(TRAPS)

def classify(text, code, before, case):
    if case not in CASES: return 'failed'
    text = text.replace("warning: '--build-system native' has been deprecated and will be removed in a future release; please report an issue at https://github.com/swiftlang/swift-package-manager/issues if you are unable to adopt the default build system.\n", '')
    events = re.findall(r"^Test Case '([^']+)' (started|passed|failed|skipped)(?:\.| \()", text, re.M)
    name = f'-[SDKTests.SessionResponseRoutingTests {case}]'
    errors = [line for line in text.splitlines() if ': error:' in line]
    if before and case in ASSERTIONS:
        messages = [line.split(name+' : ', 1)[-1] for line in errors]
        valid = (code == 1 and events == [(name, 'started'), (name, 'failed')] and 'Fatal error:' not in text
                 and sorted(messages) == sorted(ASSERTIONS[case])
                 and all(name+' : ' in line for line in errors))
        return 'expected-response-routing-failure' if valid else 'failed'
    return 'passed' if code == 0 and events == [(name, 'started'), (name, 'passed')] and not errors and 'Fatal error:' not in text else 'failed'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--expected-commit')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    a = p.parse_args()
    source, out, scratch = a.source.resolve(), a.output.resolve(), a.scratch.resolve()
    sha = require_source_state(source, a.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    env['SWIFT_DETERMINISTIC_HASHING'] = '1'
    fixture = (source/TEST).read_bytes()
    if fixture != subprocess.check_output(['git', '-C', str(source), 'show', BASELINE+':'+TEST]): raise ValueError('Paired fixture changed')
    if set(re.findall(rb'func (test\w+)\(', fixture)) != {name.encode() for name in CASES}: raise ValueError('Unexpected test corpus')
    rows = []
    started = time.monotonic()
    for phase, revision in [('before', BASELINE), ('after', sha)]:
        archive = subprocess.check_output(['git', '-C', str(source), 'archive', revision, *INPUTS])
        with tempfile.TemporaryDirectory(prefix='oath-response-routing-') as temporary:
            work = Path(temporary)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(work, filter='data')
            harness = work/'Tools/CheckWalletConnectSDK.py'
            original = harness.read_text()
            token = "'/tmp/oath-sdk-warning-host'"
            if original.count(token) != 1: raise ValueError('Unexpected SDK harness scratch layout')
            harness.write_text(original.replace(token, repr(str(scratch/phase))))
            for index, case in enumerate(CASES):
                log = out/(phase+'-'+case+'.log'); began = time.monotonic()
                command = ['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)',
                    'python3', str(harness), '--build-system', 'native', '--disable-sandbox', '--filter', 'SessionResponseRoutingTests.'+case]
                if index: command += ['--skip-build']
                with log.open('w') as stream: code, timeout = logged_command(command, stream=stream, env=env, timeout=360)
                text = log.read_text(errors='replace').replace(str(work), '<SOURCE-COPY>').replace(str(source), '<SOURCE>').replace(str(scratch), '<SCRATCH>').replace(str(Path.home()), '<HOME>')
                text = re.sub(r'/(?:private/)?var/folders/[^\s:]+/oath-sdk-validation-[^/\s]+', '<SDK-HARNESS>', text)
                log.write_text(text)
                status = classify(text, code, phase == 'before', case) if not timeout else 'failed'
                rows.append(dict(phase=phase, case=case, source_commit=revision, status=status, exit_code=code, timed_out=timeout,
                    duration_seconds=round(time.monotonic()-began,3), source_archive_sha256=hashlib.sha256(archive).hexdigest(),
                    log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
                print(phase, case, status, flush=True)
                # Do not run stale --skip-build tests if the initial compilation/control fails.
                if index == 0 and status != 'passed': break
    require_source_state(source, sha)
    ok = len(rows) == 2*len(CASES) and all(row['status'] != 'failed' for row in rows)
    result = dict(check='response-routing', source_commit=sha, baseline_commit=BASELINE, status='passed' if ok else 'failed',
        fixture_sha256=hashlib.sha256(fixture).hexdigest(), executions=rows, duration_seconds=round(time.monotonic()-started,3),
        scope='Complete production relay and link session responders, HistoryService, RPCHistory and link serializer. Same 12 cases in separate network-denied host processes; eight invalid-routing cases and four valid/expiry controls.',
        limits='In-memory session store and KMS. Link opening is an explicit host callback; no UIKit/domain association. Relay uses the upstream NetworkingInteractorMock recorder, not a live relay or acknowledgement. App callers retain original request topic; no remote signing bypass or fund loss established. Generic transport response APIs and concurrent history replacement remain separate review gaps.')
    log = out/'response-routing.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'response-routing.json').write_text(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if ok else 1)

if __name__ == '__main__': main()
