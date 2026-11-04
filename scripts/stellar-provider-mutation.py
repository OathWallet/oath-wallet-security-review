#!/usr/bin/env python3
"""Negative control: relax exact contract authorization binding only in an existing disposable replay copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from isolated_tests import classify
ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
PATH='Packages/OathAnkr/Sources/OathAnkr/StellarSendPlan.swift'
CHECK='authorization == [expected]'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['scratch','baseline_results','output']:p.add_argument(n,type=Path)
    a=p.parse_args();scratch=a.scratch.resolve();out=a.output.resolve();source=scratch/'source'
    report=json.loads((a.baseline_results/'result.json').read_text())
    if report['source_commit']!=PIN or len(report['methods'])!=12 or any(r['status']!='passed' for r in report['methods']):raise ValueError('Requires verified successful replay')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Wrong source pin')
    if subprocess.check_output(['git','-C',str(source),'diff','--name-only']).strip():raise ValueError('Requires pristine tracked source')
    target=source/PATH;original=target.read_bytes();text=original.decode()
    expected=next(r['sha256'] for r in report['production'] if r['path']==PATH)
    if digest(original)!=expected or text.count(CHECK)!=1:raise ValueError('Mutation source binding mismatch')
    if out.exists():raise ValueError('Fresh output required')
    out.mkdir(parents=True);start=time.monotonic()
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    prefix=['--package-path',str(source/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(scratch/'build')]
    mutated=text.replace(CHECK,'authorization.count == 1').encode()
    try:
        target.write_bytes(mutated)
        diff=subprocess.check_output(['git','-C',str(source),'diff','--',PATH]);(out/'mutation.patch').write_bytes(diff)
        with (out/'build.log').open('w') as f:
            r=subprocess.run(['swift','build',*prefix,'--build-tests','--jobs','4'],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
        if r.returncode:raise RuntimeError('Mutation compile failed; not a successful negative control')
        bindir=Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],env=env,text=True).strip());bundles=list(bindir.glob('*.xctest'))
        if len(bundles)!=1:raise ValueError('Ambiguous bundle')
        method='testMalformedContractSimulationsCannotReachSigning'
        r=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.StellarProviderReviewTests/'+method,str(bundles[0])],env=env,capture_output=True,timeout=120)
        raw=r.stdout+r.stderr;(out/'mutation.log').write_bytes(raw)
        status=classify(raw.decode(errors='replace'),r.returncode)
        assertion_count=raw.count(b'failed - Accepted changedAuthorization')
        result={'source_commit':PIN,'source_path':PATH,'original_sha256':digest(original),'mutated_sha256':digest(mutated),'driver_sha256':digest(Path(__file__).read_bytes()),'test_executable_sha256':digest((bundles[0]/'Contents/MacOS'/bundles[0].stem).read_bytes()),'method':method,'exit_code':r.returncode,'status':status,'expected_authorization_assertion_failures':1,'observed_authorization_assertion_failures':assertion_count,'runtime_network':'denied by sandbox-exec','duration_seconds':round(time.monotonic()-start,3),'scope':'Same disposable checkout and build graph as successful replay, then recompiled after a single mutation. No app publication.'}
    finally:
        target.write_bytes(original)
    if subprocess.check_output(['git','-C',str(source),'diff','--name-only']).strip():raise ValueError('Source restoration failed')
    result['tracked_source_restored']=True
    result['files']=[{'path':f.name,'sha256':digest(f.read_bytes())} for f in sorted(out.iterdir()) if f.is_file()]
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':status,'assertion_failures':assertion_count}))
    if r.returncode==0 or status not in ['failed','assertion-failed'] or assertion_count!=1:raise RuntimeError('Unexpected negative-control result')
if __name__=='__main__':main()
