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
COMMIT='0614556b993f85808b13e3a69984ce36050a8dfe'
METHODS=['testIndependentPlanBytesHashesAndSignatures','testIndependentActionsAndProductionSignatures','testChangedPlansAndTamperedSignaturesAreRejected','testTruncatedAndTrailingActionBytesAreRejected','testNonzeroOriginDataSliceMatchesBytes']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('scratch',type=Path);p.add_argument('output',type=Path);p.add_argument('--commit',default=COMMIT);a=p.parse_args()
    commit=a.commit
    source=a.source.resolve();scratch=a.scratch.resolve();out=a.output.resolve();scratch.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,commit)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    env['npm_config_update_notifier']='false'
    start=time.monotonic();results=[]
    sdk=scratch/'sdk';sdk.mkdir(exist_ok=True)
    for n in ['package.json','package-lock.json']:shutil.copyfile(ROOT/'fixtures/near-signing'/n,sdk/n)
    def run(command,log,extra=None):
        with (out/log).open('w') as f:
            r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env| (extra or {}),timeout=1200)
        if r.returncode:raise RuntimeError(f'{log} failed; original log retained')
    run(['npm','ci','--ignore-scripts','--no-audit','--no-fund','--cache',str(scratch/'npm-cache'),'--prefix',str(sdk)],'npm.log')
    run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','node',str(ROOT/'fixtures/near-signing/generate.mjs'),str(sdk),str(out/'vectors.json')],'generate.log')
    run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','node',str(ROOT/'fixtures/near-signing/generate.mjs'),str(sdk),str(out/'vectors-repeat.json')],'generate-repeat.log')
    if sha(out/'vectors.json') != sha(out/'vectors-repeat.json'): raise ValueError('Nondeterministic fixtures')
    for command,log in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['node','--version'],'node-version.log'),(['npm','--version'],'npm-version.log'),(['python3','--version'],'python-version.log')]:run(command,log)
    fixture=json.loads((out/'vectors.json').read_text())
    if len(fixture['plans'])!=72 or len(fixture['actions'])!=10:raise ValueError('Unexpected fixture coverage')
    with tempfile.TemporaryDirectory(prefix='oath-near-signing-') as temporary:
        copy=Path(temporary)/'source'
        run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
        run(['git','-C',str(copy),'checkout','--detach',commit],'checkout.log')
        overlay=copy/'Packages/OathAnkr/Tests/OathAnkrTests/NearAuditSigningTests.swift'
        shutil.copyfile(ROOT/'fixtures/near-signing/NearAuditSigningTests.swift',overlay)
        package=['--package-path',str(copy/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(scratch/'build')]
        run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
        binary=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
        bundles=list(binary.glob('*.xctest'))
        if len(bundles)!=1:raise ValueError('Expected one test bundle')
        for method in METHODS:
            cmd=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.NearAuditSigningTests/'+method,str(bundles[0])]
            r=subprocess.run(cmd,env=env|{'OATH_NEAR_AUDIT_VECTORS':str(out/'vectors.json'),'OATH_NEAR_AUDIT_SIGNATURES':str(out/'application-signatures.json')},capture_output=True,timeout=120)
            raw=r.stdout+r.stderr;log=out/(method+'.log');log.write_bytes(raw)
            results.append(dict(method=method,status=classify(raw.decode(errors='replace'),r.returncode),exit_code=r.returncode,log=log.name,log_sha256=sha(log)))
        changed=subprocess.check_output(['git','-C',str(copy),'diff','--name-only'],env=env,text=True)
        if changed:raise ValueError('Tracked source changed in isolated copy')
    verification = all(r['status']=='passed' for r in results)
    if verification:
        run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','node',str(ROOT/'fixtures/near-signing/verify.mjs'),str(out/'vectors.json'),str(out/'application-signatures.json')],'verify-signatures.log')
    require_source_state(source,commit)
    report=dict(source_commit=commit,methods=results,transaction_vectors=72,action_vectors=10,fixture_sha256=sha(out/'vectors.json'),sdk_lock_sha256=sha(sdk/'package-lock.json'),overlay_sha256=sha(ROOT/'fixtures/near-signing/NearAuditSigningTests.swift'),generator_sha256=sha(ROOT/'fixtures/near-signing/generate.mjs'),script_sha256=sha(Path(__file__)),independent_signature_verification=verification,verifier_sha256=sha(ROOT/'fixtures/near-signing/verify.mjs'),duration_seconds=round(time.monotonic()-start,2),runtime_network='denied by sandbox-exec',scope='Real OathAnkr package and CryptoKit Ed25519; synthetic public keys, pinned NEAR SDK vectors and Node crypto verification; no provider or device')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(sum(r['status']=='passed' for r in results),'passed methods;',len(results),'selected')
    if any(r['status']!='passed' for r in results):raise SystemExit(1)
if __name__=='__main__':main()
