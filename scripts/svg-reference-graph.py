#!/usr/bin/env python3
"""Run each production artwork decoder fixture in its own network-denied XCTest process."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import tarfile
import tempfile
import time
from bounded_process import logged_command
from source_state import require_source_state

BASE = '34ba87a3e0b2beb27bd1acdb618e480f5faefb9d'
SWIFTDRAW = '82699f4bdf2f075793cfa0d392eb27c59b41a3fe'
ROOT = Path(__file__).resolve().parents[1]
PKG = 'Packages/OathTokenImages'
SUITE = 'OathTokenImagesTests.ArtworkReferenceDepthTests'
FIXTURE = PKG+'/Tests/OathTokenImagesTests/ArtworkReferenceDepthTests.swift'
CRASH = 'testShadowedCycleCannotReachRenderer'
OVER = 'testSharedLeafFirstCannotBypassDepthBudget'
CASES = [OVER,CRASH,'testSharedRootFirstCannotBypassDepthBudget','testExactlyAtDepthBudgetInBothOrders','testSiblingReferencesMayShareOneID']

def outcome(text, code, case, before):
    name = '-['+SUITE+' '+case+']'
    events = re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors = [line for line in text.splitlines() if ': error:' in line]
    if case not in CASES: return 'failed'
    if before and case == CRASH:
        return 'expected-signal-11' if code==-signal.SIGSEGV and events==[(name,'started')] and not errors else 'failed'
    if before and case == OVER:
        suffix = name+' : XCTAssertThrowsError failed: did not throw an error - Over-budget SVG must be rejected before rendering'
        ok = code==1 and events==[(name,'started'),(name,'failed')] and len(errors)==1 and errors[0].endswith(suffix)
        return 'expected-depth-assertion' if ok else 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--expected-commit')
    args=parser.parse_args()
    source=args.source.resolve()
    sha=require_source_state(source,args.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    fixture=(source/FIXTURE).read_bytes()
    assert fixture==subprocess.check_output(['git','-C',source,'show',BASE+':'+FIXTURE])
    assert set(re.findall(rb'func (test\w+)\(',fixture))=={case.encode() for case in CASES}
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();rows=[]
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    for phase,rev in [('before',BASE),('after',sha)]:
        archive=subprocess.check_output(['git','-C',source,'archive',rev,PKG,'Packages/OathDiagnostics'])
        with tempfile.TemporaryDirectory(prefix='oath-svg-graph-') as tmp:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(tmp,filter='data')
            scratch=args.scratch.resolve()/phase
            prefix=['swift','build','--package-path',str(Path(tmp)/PKG),'--scratch-path',str(scratch),'--build-system','native','--force-resolved-versions']
            with (out/(phase+'-build.log')).open('w') as stream:
                code,expired=logged_command(prefix+['--build-tests','--jobs','4'],stream=stream,env=env,timeout=600)
            if code or expired: raise ValueError('Pinned package build failed: '+phase)
            assert subprocess.check_output(['git','-C',scratch/'checkouts/SwiftDraw','rev-parse','HEAD'],text=True).strip()==SWIFTDRAW
            binary=Path(subprocess.check_output(prefix+['--show-bin-path'],env=env,text=True).strip())
            bundles=list(binary.glob('*.xctest'));assert len(bundles)==1
            for case in CASES:
                log=out/(phase+'-'+case+'.log')
                command=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',SUITE+'/'+case,str(bundles[0])]
                with log.open('w') as stream:
                    code,expired=logged_command(command,stream=stream,env=env,timeout=45)
                status='failed' if expired else outcome(log.read_text(errors='replace'),code,case,phase=='before')
                rows.append(dict(phase=phase,case=case,source_commit=rev,status=status,exit_code=code,timed_out=expired,log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
                print(phase,case,status,flush=True)
    require_source_state(source,sha)
    ok=len(rows)==10 and all(x['status']!='failed' for x in rows)
    result=dict(check='svg-reference-graph',source_commit=sha,baseline_commit=BASE,swiftdraw_commit=SWIFTDRAW,
                fixture_sha256=hashlib.sha256(fixture).hexdigest(),status='passed' if ok else 'failed',executions=rows,
                duration_seconds=round(time.monotonic()-start,3),scope='Production token decoder and pinned drawing dependency; five synthetic images/cases per revision. Separate offline host XCTest process per case.')
    log=out/'svg-reference-graph.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'svg-reference-graph.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0 if ok else 1

if __name__=='__main__': raise SystemExit(main())
