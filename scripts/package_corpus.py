#!/usr/bin/env python3
"""Run each production Swift package fixture in its own network-denied XCTest process."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import tarfile
import tempfile
import time
from bounded_process import logged_command
from source_state import require_source_state

SWIFTDRAW = '82699f4bdf2f075793cfa0d392eb27c59b41a3fe'
ROOT = Path(__file__).resolve().parents[1]
def run(*, check, base, suite, cases, outcome, scope, package='OathTokenImages',
        local_dependencies=('OathDiagnostics',), pins=None, overlay=None):
    pins = {'SwiftDraw': SWIFTDRAW} if pins is None else pins
    pkg = 'Packages/' + package
    fixture_path = f"{pkg}/Tests/{package}Tests/{suite.split('.')[-1]}.swift"
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--expected-commit')
    args=parser.parse_args()
    source=args.source.resolve()
    sha=require_source_state(source,args.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    fixture = overlay.read_bytes() if overlay else (source/fixture_path).read_bytes()
    if not overlay:
        assert fixture==subprocess.check_output(['git','-C',source,'show',base+':'+fixture_path])
    assert set(re.findall(rb'func (test\w+)\(',fixture))=={case.encode() for case in cases}
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();rows=[]
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    for phase,rev in [('before',base),('after',sha)]:
        archive=subprocess.check_output(['git','-C',source,'archive',rev,pkg,*['Packages/'+name for name in local_dependencies]])
        with tempfile.TemporaryDirectory(prefix='oath-package-review-') as tmp:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(tmp,filter='data')
            if overlay:
                # Both revisions receive identical audit-owned tests; never replace a shipped file.
                with (Path(tmp)/fixture_path).open('xb') as stream: stream.write(fixture)
            scratch=args.scratch.resolve()/phase
            prefix=['swift','build','--package-path',str(Path(tmp)/pkg),'--scratch-path',str(scratch),'--build-system','native','--force-resolved-versions']
            with (out/(phase+'-build.log')).open('w') as stream:
                code,expired=logged_command(prefix+['--build-tests','--jobs','4'],stream=stream,env=env,timeout=600)
            if code or expired: raise ValueError('Pinned package build failed: '+phase)
            for name, revision in pins.items():
                assert subprocess.check_output(['git','-C',scratch/'checkouts'/name,'rev-parse','HEAD'],text=True).strip()==revision
            binary=Path(subprocess.check_output(prefix+['--show-bin-path'],env=env,text=True).strip())
            bundles=list(binary.glob('*.xctest'));assert len(bundles)==1
            for case in cases:
                log=out/(phase+'-'+case+'.log')
                command=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',suite+'/'+case,str(bundles[0])]
                with log.open('w') as stream:
                    code,expired=logged_command(command,stream=stream,env=env,timeout=45)
                status='failed' if expired else outcome(log.read_text(errors='replace'),code,case,phase=='before')
                rows.append(dict(phase=phase,case=case,source_commit=rev,status=status,exit_code=code,timed_out=expired,log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
                print(phase,case,status,flush=True)
    require_source_state(source,sha)
    ok=len(rows)==2*len(cases) and all(x['status']!='failed' for x in rows)
    result=dict(check=check,source_commit=sha,baseline_commit=base,dependency_commits=pins,
                fixture_sha256=hashlib.sha256(fixture).hexdigest(),status='passed' if ok else 'failed',executions=rows,
                duration_seconds=round(time.monotonic()-start,3),scope=scope)
    if 'SwiftDraw' in pins: result['swiftdraw_commit'] = pins['SwiftDraw']
    log=out/(check+'.log');log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/(check+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    return 0 if ok else 1
