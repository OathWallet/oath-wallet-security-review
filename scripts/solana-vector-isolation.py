#!/usr/bin/env python3
"""Run every unchanged Squads SDK vector in a separate network-denied process."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'e46fff5686db48a40103c9dbffe5e830cfc5548a'
TEST = 'Packages/OathAnkr/Tests/OathAnkrTests/SolanaMultisigTests.swift'
FIXTURE = 'Packages/OathAnkr/Tests/OathAnkrTests/Fixtures/SolanaMultisig/sdk-vectors.json'
KINDS = {'Setup': 'setup', 'Native': 'native', 'SPL': 'spl', 'Token2022': 'token2022'}

def selectors(source):
    pattern = r'^    func (testOfficialSquads(Setup|Native|SPL|Token2022)Vector(\d{2}))\(\) throws \{ try verifyOfficialSquadsVectors\(kind: "(\w+)", index: (\d+)\) \}$'
    rows = re.findall(pattern, source, re.M)
    expected = {(label, i) for label in KINDS for i in range(19)}
    if len(rows) != 76 or {(label, int(index)) for _, label, index, _, _ in rows} != expected:
        raise ValueError('Every fixture requires one distinct test declaration')
    if any(KINDS[label] != kind or int(index) != int(argument) for _, label, index, kind, argument in rows):
        raise ValueError('Test name does not match the fixture it executes')
    return ['OathAnkrTests.SolanaMultisigTests/' + name for name, *_ in rows]

def classify(output, code, selector):
    cls, method = selector.split('/')
    names = {f'-[{cls} {method}]', cls.split('.')[-1] + '.' + method}
    events = re.findall(r"^Test Case '([^']+)' (started|passed|failed|skipped)(?:\.| \()", output, re.M)
    return 'passed' if code == 0 and len(events) == 2 and all(n in names for n, _ in events) and [v for _, v in events] == ['started', 'passed'] and ': error:' not in output else 'failed'

def assertion_body(source):
    start = source.index('            let p = try plan(row), policy =')
    end = source.index('\n        }\n    }\n    func testMainnetAndDevnet', start)
    return source[start:end]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--expected-commit', required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    source, scratch, out = a.source.resolve(), a.scratch.resolve(), a.output.resolve()
    sha = require_source_state(source, a.expected_commit)
    out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    current = (source / TEST).read_text()
    old = subprocess.check_output(['git', '-C', str(source), 'show', BASELINE + ':' + TEST], text=True)
    if assertion_body(old) != assertion_body(current): raise ValueError('Original vector assertions changed')
    raw = (source / FIXTURE).read_bytes()
    if raw != subprocess.check_output(['git', '-C', str(source), 'show', BASELINE + ':' + FIXTURE]): raise ValueError('Independent SDK vectors changed')
    changed = subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only', BASELINE, sha], text=True).splitlines()
    production_source_unchanged = changed == [TEST]
    cases = selectors(current)
    vectors = json.loads(raw)['vectors']
    if len(vectors) != 76 or any(sum(v['kind'] == kind for v in vectors) != 19 for kind in KINDS.values()): raise ValueError('Unexpected fixture inventory')
    started = time.monotonic()
    def run(name, command, timeout):
        log = out / (name + '.log'); began = time.monotonic()
        with log.open('w') as stream: code, timed_out = logged_command(command, stream=stream, env=env, timeout=timeout)
        text = log.read_text(errors='replace')
        for path, label in [(str(source),'<SOURCE>'),(str(scratch),'<SCRATCH>'),(str(out),'<OUTPUT>'),(str(Path.home()),'<HOME>')]: text = text.replace(path,label)
        log.write_text(text)
        return dict(exit_code=code, timed_out=timed_out, duration_seconds=round(time.monotonic()-began,3), log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()), text
    swift, _ = run('swift-version', ['xcrun','swift','--version'],30)
    xcode, _ = run('xcode-version', ['xcodebuild','-version'],30)
    prefix = ['--package-path', str(source/'Packages/OathAnkr'), '--build-system','native','--scratch-path',str(scratch)]
    build, _ = run('build',['swift','build',*prefix,'--force-resolved-versions','--build-tests','--jobs','4'],900)
    results = []; binary_hash = None
    if build['exit_code'] == 0 and not build['timed_out']:
        listed = subprocess.check_output(['swift','test',*prefix,'list','--skip-build','--disable-swift-testing'],env=env,text=True)
        actual = [s for s in listed.splitlines() if s.startswith('OathAnkrTests.SolanaMultisigTests/testOfficialSquads')]
        if len(actual) != 76 or set(actual) != set(cases): raise ValueError('Compiled test discovery does not cover every vector')
        directory = Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],env=env,text=True).strip())
        bundles = list(directory.glob('*.xctest'))
        if len(bundles) != 1: raise ValueError('Ambiguous test bundle')
        binary_hash = hashlib.sha256((bundles[0]/'Contents/MacOS/OathAnkrPackageTests').read_bytes()).hexdigest()
        def check(case):
            row,text = run(case.split('/')[-1], ['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',case,str(bundles[0])],120)
            row.update(selector=case,status=classify(text,row['exit_code'],case));return row
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(check,cases))
    require_source_state(source,sha)
    ok = len(results)==76 and all(r['status']=='passed' and not r['timed_out'] for r in results) and swift['exit_code']==xcode['exit_code']==0
    result=dict(check='solana-vector-isolation',source_commit=sha,baseline_commit=BASELINE,status='passed' if ok else 'failed',fixture_sha256=hashlib.sha256(raw).hexdigest(),assertion_body_sha256=hashlib.sha256(assertion_body(current).encode()).hexdigest(),test_binary_sha256=binary_hash,production_source_unchanged=production_source_unchanged,changed_paths_from_baseline=changed,build=build,toolchain={'swift':swift,'xcode':xcode},cases=results,duration_seconds=round(time.monotonic()-started,3),runtime_scope='macOS host, 76 independent SDK vectors, separate network-denied processes, same assertions and 120-second process limit; no device or blockchain')
    log=out/'solana-vector-isolation.log';log.write_text(json.dumps(result,indent=2)+'\n');result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'solana-vector-isolation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],len(results),'individual vector executions')
    raise SystemExit(0 if ok else 1)

if __name__ == '__main__': main()
