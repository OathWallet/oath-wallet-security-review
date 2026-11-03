#!/usr/bin/env python3
"""Replay Sui/XRP history restart boundaries against a pinned public source checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from isolated_tests import classify
from source_state import require_source_state
ROOT = Path(__file__).resolve().parents[1]
BASELINE = '05e7917f0a3c26072b1a6b88d2e9e4a0d0310427'
OVERLAY = ROOT / 'fixtures/history-restart-boundaries/SuiHistoryRestartBoundaryTests.swift'
PRODUCTION = 'Packages/OathDatabase/Sources/OathDatabase/SuiLedger.swift'
SOURCES = [PRODUCTION, 'Packages/OathDatabase/Sources/OathDatabase/XrplLedger.swift', 'Packages/OathAnkr/Sources/OathAnkr/SuiDecoding.swift', 'Packages/OathAnkr/Sources/OathAnkr/SuiModels.swift']
METHODS = [
 'SuiLedgerTests/testAuditRestartRejectsOverflowFromDecodedProviderCheckpoint',
 'SuiLedgerTests/testAuditRestartAllowsLargestRepresentableSuccessor',
 'SuiLedgerTests/testAuditRestartRejectsAnotherAccountsCursor',
 'XrplLedgerTests/testAuditRestartRejectsAnotherAccountsCursor']
FAILURES = set(METHODS) - {METHODS[1]}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','scratch','output'): p.add_argument(n,type=Path)
    p.add_argument('--baseline',action='store_true');p.add_argument('--expected-commit',required=True);a=p.parse_args()
    COMMIT=a.expected_commit
    if a.baseline and COMMIT!=BASELINE:raise ValueError('Incorrect baseline')
    source,scratch,out=[getattr(a,n).resolve() for n in ('source','scratch','output')]
    require_source_state(source,COMMIT)
    if scratch.exists() or out.exists(): raise ValueError('Use fresh scratch and output paths')
    scratch.mkdir(parents=True);out.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    start=time.monotonic()
    def run(command,log):
        with (out/log).open('w') as f:
            r=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
        if r.returncode: raise RuntimeError(log+' failed; original log retained')
    copy=scratch/'source'
    run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
    run(['git','-C',str(copy),'checkout','--detach',COMMIT],'checkout.log')
    production=copy/PRODUCTION
    overlay=copy/'Packages/OathDatabase/Tests/OathDatabaseTests'/OVERLAY.name
    if overlay.exists() and overlay.read_bytes()!=OVERLAY.read_bytes():raise ValueError('Fixture mismatch')
    shutil.copyfile(OVERLAY,overlay)
    methods=METHODS
    if len(re.findall(r'func (test\w+)\(',overlay.read_text()))!=4:raise ValueError('Unexpected test selection')
    for command,log in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['python3','--version'],'python-version.log')]:run(command,log)
    package=['--package-path',str(copy/'Packages/OathDatabase'),'--build-system','native','--scratch-path',str(scratch/'build')]
    run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
    bindir=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
    bundles=list(bindir.glob('*.xctest'))
    if len(bundles)!=1:raise ValueError('Ambiguous test bundle')
    results=[]
    for method in methods:
        command=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathDatabaseTests.'+method,str(bundles[0])]
        r=subprocess.run(command,env=env,capture_output=True,timeout=120)
        raw=r.stdout+r.stderr;log=out/(method.replace('/','-')+'.log');log.write_bytes(raw)
        results.append({'method':method,'exit_code':r.returncode,'status':classify(raw.decode(errors='replace'),r.returncode),'log':log.name,'log_sha256':sha(log)})
    diff=subprocess.check_output(['git','-C',str(copy),'diff'],env=env,text=True)
    changed=subprocess.check_output(['git','-C',str(copy),'diff','--name-only'],env=env,text=True).splitlines()
    if changed:raise ValueError('Unexpected tracked source changes')
    require_source_state(source,COMMIT)
    report={'source_commit':COMMIT,'baseline':a.baseline,'source_files':[{'path':f,'source_sha256':sha(source/f),'executed_sha256':sha(copy/f)} for f in SOURCES],
            'overlay_sha256':sha(OVERLAY),'driver_sha256':sha(Path(__file__)),'isolation_classifier_sha256':sha(ROOT/'scripts/isolated_tests.py'),
            'methods':results,'runtime_network':'denied by sandbox-exec','duration_seconds':round(time.monotonic()-start,3),
            'scope':'Production Sui decoder and SQLite history cursor methods with synthetic records. Overflow baseline must terminate with SIGTRAP; account mismatch tests exercise internal database methods, not a demonstrated app-level exploit. No network, app UI or transaction broadcast.'}
    report['files']=[{'path':str(f.relative_to(out)),'sha256':sha(f)} for f in sorted(out.rglob('*')) if f.is_file()]
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    failures={r['method'] for r in results if r['status']!='passed'}
    expected=FAILURES if a.baseline else set()
    if failures!=expected or any(r['status'] not in ('passed','failed') for r in results):raise RuntimeError('Unexpected method results: '+str(results))
    if a.baseline and results[0]['exit_code'] != -5:raise RuntimeError('Expected baseline overflow trap was not reproduced')
    print(json.dumps({'passed':4-len(failures),'expected_baseline_failures':len(failures)}))
if __name__=='__main__':main()
