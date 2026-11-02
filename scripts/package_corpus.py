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
        local_dependencies=('OathDiagnostics',), pins=None, overlay=None, compare=True, case_suites=None):
    pins = {'SwiftDraw': SWIFTDRAW} if pins is None else pins
    pkg = 'Packages/' + package
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--expected-commit')
    args=parser.parse_args()
    source=args.source.resolve()
    sha=require_source_state(source,args.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    paired_fixtures = {}
    if case_suites is None:
        fixture_path = f"{pkg}/Tests/{package}Tests/{suite.split('.')[-1]}.swift"
        fixture = overlay.read_bytes() if overlay else (source/fixture_path).read_bytes()
        if not overlay:
            assert fixture==subprocess.check_output(['git','-C',source,'show',base+':'+fixture_path])
        assert set(re.findall(rb'func (test\w+)\(',fixture))=={case.encode() for case in cases}
        fixture_hash = hashlib.sha256(fixture).hexdigest()
    else:
        if overlay or set(cases) != set(case_suites):
            raise ValueError('Expected the exact set of selected test cases and no overlay')
        suite_hashes = {}
        target_suite_hashes = {}
        for name in sorted(set(case_suites.values())):
            path = f"{pkg}/Tests/{package}Tests/{name.split('.')[-1]}.swift"
            target = (source/path).read_bytes()
            original = subprocess.check_output(['git','-C',source,'show',base+':'+path])
            selected = {case.encode() for case in cases if case_suites[case] == name}
            for data in (original, target):
                declared = re.findall(rb'func (test\w+)\(',data)
                if any(declared.count(case) != 1 for case in selected):
                    raise ValueError('Missing or ambiguous selected case in '+path)
            # Build the baseline test and its original helpers against BOTH production
            # revisions. Unrelated new tests in a shared suite are outside this probe.
            paired_fixtures[path] = original
            suite_hashes[name] = hashlib.sha256(original).hexdigest()
            target_suite_hashes[name] = hashlib.sha256(target).hexdigest()
        fixture_hash = hashlib.sha256(json.dumps(suite_hashes,sort_keys=True).encode()).hexdigest()
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();rows=[]
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    phases = [('before',base),('after',sha)] if compare else [('after',sha)]
    for phase,rev in phases:
        archive=subprocess.check_output(['git','-C',source,'archive',rev,pkg,*['Packages/'+name for name in local_dependencies]])
        with tempfile.TemporaryDirectory(prefix='oath-package-review-') as tmp:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(tmp,filter='data')
            for path, data in paired_fixtures.items():
                # The path is constructed solely under the exported package test target.
                (Path(tmp)/path).write_bytes(data)
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
                test_suite = case_suites[case] if case_suites else suite
                command=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',test_suite+'/'+case,str(bundles[0])]
                with log.open('w') as stream:
                    code,expired=logged_command(command,stream=stream,env=env,timeout=45)
                status='failed' if expired else outcome(log.read_text(errors='replace'),code,case,phase=='before')
                rows.append(dict(phase=phase,case=case,source_commit=rev,status=status,exit_code=code,timed_out=expired,log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
                print(phase,case,status,flush=True)
    require_source_state(source,sha)
    ok=len(rows)==len(phases)*len(cases) and all(x['status']!='failed' for x in rows)
    result=dict(check=check,source_commit=sha,baseline_commit=base,dependency_commits=pins,
                fixture_sha256=fixture_hash,status='passed' if ok else 'failed',executions=rows,
                duration_seconds=round(time.monotonic()-start,3),scope=scope)
    if case_suites:
        result.update(suite_sha256=suite_hashes,shipped_target_suite_sha256=target_suite_hashes,fixture_revision=base,case_suites=case_suites)
    if 'SwiftDraw' in pins: result['swiftdraw_commit'] = pins['SwiftDraw']
    log=out/(check+'.log');log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/(check+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    return 0 if ok else 1
