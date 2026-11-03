#!/usr/bin/env python3
"""Replay OW-2026-061 against two pinned public commits, without live flags."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_state import require_source_state

BEFORE = 'f8a6d29803594f1f3a74063e92f90b8155122556'
AFTER = '8a31eb265c34ef7f37ba21741201842366d43b7b'
FAILING = {'testReviewRejectsFailedOrMissingSimulationMetadata',
           'testPreflightRejectsFailedOrMissingSimulationMetadata'}
METHODS = FAILING | {'testSuccessfulSimulationAndDeliverMaxAliasRemainAccepted',
                    'testEngineFailureCannotBeHiddenBySuccessfulMetadata',
                    'testReceiptNeverConfusesUncertainSubmissionWithFailure',
                    'testWrongNetworkAndReceiptHashCannotConfirm'}

def verify(cases, before):
    names = [c['selector'].split('/')[-1] for c in cases]
    if len(cases) != 6 or set(names) != METHODS:
        raise ValueError('Missing, duplicate or unexpected test method')
    for case, name in zip(cases, names):
        expected = 'failed' if before and name in FAILING else 'passed'
        if case['status'] != expected or (case['exit_code'] == 0) != (expected == 'passed'):
            raise ValueError('Unexpected result for ' + name)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('scratch', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--before', action='store_true')
    a = p.parse_args()
    commit = BEFORE if a.before else AFTER
    source, out = a.source.resolve(), a.output.resolve()
    require_source_state(source, commit)
    out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in
           ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL']}
    start = time.monotonic()
    command = [sys.executable, str(Path(__file__).with_name('isolated_tests.py')),
               str(source), 'OathAnkr', str(a.scratch.resolve()), str(out),
               '--filter', 'WalletConnectXrplProviderTests']
    with (out/'driver.log').open('w') as stream:
        code = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT).returncode
    cases = json.loads((out/'OathAnkr-cases.json').read_text())
    verify(cases, a.before)
    if (code == 0) != (not a.before):
        raise ValueError('Unexpected test runner exit')
    for c in cases:
        assert hashlib.sha256((out/c['log']).read_bytes()).hexdigest() == c['log_sha256']
    require_source_state(source, commit)
    result = {'source_commit': commit, 'expected_failure_reproduced': a.before,
              'test_exit_code': code, 'cases': cases,
              'duration_seconds': round(time.monotonic()-start, 2),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Production OathAnkr package with synthetic mock RPC transport. No signing or broadcast in new simulation cases; no UI, simulator or live network tests.'}
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Expected before-fix failure reproduced' if a.before else 'All six provider tests pass')

if __name__ == '__main__':
    main()
