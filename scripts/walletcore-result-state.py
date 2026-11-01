#!/usr/bin/env python3
"""Paired production Rust-result wrapper transition tests; no mocked FFI."""
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
    a = parser.parse_args()
    source, library, header, out = [p.resolve() for p in [a.source, a.rust_library, a.bindgen_header, a.output]]
    require_source_state(source, PIN)
    out.mkdir(parents=True, exist_ok=True)
    patch, fixture = ROOT/'patches/walletcore-4.8.4-result-state.patch', ROOT/'tests/UpstreamResultState.cpp'
    hashes = {str(p): sha(p) for p in [patch, fixture, library, header]}
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    env.update(ASAN_OPTIONS='detect_leaks=0:abort_on_error=0', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    commands, cases = [], []
    started = time.monotonic()
    def run(command, name, required=True, cwd=None):
        log = out/(name+'.log')
        with log.open('w') as stream:
            code, timeout = logged_command(command, stream=stream, timeout=180, env=env, cwd=cwd)
        commands.append(dict(name=name, command=command, exit_code=code, timed_out=timeout, log_sha256=sha(log)))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if required and (code or timeout):
            raise RuntimeError(name+' failed; logs retained')
        return code, timeout, log.read_text()
    with tempfile.TemporaryDirectory(prefix='oath-result-state-') as directory:
        work = Path(directory)
        (work/'src/rust/bindgen').mkdir(parents=True)
        (work/'src/Data.h').write_bytes((source/'src/Data.h').read_bytes())
        (work/'src/rust/bindgen/WalletCoreRSBindgen.h').write_bytes(header.read_bytes())
        target = work/'src/rust/Wrapper.h'
        target.write_bytes((source/'src/rust/Wrapper.h').read_bytes())
        for stage in ['before','after']:
            if stage == 'after':
                run(['git','apply',str(patch)], 'apply', cwd=work)
            binary = work/stage
            cmd = ['clang++','-std=c++20','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(work/'src'),'-I',str(source/'src'),'-I',str(source/'include'),'-Wl,-dead_strip',str(fixture),str(library),'-framework','Security','-framework','CoreFoundation','-lresolv','-liconv','-o',str(binary)]
            run(cmd, stage+'-compile')
            code, timeout, text = run([str(binary)], stage, required=False)
            failures = 4000 if stage == 'before' else 0
            expected = code == (1 if failures else 0) and not timeout and text.strip() == f'RESULT_STATE_CHECKS total=8000 failures={failures}'
            cases.append(dict(stage=stage, source_sha256=sha(target), exit_code=code, timed_out=timeout, expected_outcome_observed=expected))
    require_source_state(source, PIN)
    if any(sha(Path(p)) != h for p,h in hashes.items()):
        raise RuntimeError('Inputs changed during execution')
    status = 'passed' if all(row['expected_outcome_observed'] for row in cases) else 'failed'
    result = dict(check='upstream-result-state', status=status, upstream_commit=PIN, cases=cases, input_hashes=hashes, compiler=subprocess.check_output(['clang++','--version'],text=True), duration_seconds=round(time.monotonic()-started,3), limitations=['Production C++ header and real Rust decode_hex implementation; no FFI substitution.', 'Repeated synthetic transition corpus, not 8000 distinct cryptographic vectors.', 'No reassignment use found in scoped application/Core call sites; reachable Oath exploit not established.', 'ASan/UBSan C++ host test; Rust archive not sanitizer-instrumented; leak detection disabled.', 'Generated header and Rust library recorded by hash, not rebuilt by this runner.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if status == 'passed' else 1

if __name__ == '__main__':
    raise SystemExit(main())
