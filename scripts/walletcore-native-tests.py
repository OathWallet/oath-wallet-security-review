#!/usr/bin/env python3
"""Run real upstream C/C++ suites from a verified, prepared Core checkout.

Preparation is documented in review/CORE-NATIVE-AND-EXTENDED-KEY.md. This does
not create Apple frameworks or turn native test coverage into a source review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
PIN = 'd40d24a63d92619167903369308bf0e2f7eb3a59'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prepared', type=Path)
    parser.add_argument('--app-source', type=Path, required=True)
    parser.add_argument('--app-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repair-set', choices=['api-only', 'all-seven', 'all-eight'], default='api-only',
                        help='Require exactly the selected published source patch; no arbitrary dirty checkout')
    args = parser.parse_args()
    source, out = args.prepared.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    require_source_state(args.app_source, args.app_commit)
    patch_name = {'api-only': 'walletcore-4.8.4-api-repairs.patch',
                  'all-seven': 'walletcore-4.8.4-combined-seven.patch',
                  'all-eight': 'walletcore-4.8.4-combined-eight.patch'}[args.repair_set]
    expected = (ROOT/'patches'/patch_name).read_bytes()

    def check_source():
        git = lambda *a: subprocess.check_output(['git', '-C', str(source), *a])
        if git('rev-parse', 'HEAD').decode().strip() != PIN:
            raise ValueError('Wrong upstream revision')
        if git('diff', 'HEAD', '--binary') != expected:
            raise ValueError('Expected exactly the selected published repair set')
        if git('ls-files', '--others', '--exclude-standard').strip():
            raise ValueError('Untracked source inputs present')

    check_source()
    env = {k: v for k, v in os.environ.items() if k in
           ['HOME', 'PATH', 'TMPDIR', 'LANG', 'LC_ALL', 'DEVELOPER_DIR']}
    env['TEST_TMPDIR'] = str(out/'test-temp')
    Path(env['TEST_TMPDIR']).mkdir(exist_ok=True)
    rows = []
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

    def run(command, name, timeout):
        started = time.monotonic()
        with (out/(name+'.log')).open('w') as log:
            code, expired = logged_command(command, stream=log, timeout=timeout,
                                            cwd=source, env=env)
        rows.append(dict(name=name, command=command, exit_code=code,
                         timed_out=expired, duration_seconds=round(time.monotonic()-started, 3),
                         log_sha256=digest(out/(name+'.log'))))
        (out/'commands.json').write_text(json.dumps(rows, indent=2)+'\n')
        if code or expired:
            raise RuntimeError(name+' failed; logs preserved')

    run(['cmake', '--build', 'build/native-core', '--parallel', '4'], 'build', 3600)
    original = source/'build/native-core/tests/tests'
    placed = source/'build/tests/tests'
    placed.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, placed)
    placed.chmod(0o700)
    if digest(placed) != digest(original):
        raise ValueError('Fixture-root placement changed the binary')
    run([str(placed), '--gtest_output=json:'+str(out/'cpp-results.json')], 'cpp', 1800)
    cpp = json.loads((out/'cpp-results.json').read_text())
    if cpp['tests'] != 2363 or any(cpp[k] for k in ['failures', 'errors', 'disabled']):
        raise ValueError('Unexpected full-suite result')
    trezor = source/'build/native-core/trezor-crypto/crypto/tests/TrezorCryptoTests'
    run([str(trezor)], 'trezor', 1800)
    if 'Checks: 113, Failures: 0, Errors: 0' not in (out/'trezor.log').read_text():
        raise ValueError('Unexpected C test count')
    check_source()
    require_source_state(args.app_source, args.app_commit)
    result = dict(check='upstream-native', source_commit=args.app_commit,
                  upstream_commit=PIN, status='passed', runtime_scope='native-macOS',
                  cpp={k: cpp[k] for k in ['tests', 'failures', 'errors', 'disabled', 'time']},
                  c_checks=113, c_failures=0, c_errors=0,
                  binary_sha256={'cpp': digest(placed), 'trezor': digest(trezor)},
                  patch_sha256=hashlib.sha256(expected).hexdigest(),
                  repair_set=args.repair_set,
                  log_sha256=digest(out/'cpp.log'),
                  limitations=['Prepared native build, not an Apple framework or whole-application test.',
                               'Passing suites do not establish manual source coverage or historical binary equivalence.'])
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
