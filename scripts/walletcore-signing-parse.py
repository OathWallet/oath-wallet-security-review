#!/usr/bin/env python3
"""Rebuild paired production C API signing tests in a disposable Core checkout.

Requires exactly the eight-repair diff and the documented prepared native build.
Temporarily reverses only the eighth repair, rebuilds and runs the same fixture,
then reapplies it and rebuilds. Do not share this checkout with another build.
Evidence is retained on failure; source restoration runs in finally.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from bounded_process import logged_command

ROOT = Path(__file__).resolve().parents[1]
PIN = 'd40d24a63d92619167903369308bf0e2f7eb3a59'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prepared', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    source, out = a.prepared.resolve(), a.output.resolve()
    patch = ROOT/'patches/walletcore-4.8.4-signing-parse.patch'
    fixture = ROOT/'tests/UpstreamSigningParse.cpp'
    seven = (ROOT/'patches/walletcore-4.8.4-combined-seven.patch').read_bytes()
    eight = (ROOT/'patches/walletcore-4.8.4-combined-eight.patch').read_bytes()
    def check(expected):
        git = lambda *args: subprocess.check_output(['git', '-C', str(source), *args])
        if git('rev-parse', 'HEAD').decode().strip() != PIN or git('diff', 'HEAD', '--binary') != expected:
            raise ValueError('Unexpected source identity or repair diff')
        if git('ls-files', '--others', '--exclude-standard').strip():
            raise ValueError('Unexpected untracked inputs')
    check(eight)
    out.mkdir(parents=True, exist_ok=False)
    commands, cases = [], []
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR']}
    inputs = {str(p): sha(p) for p in [patch, fixture]}
    def run(command, name, required=True):
        started = time.monotonic()
        log = out/(name+'.log')
        with log.open('w') as stream:
            code, timed_out = logged_command(command, stream=stream, timeout=1800, cwd=source, env=env)
        commands.append(dict(name=name, command=command, exit_code=code, timed_out=timed_out,
                             duration_seconds=round(time.monotonic()-started,3), log_sha256=sha(log)))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        print(name, code, flush=True)
        if required and (code or timed_out):
            raise RuntimeError(name+' failed; evidence retained')
        return code, timed_out, log.read_text()
    original = (source/'src/CoinEntry.h').read_bytes()
    try:
        run(['git','apply','--reverse',str(patch)], 'reverse-eighth-repair')
        for stage, expected, failures in [('before', seven, 12), ('after', eight, 0)]:
            if stage == 'after':
                run(['git','apply',str(patch)], 'apply-eighth-repair')
            check(expected)
            run(['cmake','--build','build/native-core','--target','TrustWalletCore','--parallel','4'],stage+'-build')
            binary = out/(stage+'-fixture')
            libraries = [source/p for p in ['build/native-core/libTrustWalletCore.a',
                'build/native-core/trezor-crypto/libTrezorCrypto.a',
                'rust/target/release/libwallet_core_rs.a','build/native-core/libprotobuf.a']]
            command = ['clang++','-std=c++20','-O2','-DNDEBUG','-Iinclude','-Isrc',
                '-Ibuild/local/include','-I/opt/homebrew/opt/boost/include',str(fixture)]
            run(command+[str(p) for p in libraries]+['-o',str(binary)],stage+'-compile')
            code, expired, text = run([str(binary)],stage,required=False)
            lines = text.strip().splitlines()
            observed = (code == (1 if failures else 0) and not expired and len(lines) == 19 and
                lines[-1] == f'checks=18 failures={failures}' and
                sum(line.endswith('passed=0') for line in lines[:-1]) == failures)
            cases.append(dict(stage=stage, expected_outcome_observed=observed,
                fixture_binary_sha256=sha(binary), source_header_sha256=sha(source/'src/CoinEntry.h'),
                patch_sha256=hashlib.sha256(expected).hexdigest(),
                library_sha256={str(p.relative_to(source)):sha(p) for p in libraries},
                checks=18, expected_failures=failures, exit_code=code, timed_out=expired))
            check(expected)
    finally:
        (source/'src/CoinEntry.h').write_bytes(original)
    check(eight)
    if any(sha(Path(p)) != h for p,h in inputs.items()):
        raise ValueError('Fixture or patch changed during execution')
    status = 'passed' if len(cases)==2 and all(r['expected_outcome_observed'] for r in cases) else 'failed'
    result = dict(status=status, upstream_commit=PIN, cases=cases, input_hashes=inputs,
        limitations=['Real TWAnySignerSign/Plan calls; synthetic keys, fake UTXO, no broadcast.',
          'Optimized macOS native build; not a sanitizer, app runtime or Apple framework test.',
          'Only three entry paths tested; other chains and greater-than-INT_MAX inputs not executed.',
          'No tracked Oath AnySigner call site established; no reachable application exploit demonstrated.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if status == 'passed' else 1

if __name__ == '__main__':
    raise SystemExit(main())
