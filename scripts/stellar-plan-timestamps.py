#!/usr/bin/env python3
"""Reproduce Stellar transaction timestamp bounds in a pinned production checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from isolated_tests import classify
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
BASELINE='152e094f85f196479d2ab08856eaf3b0264cd6c1'
OVERLAY=ROOT/'fixtures/stellar-plan-timestamps/StellarPlanTimestampTests.swift'
PRODUCTION=['Packages/OathAnkr/Sources/OathAnkr/StellarSendPlan.swift','Packages/OathAnkr/Sources/OathAnkr/StellarSendXDR.swift']
METHODS=['testPersistedValidPlanKeepsSignedBytes','testOutOfRangeFiniteDatesAreRejected','testInfiniteDatesAreRejected','testNaNDateIsRejected','testDecodedOutOfRangePlanIsRejectedByPublicVerifier','testTimestampAndExpiryBoundariesRemainCompatible']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','scratch','output'):p.add_argument(n,type=Path)
    p.add_argument('--expected-commit',required=True);p.add_argument('--baseline',action='store_true')
    a=p.parse_args();source,scratch,out=[getattr(a,n).resolve() for n in ('source','scratch','output')]
    require_source_state(source,a.expected_commit)
    if a.baseline and a.expected_commit!=BASELINE:raise ValueError('Unexpected baseline')
    if scratch.exists() or out.exists():raise ValueError('Fresh scratch/output required')
    scratch.mkdir(parents=True);out.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    start=time.monotonic()
    def run(cmd,log):
        with (out/log).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
        if r.returncode:raise RuntimeError(log+' failed; original log retained')
    copy=scratch/'source'
    run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
    run(['git','-C',str(copy),'checkout','--detach',a.expected_commit],'checkout.log')
    target=copy/'Packages/OathAnkr/Tests/OathAnkrTests'/OVERLAY.name
    if target.exists() and target.read_bytes()!=OVERLAY.read_bytes():raise ValueError('Fixture mismatch')
    shutil.copyfile(OVERLAY,target)
    for cmd,log in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log')]:run(cmd,log)
    cache=(scratch/'build').resolve()
    # Never share a SwiftPM build graph between different source checkouts.
    if cache.exists():raise ValueError('Fresh build directory required')
    package=['--package-path',str(copy/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(cache)]
    run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
    binary=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
    bundles=list(binary.glob('*.xctest'))
    if len(bundles)!=1:raise ValueError('Ambiguous test bundle')
    rows=[]
    for method in METHODS:
        cmd=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.StellarPlanTimestampTests/'+method,str(bundles[0])]
        r=subprocess.run(cmd,env=env,capture_output=True,timeout=120)
        raw=r.stdout+r.stderr;log=out/(method+'.log');log.write_bytes(raw)
        rows.append({'method':method,'status':classify(raw.decode(errors='replace'),r.returncode),'exit_code':r.returncode,'log':log.name,'log_sha256':sha(log)})
    if subprocess.check_output(['git','-C',str(copy),'diff','--name-only']).strip():raise ValueError('Tracked source changed')
    require_source_state(source,a.expected_commit)
    report={'source_commit':a.expected_commit,'baseline':a.baseline,'production':[{'path':f,'source_sha256':sha(source/f),'executed_sha256':sha(copy/f)} for f in PRODUCTION],
        'overlay_sha256':sha(OVERLAY),'driver_sha256':sha(Path(__file__)),'test_executable_sha256':sha(bundles[0]/'Contents/MacOS'/bundles[0].stem),
        'methods':rows,'runtime_network':'denied by sandbox-exec','duration_seconds':round(time.monotonic()-start,3),
        'scope':'Public and JSON-decoded Stellar plans with malformed timestamps; no remote writer or funded transaction is demonstrated. Synthetic transactions only.'}
    report['files']=[{'path':f.name,'sha256':sha(f)} for f in sorted(out.iterdir()) if f.is_file()]
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    expected=[0,-5,-5,0,-5,0] if a.baseline else [0]*len(METHODS)
    if [r['exit_code'] for r in rows]!=expected or rows[0]['status']!='passed':raise RuntimeError('Unexpected results: '+str(rows))
    if any(r['status']!='passed' for r in rows if r['exit_code']==0):raise RuntimeError('Tests did not execute')
    print(json.dumps({'passed':sum(r['status']=='passed' for r in rows),'sigtrap':sum(r['exit_code']==-5 for r in rows)}))
if __name__=='__main__':main()
