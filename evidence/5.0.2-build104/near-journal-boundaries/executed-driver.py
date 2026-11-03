#!/usr/bin/env python3
"""Replay existing NEAR journal and wallet-removal guards with runtime network denied."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '0614556b993f85808b13e3a69984ce36050a8dfe'
CLASSES = ('WalletConnectNearJournalTests', 'WalletConnectRemovalGuardTests')
FILTER = r'^OathDatabaseTests\.(?:' + '|'.join(CLASSES) + r')/'


def validate_results(rows, expected):
    names = [r['selector'] for r in rows]
    if len(names) != 8 or len(set(names)) != 8 or set(names) != set(expected):
        raise ValueError('Incomplete, duplicate or unexpected NEAR test selection')
    if any(r['status'] != 'passed' or r['exit_code'] != 0 for r in rows):
        raise ValueError('A selected NEAR method failed or skipped')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('scratch', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args()
    source, scratch, out = a.source.resolve(), a.scratch.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    require_source_state(source, COMMIT)
    env = {k: v for k, v in os.environ.items() if k in {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
    expected = []
    bindings = []
    for name in CLASSES:
        path = source / 'Packages/OathDatabase/Tests/OathDatabaseTests' / (name + '.swift')
        expected.extend('OathDatabaseTests.' + name + '/' + method for method in re.findall(r'func (test\w+)\(', path.read_text()))
        bindings.append({'path': str(path.relative_to(source)), 'sha256': sha(path)})
    start = time.monotonic()
    commands = [
        (['xcodebuild', '-version'], 'xcode-version.log'),
        (['swift', '--version'], 'swift-version.log'),
        (['python3', '--version'], 'python-version.log'),
        (['swift', 'build', '--package-path', str(source / 'Packages/OathDatabase'), '--build-system', 'native',
          '--scratch-path', str(scratch), '--build-tests', '--jobs', '4'], 'build.log'),
        (['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)', 'python3',
          str(ROOT / 'scripts/isolated_tests.py'), str(source), 'OathDatabase', str(scratch), str(out),
          '--skip-build', '--filter', FILTER], 'tests.log')]
    for command, log in commands:
        with (out / log).open('w') as f:
            result = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=1200)
        if result.returncode:
            raise RuntimeError(log + ' failed; original output retained')
    rows = json.loads((out / 'OathDatabase-cases.json').read_text())
    validate_results(rows, expected)
    for row in rows:
        if sha(out / row['log']) != row['log_sha256']:
            raise ValueError('Case log digest mismatch')
    require_source_state(source, COMMIT)
    report = {'source_commit': COMMIT, 'selected': 8, 'passed': 8, 'skipped': 0, 'failed': 0,
              'test_sources': bindings, 'script_sha256': sha(Path(__file__)),
              'isolation_driver_sha256': sha(ROOT / 'scripts/isolated_tests.py'),
              'duration_seconds': round(time.monotonic() - start, 2),
              'runtime_network': 'denied by sandbox-exec',
              'scope': 'Existing production database tests; NEAR signed journals plus all-chain removal SQL fixtures. No live provider, UI, simulator or device checks',
              'files': [{'path': str(f.relative_to(out)), 'sha256': sha(f)} for f in sorted(out.rglob('*')) if f.is_file() and f.name != 'result.json']}
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('8 selected NEAR methods passed; runtime network denied')


if __name__ == '__main__':
    main()
