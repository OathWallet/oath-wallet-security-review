#!/usr/bin/env python3
"""Compare the same relay privacy corpus against original and repaired encoders."""
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
BASELINE = '0c466ea73d0875bdb46ce37a9bfcf6c702ee3639'
TEST = 'Tools/WalletConnectSDKValidation/RelayMetadataPrivacyTests.swift'
INPUTS = ['Vendor/Reown/Sources', 'Vendor/Reown/Tests', 'Packages/OathDiagnostics',
          'Tools/WalletConnectSDKValidation', 'Tools/CheckWalletConnectSDK.py']
CASES = {
    'testOptionalTransactionMetadataNotPublished': 4,
    'testCollectorResponseDoesNotBypassPrivacyBoundary': 3,
    'testDecodedMetadataCannotBeRepublished': 4,
    'testEncryptedResponseAndRoutingFieldsRemainIntact': 0,
}

def classify(text, code, before):
    events = re.findall(r"^Test Case '-\[SDKTests.RelayMetadataPrivacyTests (\w+)\]' (started|passed|failed|skipped)(?:\.| \()", text, re.M)
    all_events = re.findall(r"^Test Case '[^']+' (started|passed|failed|skipped)(?:\.| \()", text, re.M)
    if len(events) != 8 or len(all_events) != 8 or {n for n, _ in events} != set(CASES): return 'failed'
    for method, count in CASES.items():
        expected = ['started', 'failed' if before and count else 'passed']
        if [v for n, v in events if n == method] != expected: return 'failed'
    errors = [line for line in text.splitlines() if ': error:' in line]
    if not before:
        return 'passed' if code == 0 and not errors else 'failed'
    if code != 1 or len(errors) != 11 or text.count('Optional transaction metadata must stay inside the encrypted session:') != 11: return 'failed'
    for method, count in CASES.items():
        found = [line for line in errors if f' {method}] : XCTAssertNil failed:' in line]
        if len(found) != count: return 'failed'
    return 'metadata-disclosure-reproduced'

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
        with tempfile.TemporaryDirectory(prefix='oath-relay-metadata-') as temporary:
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
                       'python3', str(harness), '--build-system', 'native', '--disable-sandbox', '--filter', 'RelayMetadataPrivacyTests']
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
    ok = [r['status'] for r in rows] == ['metadata-disclosure-reproduced', 'passed']
    result = dict(check='relay-metadata', source_commit=sha, baseline_commit=BASELINE, status='passed' if ok else 'failed',
                  fixture_sha256=hashlib.sha256(fixture).hexdigest(), executions=rows, duration_seconds=round(time.monotonic()-started,3),
                  scope='Exact production relay encoder, collector and encrypted serializer; same four synthetic host tests; all build/test processes deny network',
                  limits='No live relay, simulator, physical device, production transaction or App Store validation. Harness changes only its isolated scratch path.')
    log = out/'relay-metadata.log'; log.write_text(json.dumps(result, indent=2)+'\n')
    result.update(log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'relay-metadata.json').write_text(json.dumps(result, indent=2)+'\n')
    raise SystemExit(0 if ok else 1)

if __name__ == '__main__': main()
