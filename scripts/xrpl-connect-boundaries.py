#!/usr/bin/env python3
"""Exercise XRP request boundaries through the actual package and bundled JavaScriptCore codec."""
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
COMMIT='8a31eb265c34ef7f37ba21741201842366d43b7b'
METHODS=['testDuplicateAndResourceBounds','testAuthorityAndChainBoundaries','testReviewMutationAndTimeBoundaries','testSignedPayloadTampering','testMultisignOrderingAndPriorSignatureTamper','testMemoUnknownFieldsAndNumericRoundTrip']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('scratch',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    source=a.source.resolve();scratch=a.scratch.resolve();out=a.output.resolve();scratch.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,COMMIT)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    env['npm_config_update_notifier']='false'
    start=time.monotonic();results=[]
    def run(command,log,extra=None):
        with (out/log).open('w') as f:
            r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env| (extra or {}),timeout=1200)
        if r.returncode:raise RuntimeError(f'{log} failed; original log retained')
    with tempfile.TemporaryDirectory(prefix='oath-xrpl-boundary-') as temporary:
        copy=Path(temporary)/'source'
        run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
        run(['git','-C',str(copy),'checkout','--detach',COMMIT],'checkout.log')
        overlay=copy/'Packages/OathAnkr/Tests/OathAnkrTests/WalletConnectXrplAuditBoundaryTests.swift'
        shutil.copyfile(ROOT/'fixtures/xrpl-signing/WalletConnectXrplAuditBoundaryTests.swift',overlay)
        package=['--package-path',str(copy/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(scratch/'build')]
        run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
        binary=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
        bundles=list(binary.glob('*.xctest'))
        if len(bundles)!=1:raise ValueError('Expected one test bundle')
        for method in METHODS:
            cmd=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathAnkrTests.WalletConnectXrplAuditBoundaryTests/'+method,str(bundles[0])]
            r=subprocess.run(cmd,env=env,capture_output=True,timeout=120)
            raw=r.stdout+r.stderr;log=out/(method+'.log');log.write_bytes(raw)
            results.append(dict(method=method,status=classify(raw.decode(errors='replace'),r.returncode),exit_code=r.returncode,log=log.name,log_sha256=sha(log)))
        changed=subprocess.check_output(['git','-C',str(copy),'diff','--name-only'],env=env,text=True)
        if changed:raise ValueError('Tracked source changed in isolated copy')
    require_source_state(source,COMMIT)
    report=dict(source_commit=COMMIT,methods=results,overlay_sha256=sha(ROOT/'fixtures/xrpl-signing/WalletConnectXrplAuditBoundaryTests.swift'),script_sha256=sha(Path(__file__)),duration_seconds=round(time.monotonic()-start,2),runtime_network='denied by sandbox-exec',scope='Real Swift request, review, signing verification and JavaScriptCore codec; public deterministic test material only, no provider, simulator or device')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(sum(r['status']=='passed' for r in results),'passed methods;',len(results),'selected')
    if any(r['status']!='passed' for r in results):raise SystemExit(1)
if __name__=='__main__':main()
