#!/usr/bin/env python3
"""Compile actual TWData/TWString before and after the alias repair under sanitizers.

Requires a clean pinned Core checkout and the native Rust static library built
using review/CORE-NATIVE-REPRODUCTION.md. No replacement production functions.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
PIN = 'd40d24a63d92619167903369308bf0e2f7eb3a59'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--rust-library', type=Path, required=True)
    parser.add_argument('--bindgen-header', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, library, out = args.source.resolve(), args.rust_library.resolve(), args.output.resolve()
    require_source_state(source, PIN)
    out.mkdir(parents=True, exist_ok=True)
    patch = ROOT / 'patches/walletcore-4.8.4-data-alias.patch'
    fixture = ROOT / 'tests/UpstreamDataAlias.cpp'
    header = args.bindgen_header.resolve()
    inputs = {str(p): sha(p) for p in [patch, fixture, library, header]}
    env = {k: v for k, v in os.environ.items() if k in ['HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL']}
    env['ASAN_OPTIONS'] = 'detect_leaks=0:abort_on_error=0:symbolize=1'
    env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
    commands, cases = [], []
    started = time.monotonic()
    def run(command, name, required=True, cwd=None):
        log = out / (name + '.log')
        with log.open('w') as stream:
            code, timeout = logged_command(command, stream=stream, timeout=180, env=env, cwd=cwd)
        commands.append(dict(name=name, command=command, exit_code=code, timed_out=timeout, log_sha256=sha(log)))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if required and (code or timeout):
            raise RuntimeError(name + ' failed; logs preserved')
        return code, timeout, log.read_text()
    with tempfile.TemporaryDirectory(prefix='oath-data-alias-') as directory:
        work = Path(directory)
        (work / 'src/interface').mkdir(parents=True)
        (work / 'generated/rust/bindgen').mkdir(parents=True)
        (work / 'generated/rust/bindgen/WalletCoreRSBindgen.h').write_bytes(header.read_bytes())
        target = work / 'src/interface/TWData.cpp'
        target.write_bytes((source / 'src/interface/TWData.cpp').read_bytes())
        flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer']
        memzero = work / 'memzero.o'
        run(['clang'] + flags + ['-c', str(source / 'trezor-crypto/crypto/memzero.c'), '-o', str(memzero)], 'memzero-compile')
        includes = [part for path in ['include', 'src', 'trezor-crypto/include', 'trezor-crypto/crypto'] for part in ['-I', str(source / path)]]
        includes += ['-I', str(work / 'generated'), '-I', str(work / 'generated/rust')]
        for stage in ['before', 'after']:
            if stage == 'after':
                run(['git', 'apply', str(patch)], 'apply', cwd=work)
            binary = work / stage
            source_hash = sha(target)
            run(['clang++', '-std=c++20'] + flags + includes + ['-Wl,-dead_strip', str(fixture), str(target), str(source / 'src/interface/TWString.cpp'), str(memzero), str(library), '-framework', 'Security', '-framework', 'CoreFoundation', '-lresolv', '-liconv', '-o', str(binary)], stage + '-compile')
            for mode, count in [('self', 1), ('alias', 1), ('controls', 792), ('properties', 5018)]:
                code, timeout, log = run([str(binary), mode], stage + '-' + mode, required=False)
                expected_failure = stage == 'before' and mode != 'controls'
                observed = (code != 0 and 'AddressSanitizer: heap-use-after-free' in log) if expected_failure else (code == 0 and log.strip().endswith(f'DATA_ALIAS_CHECKS mode={mode} checks={count} failures=0'))
                cases.append(dict(stage=stage, mode=mode, source_sha256=source_hash, exit_code=code, timed_out=timeout, expected_outcome_observed=observed and not timeout))
    require_source_state(source, PIN)
    if any(sha(Path(p)) != h for p, h in inputs.items()):
        raise RuntimeError('Input changed during execution')
    passed = all(row['expected_outcome_observed'] for row in cases)
    result = dict(check='upstream-data-alias', status='passed' if passed else 'failed', upstream_commit=PIN, cases=cases, input_hashes=inputs, compiler=subprocess.check_output(['clang++', '--version'], text=True), duration_seconds=round(time.monotonic()-started, 3), limitations=['Host ASan/UBSan test of production translation units, not application runtime.', 'No reachable Oath call to either append API established.', 'LeakSanitizer disabled; this is not a leak or full memory-hygiene proof.', 'Rust library identity recorded, not independently rebuilt by this runner.'])
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
