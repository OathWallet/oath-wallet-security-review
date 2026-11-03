#!/usr/bin/env python3
"""Pinned production Sui signing checks; independent hashlib and integer Base58 vectors."""
import argparse
import base64
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
COMMIT = 'b3f1f6af98bedfe850d390cac684a563c598e3ac'
OVERLAY = ROOT / 'fixtures/sui-signing-boundaries/SuiAuditSigningBoundaryTests.swift'
SOURCES = ['Packages/OathAnkr/Sources/OathAnkr/' + n + '.swift' for n in ['SuiSendCrypto','SuiSendPlan','SuiMultisig','SuiSendClient','SuiModels','WalletConnectSui']]
METHODS = ['testIndependentBlake2bAndBase58Vectors','testSingleSignatureByteMutationsAndIntentSeparation','testSignatureTruncationsTrailingBytesAndSlices','testMultisigEnvelopeMutationsAndSignerMembership','testDecodedInvalidPlansFailBeforeSerializationAndSigning','testAgeAndMaximumEpochBoundaries']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def vectors():
    lengths = [0,1,2,3,31,32,63,64,65,127,128,129,255,256,257,1024] + [(i*73+19)%2049 for i in range(68)]
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    out = []
    for i, size in enumerate(lengths):
        data = bytes((j*37+i*11)%256 for j in range(size))
        if i % 3 == 0: data = bytes(min(3,size)) + data[min(3,size):]
        encoded = None
        if 0 < size <= 32:
            n = int.from_bytes(data,'big'); digits = ''
            while n: n,r = divmod(n,58); digits = alphabet[r]+digits
            encoded = '1'*(len(data)-len(data.lstrip(b'\0'))) + digits
        for length in [1,16,32,64]:
            out.append({'input':base64.b64encode(data).decode(),'length':length,'hash':hashlib.blake2b(data,digest_size=length).hexdigest(),'base58':encoded})
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','scratch','output'): p.add_argument(n,type=Path)
    p.add_argument('--expected-commit',default=COMMIT);p.add_argument('--build-cache',type=Path)
    a=p.parse_args(); commit=a.expected_commit; source,scratch,out=[getattr(a,n).resolve() for n in ('source','scratch','output')]
    require_source_state(source,commit)
    if scratch.exists() or out.exists(): raise ValueError('Fresh scratch/output paths required')
    scratch.mkdir(parents=True); out.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    start=time.monotonic()
    def run(cmd, log):
        with (out/log).open('w') as f: r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
        if r.returncode: raise RuntimeError(log+' failed; original log retained')
    copy=scratch/'source'
    run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
    run(['git','-C',str(copy),'checkout','--detach',commit],'checkout.log')
    shutil.copyfile(OVERLAY,copy/'Packages/OathAnkr/Tests/OathAnkrTests'/OVERLAY.name)
    (out/'vectors.json').write_text(json.dumps(vectors(),indent=2)+'\n')
    for cmd,log in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['python3','--version'],'python-version.log')]: run(cmd,log)
    package=['--package-path',str(copy/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str((a.build_cache or scratch/'build').resolve())]
    run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
    binary=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
    bundles=list(binary.glob('*.xctest'))
    if len(bundles)!=1: raise ValueError('Ambiguous test bundle')
    selection=['SuiAuditSigningBoundaryTests/'+m for m in METHODS]
    excluded=[]
    for suite in ['SuiSendTests','SuiSendTransportTests','SuiMultisigTests','WalletConnectSuiTests','WalletConnectSuiReviewTests']:
        text=(copy/'Packages/OathAnkr/Tests/OathAnkrTests'/(suite+'.swift')).read_text()
        for method in re.findall(r'func (test\w+)\(',text):
            (excluded if suite == 'SuiSendTests' and method.startswith('testLive') else selection).append(suite+'/'+method)
    results=[]
    for method in selection:
        cmd=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.'+method,str(bundles[0])]
        r=subprocess.run(cmd,env=env|{'OATH_SUI_AUDIT_VECTORS':str(out/'vectors.json')},capture_output=True,timeout=120)
        raw=r.stdout+r.stderr; log=out/(method.replace('/','-')+'.log'); log.write_bytes(raw)
        results.append({'method':method,'status':classify(raw.decode(errors='replace'),r.returncode),'exit_code':r.returncode,'log':log.name,'log_sha256':sha(log)})
    if subprocess.check_output(['git','-C',str(copy),'diff','--name-only']).strip(): raise ValueError('Tracked sources changed')
    require_source_state(source,commit)
    report={'source_commit':commit,'source_files':[{'path':f,'source_sha256':sha(source/f),'executed_sha256':sha(copy/f)} for f in SOURCES],
        'overlay_sha256':sha(OVERLAY),'driver_sha256':sha(Path(__file__)),'vectors_sha256':sha(out/'vectors.json'),
        'oracle':'Python hashlib.blake2b; independent integer-based Base58 conversion', 'vectors':336,
        'methods':results,'live_methods_excluded':excluded,'runtime_network':'denied by sandbox-exec',
        'duration_seconds':round(time.monotonic()-start,3),
        'scope':'Production package host tests with synthetic secrets. No node execution, app UI, device or broadcast. Existing SDK fixture provenance is not independently re-established here.'}
    report['files']=[{'path':str(f.relative_to(out)),'sha256':sha(f)} for f in sorted(out.rglob('*')) if f.is_file()]
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':sum(r['status']=='passed' for r in results),'selected':len(results),'live_excluded':len(excluded)}))
    if any(r['status']!='passed' for r in results): raise SystemExit(1)

if __name__=='__main__':main()
