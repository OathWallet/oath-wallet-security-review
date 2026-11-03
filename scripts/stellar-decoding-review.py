#!/usr/bin/env python3
"""Replay independent synthetic decoding vectors against a fresh pinned app checkout."""
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
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
SDK_PIN='b5dac0a6e8ff312d597c9a3b4269b03131d66e0d'
METHODS=['testIndependentStrkeyCorpusAndSDKAgreement','testIndependentAssetContractNetworkAndIssuerBinding','testExactDecimalAndSignedXDRCorpus','testCAP67AmountMapVariants','testTruncatedAndUnknownXDRCannotProduceValues','testFeeAndMovementStateOwnerContractBinding','testHoldingsBindOwnerAmountsAndMetadata']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source','scratch','output']:p.add_argument(name,type=Path)
    a=p.parse_args();source,scratch,out=[getattr(a,n).resolve() for n in ['source','scratch','output']]
    require_source_state(source,PIN)
    if scratch.exists() or out.exists():raise ValueError('Fresh scratch/output required')
    scratch.mkdir(parents=True);out.mkdir(parents=True);start=time.monotonic()
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    def run(cmd,name):
        with (out/name).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
        if r.returncode:raise RuntimeError(name+' failed; original log retained')
    copy=scratch/'source'
    run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
    run(['git','-C',str(copy),'checkout','--detach',PIN],'checkout.log')
    require_source_state(copy,PIN)
    vectors=ROOT/'fixtures/stellar-decoding/vectors.json';overlay=ROOT/'fixtures/stellar-decoding/StellarDecodingReviewTests.swift'
    run(['python3',str(ROOT/'scripts/stellar-decoding-vectors.py'),str(out/'regenerated.json')],'generator.log')
    if (out/'regenerated.json').read_bytes()!=vectors.read_bytes():raise ValueError('Vector reproduction mismatch')
    package=copy/'Packages/OathAnkr';tests=package/'Tests/OathAnkrTests'
    shutil.copyfile(vectors,tests/'Fixtures/StellarReview.json');shutil.copyfile(overlay,tests/overlay.name)
    prefix=['--package-path',str(package),'--build-system','native','--scratch-path',str(scratch/'build')]
    for cmd,name in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['python3','--version'],'python-version.log'),(['swift','build',*prefix,'--build-tests','--jobs','4'],'build.log')]:run(cmd,name)
    sdk=scratch/'build/checkouts/stellar-ios-mac-sdk'
    sdk_commit=subprocess.check_output(['git','-C',str(sdk),'rev-parse','HEAD'],text=True).strip()
    if sdk_commit!=SDK_PIN or subprocess.check_output(['git','-C',str(sdk),'status','--porcelain']).strip():raise ValueError('SDK source pin or state mismatch')
    bindir=Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],env=env,text=True).strip());bundles=list(bindir.glob('*.xctest'))
    if len(bundles)!=1:raise ValueError('Ambiguous bundle')
    rows=[]
    for method in METHODS:
        cmd=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.StellarDecodingReviewTests/'+method,str(bundles[0])]
        r=subprocess.run(cmd,env=env,capture_output=True,timeout=120);raw=r.stdout+r.stderr;log=out/(method+'.log');log.write_bytes(raw)
        rows.append({'method':method,'status':classify(raw.decode(errors='replace'),r.returncode),'exit_code':r.returncode,'log':log.name,'log_sha256':sha(log)})
    if subprocess.check_output(['git','-C',str(copy),'diff','--name-only']).strip():raise ValueError('Tracked source changed')
    allowed={str(p.relative_to(copy)) for p in [tests/'Fixtures/StellarReview.json',tests/overlay.name]}
    untracked=set(subprocess.check_output(['git','-C',str(copy),'ls-files','--others','--exclude-standard'],text=True).splitlines())
    if untracked!=allowed:raise ValueError('Unexpected overlay files')
    require_source_state(source,PIN)
    report={'source_commit':PIN,'sdk_commit':sdk_commit,'seed':'oath-stellar-decoding-v1','driver_sha256':sha(Path(__file__)),'generator_sha256':sha(ROOT/'scripts/stellar-decoding-vectors.py'),'overlay_sha256':sha(overlay),'vectors_sha256':sha(vectors),'methods':rows,'duration_seconds':round(time.monotonic()-start,3),'test_executable_sha256':sha(bundles[0]/'Contents/MacOS'/bundles[0].stem),'runtime_network':'denied by sandbox-exec','production':[{'path':'Packages/OathAnkr/Sources/OathAnkr/'+name,'sha256':sha(package/'Sources/OathAnkr'/name)} for name in ['StellarModels.swift','StellarDecoding.swift']],'files':[{'path':f.name,'sha256':sha(f)} for f in sorted(out.iterdir()) if f.is_file()]}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':sum(r['status']=='passed' for r in rows),'total':len(rows)}))
    if any(r['status']!='passed' for r in rows):raise SystemExit(1)
if __name__=='__main__':main()
