#!/usr/bin/env python3
"""Compare production event opt-out behavior against the same synthetic lifecycle corpus."""
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
BASELINE = '95e557d389413daa4dc03b8c7f7b3d4803507a7c'
TEST = 'Tools/WalletConnectSDKValidation/EventsPrivacyLifecycleTests.swift'
INPUTS = ['Vendor/Reown/Sources', 'Vendor/Reown/Tests', 'Packages/OathDiagnostics',
          'Tools/WalletConnectSDKValidation', 'Tools/CheckWalletConnectSDK.py']
CASES = {
    'testDisabledClientDoesNotCollectOrRetainEvents': 2,
    'testDisablingPurgesEveryQueueAndInMemoryTrace': 4,
    'testDisablingPreventsRetryAfterCancellationResistantFailure': 2,
    'testFreshTelemetryStateRequiresOptIn': 1,
    'testExplicitlyEnabledClientCanDeliverSyntheticEvents': 0,
    'testLateSuccessCannotEraseEventsFromNewGeneration': 2,
    'testEventsAddedDuringDeliveryAreNotErased': 2,
    'testAcknowledgementPreservesActiveTrace': 0,
    'testTransportCancellationStopsURLSessionRequest': 1,
}

EXPECTED = {
    'testDisabledClientDoesNotCollectOrRetainEvents': [
        'XCTAssertTrue failed - Disabled initialization must not retain events',
        'XCTAssertTrue failed - Disabled message collection must not retain events'],
    'testDisablingPurgesEveryQueueAndInMemoryTrace': [
        'XCTAssertTrue failed - Disabling must erase queued initialization events',
        'XCTAssertTrue failed - Disabling must erase queued message events',
        'XCTAssertTrue failed - Disabling must erase in-memory trace',
        'XCTAssertNil failed: "synthetic-topic" - Disabling must erase in-memory topic'],
    'testDisablingPreventsRetryAfterCancellationResistantFailure': [
        'Fulfilled inverted expectation "no retry after opt-out".',
        'XCTAssertEqual failed: ("3") is not equal to ("1") - Opt-out must prevent retrying a previously accepted request'],
    'testFreshTelemetryStateRequiresOptIn': ['XCTAssertFalse failed - A new SDK installation must not opt into telemetry'],
    'testExplicitlyEnabledClientCanDeliverSyntheticEvents': [],
    'testLateSuccessCannotEraseEventsFromNewGeneration': [
        'Fulfilled inverted expectation "new generation must survive old acknowledgement".',
        'XCTAssertFalse failed - Old delivery must not erase a new opt-in generation'],
    'testEventsAddedDuringDeliveryAreNotErased': [
        'Fulfilled inverted expectation "new events must survive snapshot acknowledgement".',
        'XCTAssertFalse failed - Acknowledgement must not erase events absent from its snapshot'],
    'testAcknowledgementPreservesActiveTrace': [],
    'testTransportCancellationStopsURLSessionRequest': [
        'Asynchronous wait failed: Exceeded timeout of 0.3 seconds, with unfulfilled expectations: "cancellation reached URLSession".'],
}

def classify(text, code, before):
    events = re.findall(r"^Test Case '-\[SDKTests.EventsPrivacyLifecycleTests (\w+)\]' (started|passed|failed|skipped)(?:\.| \()", text, re.M)
    all_events = re.findall(r"^Test Case '[^']+' (started|passed|failed|skipped)(?:\.| \()", text, re.M)
    if len(events) != 2*len(CASES) or len(all_events) != 2*len(CASES) or {n for n, _ in events} != set(CASES): return 'failed'
    for method, count in CASES.items():
        expected = ['started', 'failed' if before and count else 'passed']
        if [v for n, v in events if n == method] != expected: return 'failed'
    errors = [line for line in text.splitlines() if ': error:' in line]
    if not before:
        return 'passed' if code == 0 and not errors else 'failed'
    if code != 1 or len(errors) != sum(CASES.values()): return 'failed'
    for method, count in CASES.items():
        found = [line.split('] : ', 1)[1] for line in errors if f' {method}] : ' in line]
        if sorted(found) != sorted(EXPECTED[method]) or len(found) != count: return 'failed'
    return 'opt-out-defects-reproduced'

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
    fixture = (source/TEST).read_bytes()
    if fixture != subprocess.check_output(['git', '-C', str(source), 'show', BASELINE+':'+TEST]): raise ValueError('Paired fixture changed')
    rows = []
    started = time.monotonic()
    for phase, revision in [('before', BASELINE), ('after', sha)]:
        archive = subprocess.check_output(['git', '-C', str(source), 'archive', revision, *INPUTS])
        with tempfile.TemporaryDirectory(prefix='oath-events-lifecycle-') as temporary:
            work = Path(temporary)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(work, filter='data')
            harness = work/'Tools/CheckWalletConnectSDK.py'
            original = harness.read_text()
            token = "'/tmp/oath-sdk-warning-host'"
            if original.count(token) != 1: raise ValueError('Unexpected SDK harness scratch layout')
            harness.write_text(original.replace(token, repr(str(scratch/phase))))
            log = out/(phase+'.log'); began = time.monotonic()
            command = ['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)',
                       # SwiftPM cannot nest sandbox_apply inside this outer
                       # profile. Disable only its nested manifest sandbox;
                       # the enclosing network denial still applies throughout.
                       'python3', str(harness), '--build-system', 'native', '--disable-sandbox', '--filter', 'EventsPrivacyLifecycleTests']
            with log.open('w') as stream: code, timeout = logged_command(command, stream=stream, env=env, timeout=360)
            text = log.read_text(errors='replace').replace(str(work), '<SOURCE-COPY>').replace(str(source), '<SOURCE>').replace(str(scratch), '<SCRATCH>').replace(str(Path.home()), '<HOME>')
            text = re.sub(r'/(?:private/)?var/folders/[^\s:]+/oath-sdk-validation-[^/\s]+', '<SDK-HARNESS>', text)
            log.write_text(text)
            status = classify(text, code, phase == 'before') if not timeout else 'failed'
            rows.append(dict(phase=phase, source_commit=revision, status=status, exit_code=code, timed_out=timeout,
                             duration_seconds=round(time.monotonic()-began, 3), source_archive_sha256=hashlib.sha256(archive).hexdigest(),
                             log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
            print(phase, status, flush=True)
    require_source_state(source, sha)
    ok = [r['status'] for r in rows] == ['opt-out-defects-reproduced', 'passed']
    result = dict(check='events-lifecycle', source_commit=sha, baseline_commit=BASELINE, status='passed' if ok else 'failed',
                  fixture_sha256=hashlib.sha256(fixture).hexdigest(), executions=rows, duration_seconds=round(time.monotonic()-started,3),
                  scope='Actual EventsClient, dispatcher and HTTP service; same nine synthetic host tests; all build/test processes deny network',
                  limits='No live service, simulator, physical device, production transaction or App Store validation. Cancellation and negative assertions have explicit bounded observation windows; requests already received by a server cannot be recalled. Harness changes only its isolated scratch path.')
    log = out/'events-lifecycle.log'; log.write_text(json.dumps(result, indent=2)+'\n')
    result.update(log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'events-lifecycle.json').write_text(json.dumps(result, indent=2)+'\n')
    raise SystemExit(0 if ok else 1)

if __name__ == '__main__': main()
