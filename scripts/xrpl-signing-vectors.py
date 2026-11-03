#!/usr/bin/env python3
"""Replay deterministic SDK vectors against the actual Swift package in an isolated copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from isolated_tests import classify
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
COMMIT='6783750661c43d3511d8973a2de77106fdf2001d'
METHODS=['testIndependentSDKBytesAndHashes','testAlteredPlanCannotReuseSignature','testCorruptedEnvelopeAndSignerSetAreRejected','testRIPEMDBlockBoundariesMatchOpenSSL']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('scratch',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    source=a.source.resolve();scratch=a.scratch.resolve();out=a.output.resolve();scratch.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,COMMIT)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    env['npm_config_update_notifier']='false'
    start=time.monotonic();results=[]
    sdk=scratch/'sdk';sdk.mkdir(exist_ok=True)
    for n in ['package.json','package-lock.json']:shutil.copyfile(source/'Tools/WalletConnectXrplCodec'/n,sdk/n)
    def run(command,log,extra=None):
        with (out/log).open('w') as f:
            r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env| (extra or {}),timeout=1200)
        if r.returncode:raise RuntimeError(f'{log} failed; original log retained')
    run(['npm','ci','--ignore-scripts','--no-audit','--no-fund','--cache',str(scratch/'npm-cache'),'--prefix',str(sdk)],'npm.log')
    run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','node',str(ROOT/'fixtures/xrpl-signing/generate.cjs'),str(sdk),str(out/'vectors.json')],'generate.log')
    fixture=json.loads((out/'vectors.json').read_text())
    if len(fixture['vectors'])!=61 or len(fixture['hashes'])!=13:raise ValueError('Unexpected fixture coverage')
    with tempfile.TemporaryDirectory(prefix='oath-xrpl-signing-') as temporary:
        copy=Path(temporary)/'source'
        run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
        run(['git','-C',str(copy),'checkout','--detach',COMMIT],'checkout.log')
        overlay=copy/'Packages/OathAnkr/Tests/OathAnkrTests/XrplAuditSigningTests.swift'
        shutil.copyfile(ROOT/'fixtures/xrpl-signing/XrplAuditSigningTests.swift',overlay)
        package=['--package-path',str(copy/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(scratch/'build')]
        run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
        binary=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
        bundles=list(binary.glob('*.xctest'))
        if len(bundles)!=1:raise ValueError('Expected one test bundle')
        for method in METHODS:
            cmd=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.XrplAuditSigningTests/'+method,str(bundles[0])]
            r=subprocess.run(cmd,env=env|{'OATH_XRPL_REVIEW_VECTOR':str(out/'vectors.json')},capture_output=True,timeout=120)
            raw=r.stdout+r.stderr;log=out/(method+'.log');log.write_bytes(raw)
            results.append(dict(method=method,status=classify(raw.decode(errors='replace'),r.returncode),exit_code=r.returncode,log=log.name,log_sha256=sha(log)))
        changed=subprocess.check_output(['git','-C',str(copy),'diff','--name-only'],env=env,text=True)
        if changed:raise ValueError('Tracked source changed in isolated copy')
    require_source_state(source,COMMIT)
    report=dict(source_commit=COMMIT,methods=results,transaction_vectors=61,ripemd_vectors=13,fixture_sha256=sha(out/'vectors.json'),sdk_lock_sha256=sha(sdk/'package-lock.json'),overlay_sha256=sha(ROOT/'fixtures/xrpl-signing/XrplAuditSigningTests.swift'),generator_sha256=sha(ROOT/'fixtures/xrpl-signing/generate.cjs'),script_sha256=sha(Path(__file__)),duration_seconds=round(time.monotonic()-start,2),runtime_network='denied by sandbox-exec',scope='Real OathAnkr package and secp256k1 dependency; synthetic public keys, independent pinned JS SDK fixtures, no provider or device')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(sum(r['status']=='passed' for r in results),'passed methods;',len(results),'selected')
    if any(r['status']!='passed' for r in results):raise SystemExit(1)
if __name__=='__main__':main()
