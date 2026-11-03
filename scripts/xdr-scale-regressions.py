#!/usr/bin/env python3
"""Replay Stellar and Polkadot send/request regressions without network access."""
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
COMMIT = '018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0'
CLASSES = ('StellarSendTests', 'StellarMultisigTests', 'WalletConnectStellarTests', 'PolkadotSendTests', 'WalletConnectPolkadotTests')
FILTER = r'^OathAnkrTests\.(?:' + '|'.join(CLASSES) + r')/(?!testLive)'


def validate_results(rows, expected):
    names = [r['selector'] for r in rows]
    if len(names) != 40 or len(set(names)) != 40 or set(names) != set(expected):
        raise ValueError('Incomplete, duplicate or unexpected Stellar/Polkadot test selection')
    if any(r['status'] != 'passed' or r['exit_code'] != 0 for r in rows):
        raise ValueError('A selected Stellar/Polkadot method failed or skipped')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('scratch', type=Path); p.add_argument('output', type=Path)
    p.add_argument('--expected-commit', required=True)
    a = p.parse_args()
    commit = a.expected_commit
    source, scratch, out = a.source.resolve(), a.scratch.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    require_source_state(source, commit)
    env = {k: v for k, v in os.environ.items() if k in {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
    expected = []
    bindings = []
    for name in CLASSES:
        path = source / 'Packages/OathAnkr/Tests/OathAnkrTests' / (name + '.swift')
        expected.extend('OathAnkrTests.' + name + '/' + method for method in re.findall(r'func (test\w+)\(', path.read_text()) if not method.startswith('testLive'))
        bindings.append({'path': str(path.relative_to(source)), 'sha256': sha(path)})
    start = time.monotonic()
    commands = [
        (['xcodebuild', '-version'], 'xcode-version.log'),
        (['swift', '--version'], 'swift-version.log'),
        (['python3', '--version'], 'python-version.log'),
        (['swift', 'build', '--package-path', str(source / 'Packages/OathAnkr'), '--build-system', 'native',
          '--scratch-path', str(scratch), '--build-tests', '--jobs', '4'], 'build.log'),
        (['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)', 'python3',
          str(ROOT / 'scripts/isolated_tests.py'), str(source), 'OathAnkr', str(scratch), str(out),
          '--skip-build', '--filter', FILTER], 'tests.log')]
    for command, log in commands:
        with (out / log).open('w') as f:
            result = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=1200)
        if result.returncode:
            raise RuntimeError(log + ' failed; original output retained')
    rows = json.loads((out / 'OathAnkr-cases.json').read_text())
    validate_results(rows, expected)
    for row in rows:
        if sha(out / row['log']) != row['log_sha256']:
            raise ValueError('Case log digest mismatch')
    require_source_state(source, commit)
    report = {'source_commit': commit, 'selected': 40, 'passed': 40, 'skipped': 0, 'failed': 0,
              'test_sources': bindings, 'script_sha256': sha(Path(__file__)),
              'isolation_driver_sha256': sha(ROOT / 'scripts/isolated_tests.py'),
              'duration_seconds': round(time.monotonic() - start, 2),
              'runtime_network': 'denied by sandbox-exec',
              'scope': '40 adjacent production-package methods; seven opt-in live methods excluded; synthetic providers, no live providers, UI, simulator or device checks',
              'files': [{'path': str(f.relative_to(out)), 'sha256': sha(f)} for f in sorted(out.rglob('*')) if f.is_file() and f.name != 'result.json']}
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('40 selected Stellar/Polkadot methods passed; runtime network denied')


if __name__ == '__main__':
    main()
