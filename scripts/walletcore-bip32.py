#!/usr/bin/env python3
"""Exercise pinned upstream derivation C, separate from unused API hazards."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from bip32_vectors import generate
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
PIN = 'd40d24a63d92619167903369308bf0e2f7eb3a59'
SUMMARY = 'BIP32_OK official=52 independent_hardened=1920 public_private_pairs=33 malformed_calls=20000 unsupported_child_unchanged=2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--app-source', required=True, type=Path)
    parser.add_argument('--app-commit', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source, app, out = args.source.resolve(), args.app_source.resolve(), args.output.resolve()
    require_source_state(source, PIN)
    require_source_state(app, args.app_commit)
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    env = {k:v for k,v in os.environ.items() if k in ['HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL']}
    env.update(UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1', ASAN_OPTIONS='halt_on_error=1:detect_leaks=0')
    cmake = source / 'trezor-crypto/CMakeLists.txt'
    declaration = re.sub(r'#[^\n]*', '', cmake.read_text()).split('add_library(TrezorCrypto', 1)[1].split(')', 1)[0]
    relative = re.findall(r'crypto/[\w/.-]+\.c', declaration)
    if len(relative) != 61 or len(set(relative)) != 61:
        raise ValueError('Pinned Trezor source list changed')
    sources = [source / 'trezor-crypto' / p for p in relative]
    fixture = ROOT / 'tests/UpstreamBIP32.c'
    vectors = ROOT / 'tests/fixtures/slip10-vectors.json'
    official = json.loads(vectors.read_text())
    commands = []
    def run(command, name, timeout=120):
        with (out / (name+'.log')).open('w') as log:
            code, timed_out = logged_command(command, stream=log, timeout=timeout, env=env)
        result = dict(name=name, command=command, exit_code=code, timed_out=timed_out)
        return result

    with tempfile.TemporaryDirectory(prefix='oath-bip32-') as tmp:
        work = Path(tmp)
        counts = generate(official['rows'], work)
        if counts != dict(official=52, independent_hardened=1920, oracle_anchors=33):
            raise ValueError('Vector coverage changed')
        (out/'oracle-vectors.json').write_bytes((work/'oracle-vectors.json').read_bytes())
        flags = ['clang', '-std=c11', '-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', str(source/'trezor-crypto/include'), '-I', str(work)]
        def compile_one(pair):
            i, path = pair
            return run(flags+['-c', str(path), '-o', str(work/f'{i}.o')], f'compile-{i:02}')
        with ThreadPoolExecutor(max_workers=6) as pool:
            commands.extend(pool.map(compile_one, enumerate(sources)))
        if any(r['exit_code'] for r in commands):
            (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
            raise RuntimeError('Upstream compilation failed; retained logs')
        commands.append(run(['ar', 'rcs', str(work/'libtrezor.a')]+[str(work/f'{i}.o') for i in range(61)], 'archive'))
        commands.append(run(flags+[str(fixture), str(work/'libtrezor.a'), '-o', str(work/'derivation')], 'link'))
        if any(r['exit_code'] for r in commands):
            (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
            raise RuntimeError('Upstream link failed; retained logs')
        positive = run([str(work/'derivation')], 'positive', 180)
        commands.append(positive)
        positive_passed = positive['exit_code'] == 0 and (out/'positive.log').read_text().strip() == SUMMARY
        hazards = []
        for mode, diagnostic in [('unknown-curve', "member access within null pointer of type 'const curve_info'"), ('nano-public', 'any!=0')]:
            result = run([str(work/'derivation'), mode], mode)
            commands.append(result)
            observed = result['exit_code'] != 0 and not result['timed_out'] and diagnostic in (out/(mode+'.log')).read_text()
            hazards.append(dict(api_case=mode, reproduced=observed, fixed=False, exit_code=result['exit_code'], reachable_oath_vulnerability_established=False))
        (out/'api-characterizations.json').write_text(json.dumps(hazards, indent=2)+'\n')
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    inputs = [cmake]+sources+list((source/'trezor-crypto/include').rglob('*.h'))
    inputs = [p for p in inputs if not any(part.startswith('._') for part in p.parts)]
    hashes = {str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    result = dict(check='upstream-bip32', source_commit=args.app_commit, upstream_commit=PIN,
                  status='passed' if positive_passed and all(h['reproduced'] for h in hazards) else 'failed',
                  positive_derivation_tests_passed=positive_passed, api_hazards_unrepaired=hazards,
                  counts=counts, duration_seconds=round(time.monotonic()-started, 3),
                  compiler=subprocess.check_output(['clang','--version'],text=True),
                  input_hashes=hashes, fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  vectors_sha256=hashlib.sha256(vectors.read_bytes()).hexdigest(),
                  log_sha256=hashlib.sha256((out/'positive.log').read_bytes()).hexdigest(),
                  limitations=['Host source tests, not shipped binary equivalence.', 'Expected failing API characterizations are not fixes.', 'Compiled files are not automatically marked reviewed.'])
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(SUMMARY if positive_passed else 'BIP32_POSITIVE_TEST_FAILED')
    print('Unrepaired API hazards reproduced:', sum(h['reproduced'] for h in hazards))
    return 0 if result['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
