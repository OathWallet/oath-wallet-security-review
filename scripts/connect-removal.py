#!/usr/bin/env python3
"""Replay removal guards and the compatibility correction on pinned public commits."""
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

PINS = {'before':'31178e42e40d67218c2b52eda0024a5b4224f376',
        'compatibility':'610f2fbcfa1b9a08bf9cfd9b439247324bf5366a',
        'after':'0e91ce56f91ef56b3e45629967e01e449be0052f'}
FAILURES = {'testEveryJournalPendingStateBlocksOnlyItsWallet', 'testSignedXrplRemovalAndPurgeAreBlocked'}
CONTROLS = {'testTerminalJournalStatesPermitRemoval', 'testResetStillErasesPendingJournalAndRejectsLateWrites'}
COMPAT = 'testPreviouslyRemovedJournalsKeepRetentionCleanupReachable'

def verify(cases, phase):
    expected = {COMPAT} if phase == 'compatibility' else FAILURES | CONTROLS | ({COMPAT} if phase == 'after' else set())
    names = [c['selector'].split('/')[-1] for c in cases]
    if len(cases) != len(expected) or set(names) != expected:
        raise ValueError('Missing, duplicate or unexpected test method')
    for case, name in zip(cases, names):
        failed = phase == 'compatibility' or (phase == 'before' and name in FAILURES)
        status = 'failed' if failed else 'passed'
        if case['status'] != status or (case['exit_code'] == 0) != (not failed):
            raise ValueError('Unexpected result for ' + name)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('scratch', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--phase', choices=sorted(PINS), required=True)
    a = p.parse_args()
    commit = PINS[a.phase]
    source, out = a.source.resolve(), a.output.resolve()
    require_source_state(source, commit)
    out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in
           ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL']}
    start = time.monotonic()
    command = [sys.executable, str(Path(__file__).with_name('isolated_tests.py')),
               str(source), 'OathDatabase', str(a.scratch.resolve()), str(out),
               '--filter', COMPAT if a.phase == 'compatibility' else 'WalletConnectRemovalGuardTests']
    with (out/'driver.log').open('w') as stream:
        code = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT).returncode
    cases = json.loads((out/'OathDatabase-cases.json').read_text())
    verify(cases, a.phase)
    if (code == 0) != (a.phase == 'after'):
        raise ValueError('Unexpected test runner exit')
    for c in cases:
        assert hashlib.sha256((out/c['log']).read_bytes()).hexdigest() == c['log_sha256']
    require_source_state(source, commit)
    result = {'source_commit': commit, 'phase': a.phase, 'expected_failure_reproduced': a.phase != 'after',
              'test_exit_code': code, 'cases': cases,
              'duration_seconds': round(time.monotonic()-start, 2),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Actual migrated database and removal methods; XRP case uses a signed synthetic transaction, seven-chain matrix uses schema-only synthetic journal rows. No provider, UI, simulator or live network tests.'}
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Expected failure reproduced' if a.phase != 'after' else 'All five removal methods pass')

if __name__ == '__main__':
    main()
