#!/usr/bin/env python3
"""Build a fresh pinned checkout and replay offline Stellar persistence and refresh regressions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from isolated_tests import classify
from source_state import require_source_state
SUITES = ('StellarLedgerTests', 'StellarSendJournalTests', 'WalletConnectStellarJournalTests', 'PostSendBalanceRefreshTests')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'scratch', 'output'): p.add_argument(name, type=Path)
    p.add_argument('--expected-commit', required=True)
    a = p.parse_args(); COMMIT = a.expected_commit; original = a.source.resolve(); source = original; out = a.output.resolve()
    require_source_state(source, COMMIT)
    scratch = a.scratch.resolve()
    if scratch.exists() or out.exists(): raise ValueError('Fresh scratch/output required')
    scratch.mkdir(parents=True); out.mkdir(parents=True)
    started = time.monotonic()
    env = {k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    source = scratch/'source'
    for command,name in [(['git','clone','--shared','--no-checkout',str(original),str(source)],'clone.log'), (['git','-C',str(source),'checkout','--detach',COMMIT],'checkout.log')]:
        with (out/name).open('w') as f:
            subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    require_source_state(source,COMMIT)
    prefix = ['--package-path', str(source/'Packages/OathDatabase'), '--build-system', 'native', '--scratch-path', str(scratch/'build')]
    commands = [(['xcodebuild','-version'],'xcode-version.log'), (['swift','--version'],'swift-version.log'), (['python3','--version'],'python-version.log'), (['swift','build',*prefix,'--build-tests','--jobs','4'],'build.log')]
    for command, name in commands:
        with (out/name).open('w') as f:
            result = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=1800)
        if result.returncode: raise RuntimeError(name+' failed; log retained')
    bindir = Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'], env=env, text=True).strip())
    bundles = list(bindir.glob('*.xctest'))
    if len(bundles) != 1: raise ValueError('Ambiguous test bundle')
    executable = bundles[0]/'Contents/MacOS'/bundles[0].stem
    methods = []; fixtures = []; excluded = []
    for suite in SUITES:
        path = source/'Packages/OathDatabase/Tests/OathDatabaseTests'/(suite+'.swift')
        fixtures.append({'path':str(path.relative_to(source)), 'sha256':digest(path.read_bytes())})
        for name in re.findall(r'func (test\w+)\(', path.read_text()):
            (excluded if name.startswith('testLive') else methods).append(suite+'/'+name)
    if len(methods) != 31 or len(set(methods)) != 31 or len(excluded) != 1: raise ValueError('Unexpected test selection')
    rows = []
    for method in methods:
        command = ['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathDatabaseTests.'+method,str(bundles[0])]
        result = subprocess.run(command, env=env, capture_output=True, timeout=120)
        raw = result.stdout+result.stderr; name = method.replace('/','-')+'.log'; (out/name).write_bytes(raw)
        rows.append({'method':method,'status':classify(raw.decode(errors='replace'),result.returncode),'exit_code':result.returncode,'log':name,'log_sha256':digest(raw)})
    require_source_state(source, COMMIT)
    report = {'source_commit':COMMIT,'methods':rows,'source_fixtures':fixtures,'excluded_live_methods':excluded,'driver_sha256':digest(Path(__file__).read_bytes()),'classifier_sha256':digest(Path(__file__).with_name('isolated_tests.py').read_bytes()),'test_executable_sha256':digest(executable.read_bytes()),'runtime_network':'denied by sandbox-exec','duration_seconds':round(time.monotonic()-started,3),'build_requirement':'Fresh source checkout and SwiftPM build per run. Stellar persistence and separate generic worker tests; no app UI, provider endpoint, or end-to-end Stellar worker test.'}
    require_source_state(original, COMMIT)
    report['production'] = [{'path':str(p.relative_to(source)),'sha256':digest(p.read_bytes())} for p in [source/'Packages/OathDatabase/Sources/OathDatabase'/name for name in ('StellarLedger.swift','StellarSend.swift','StellarSynchronizer.swift','PostSendBalanceRefresh.swift','WalletConnectStellarJournal.swift')]]
    report['files'] = [{'path':f.name,'sha256':digest(f.read_bytes())} for f in sorted(out.iterdir()) if f.is_file()]
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    failed = [row for row in rows if row['status'] != 'passed']
    print(json.dumps({'passed':len(rows)-len(failed),'failed':len(failed),'excluded_live':len(excluded)}))
    if failed: raise SystemExit(1)
if __name__ == '__main__': main()
