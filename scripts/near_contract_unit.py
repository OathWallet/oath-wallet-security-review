#!/usr/bin/env python3
"""Isolated upstream Rust unit replay; reports SDK aborts without counting them as passes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import tomllib
from source_state import require_source_state
from near_contract_provenance import UPSTREAM_COMMIT

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '65bc055731f6c5a9344ba3155b9685f95ebdfafe83d938cf3c5bdd10ad458046'
ABORTS = {
    'test_delete_request_panic_wrong_key': 'Request cannot be deleted immediately after creation.',
    'test_panics_delete_request': 'Request cannot be deleted immediately after creation.',
    'test_panics_on_second_confirm': 'Already confirmed this request with this key',
    'test_too_many_confirmations': 'Members list must be equal or larger than number of confirmations',
    'test_too_many_requests': 'Account has too many active requests. Confirm or delete some.',
}
UPSTREAM_TESTS = set(ABORTS) | {
    'add_key_delete_key_storage_cleared', 'test_change_num_confirmations',
    'test_delete_request_future', 'test_multi_3_of_n',
    'test_multi_add_request_and_confirm', 'test_panics_add_key_different_account',
}
PRUNED_EDGES = {'multisig2': {'near-sdk-sim', 'near-primitives-core'}, 'indexmap': {'serde'}}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity(package):
    return (package['name'], package['version'], package.get('source'))


def edges(package, packages):
    result = set()
    for dep in package.get('dependencies', []):
        parts = dep.split(' ', 2)
        candidates = [p for p in packages if p['name'] == parts[0]
                      and (len(parts) < 2 or p['version'] == parts[1])
                      and (len(parts) < 3 or p.get('source') == parts[2].strip('()'))]
        if len(candidates) != 1:
            raise ValueError('Ambiguous or absent locked dependency: ' + dep)
        result.add(identity(candidates[0]))
    return result


def verify_lock(original, adapted):
    before, after = original['package'], adapted['package']
    known = {identity(p): p for p in before}
    if len(known) != len(before) or len({identity(p) for p in after}) != len(after):
        raise ValueError('Duplicate package identity')
    pending = [identity(p) for p in before if p['name'] == 'multisig2']
    if len(pending) != 1:
        raise ValueError('Missing or ambiguous root package')
    reachable = set()
    while pending:
        key = pending.pop()
        if key in reachable:
            continue
        reachable.add(key)
        pending.extend(dep for dep in edges(known[key], before)
                       if dep[0] not in PRUNED_EDGES.get(key[0], set()))
    if {identity(p) for p in after} != reachable:
        raise ValueError('Missing or extra package in pruned dependency closure')
    changes = []
    for package in after:
        key = identity(package)
        if key not in known or package.get('checksum') != known[key].get('checksum'):
            raise ValueError('Changed package version, source or checksum')
        expected = edges(known[key], before)
        actual = edges(package, after)
        removed = expected - actual
        allowed = PRUNED_EDGES.get(package['name'], set())
        if actual - expected or {item[0] for item in removed} != allowed:
            raise ValueError('Changed dependency edge: ' + package['name'])
        if removed:
            changes.append({'package': list(key), 'removed_edges': [list(e) for e in sorted(removed)]})
    return {'original_packages': len(before), 'unit_packages': len(after),
            'retained_versions_and_checksums_match': True,
            'added_or_retargeted_edges': [], 'removed_edges': changes,
            'note': 'Removing simulation dev dependencies also prunes the indexmap serde feature edge; this is an adapted native unit harness, not the full original graph.'}


def classify(name, code, log):
    if name.startswith('tests::') and name.split('::')[-1] in ABORTS:
        message = ABORTS[name.split('::')[-1]]
        if code == -6 and message in log and 'non-unwinding panic' in log:
            return 'blocked_sdk_abort'
        return 'unexpected'
    if code == 0 and 'test result: ok. 1 passed; 0 failed; 0 ignored;' in log:
        if name == 'tests::test_panics_add_key_different_account':
            # This inherited should_panic fixture fails while constructing its key,
            # before executing the receiver restriction it purports to exercise.
            return 'invalid_fixture_pass' if 'called `Result::unwrap()` on an `Err` value' in log else 'unexpected'
        return 'passed'
    return 'unexpected'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream', type=Path)
    parser.add_argument('scratch', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cargo-home', type=Path, required=True)
    parser.add_argument('--fetch', action='store_true', help='Allow Cargo to fetch public locked dependencies before the offline build')
    args = parser.parse_args()
    upstream, scratch, out = args.upstream.resolve(), args.scratch.resolve(), args.output.resolve()
    require_source_state(upstream, UPSTREAM_COMMIT)
    if scratch.exists() or out.exists():
        raise ValueError('Use fresh scratch and output directories; preserve earlier evidence')
    (scratch/'src').mkdir(parents=True); out.mkdir(parents=True)
    original = (upstream/'multisig2/src/lib.rs').read_bytes()
    if sha(original) != SOURCE_SHA:
        raise ValueError('Wrong upstream implementation')
    overlay = (ROOT/'fixtures/near-contract-unit/audit.rs').read_bytes()
    (scratch/'src/lib.rs').write_bytes(original + b'\n' + overlay)
    manifest = (upstream/'multisig2/Cargo.toml').read_text()
    marker = '[dev-dependencies]'
    if manifest.count(marker) != 1 or '[dev-dependencies]' not in manifest:
        raise ValueError('Unexpected upstream manifest')
    (scratch/'Cargo.toml').write_text(manifest.split(marker)[0])
    (scratch/'Cargo.lock').write_bytes((upstream/'multisig2/Cargo.lock').read_bytes())
    env = {k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','LANG','LC_ALL'}}
    env.update(CARGO_HOME=str(args.cargo_home.resolve()), CARGO_TARGET_DIR=str(scratch/'build'))
    started = time.monotonic()
    versions = {name: subprocess.check_output([name,'--version'], env=env, text=True).strip()
                for name in ('rustc','cargo')}
    if any('1.96.1' not in value.split() for value in versions.values()):
        raise ValueError('This replay requires Rust and Cargo 1.96.1')
    (out/'toolchain.json').write_text(json.dumps(versions, indent=2)+'\n')
    if args.fetch:
        with (out/'fetch.log').open('w') as log:
            fetched = subprocess.run(['cargo','fetch','--manifest-path',str(scratch/'Cargo.toml')],
                                     env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        if fetched.returncode:
            raise RuntimeError('Public dependency fetch failed; log preserved')
    command = ['cargo','test','--offline','--lib','--no-run','--message-format=json',
               '--manifest-path',str(scratch/'Cargo.toml')]
    with (out/'build.jsonl').open('w') as stdout, (out/'build.log').open('w') as stderr:
        built = subprocess.run(command, env=env, stdout=stdout, stderr=stderr, timeout=600)
    if built.returncode:
        raise RuntimeError('Compilation failed; original logs preserved')
    binaries = []
    for line in (out/'build.jsonl').read_text().splitlines():
        item = json.loads(line)
        if item.get('reason') == 'compiler-artifact' and item.get('executable') and item['profile']['test']:
            binaries.append(item['executable'])
    if len(binaries) != 1:
        raise ValueError('Expected exactly one unit test binary')
    lock = verify_lock(tomllib.loads((upstream/'multisig2/Cargo.lock').read_text()),
                       tomllib.loads((scratch/'Cargo.lock').read_text()))
    for file in ('Cargo.toml','Cargo.lock','src/lib.rs'):
        target = out/'inputs'/file; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((scratch/file).read_bytes())
    command = ['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binaries[0]]
    discovery = subprocess.check_output(command+['--list'], env=env, text=True, timeout=30)
    (out/'discovery.log').write_text(discovery)
    names = [line.removesuffix(': test') for line in discovery.splitlines() if line.endswith(': test')]
    expected = {'tests::'+n for n in UPSTREAM_TESTS} | {
        'audit_contract::'+n for n in re.findall(r'#\[test\]\s+fn (\w+)',overlay.decode())}
    if set(names) != expected or len(names) != len(expected) or len(expected) != 15:
        raise ValueError('Unexpected test discovery')
    cases = []
    for name in names:
        start = time.monotonic()
        result = subprocess.run(command+[name,'--exact','--nocapture'],env=env,
                                capture_output=True, text=True, timeout=30)
        log = result.stdout + result.stderr
        filename = name.replace('::','-')+'.log'; (out/filename).write_text(log)
        cases.append({'name':name,'exit_code':result.returncode,'status':classify(name,result.returncode,log),
                      'seconds':round(time.monotonic()-start,3),'log':filename,'sha256':sha(log.encode())})
    require_source_state(upstream, UPSTREAM_COMMIT)
    report = {'upstream_commit':UPSTREAM_COMMIT, 'source_sha256':sha(original),
              'overlay_sha256':sha(overlay), 'driver_sha256':sha(Path(__file__).read_bytes()),
              'toolchain':versions,'lock':lock,'cases':cases,
              'all_contract_tests_passed':False,'wasm_execution_verified':False,
              'source_to_binary_rebuild_verified':False,'runtime_network':'denied by sandbox-exec',
              'duration_seconds':round(time.monotonic()-started,3),
              'scope':'Native contract source and SDK mock receipts; dev dependencies removed. No VM, blockchain or promise execution.',
              'files':[{'path':str(p.relative_to(out)),'sha256':sha(p.read_bytes())}
                       for p in sorted(out.rglob('*')) if p.is_file()]}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    counts = {s:sum(r['status']==s for r in cases) for s in sorted({r['status'] for r in cases})}
    print(json.dumps(counts))
    if counts != {'passed':9,'blocked_sdk_abort':5,'invalid_fixture_pass':1}:
        raise RuntimeError('Unexpected replay result; retained logs need review')
    print('Evidence collected; full contract suite and WASM execution remain incomplete')


if __name__ == '__main__':
    main()
