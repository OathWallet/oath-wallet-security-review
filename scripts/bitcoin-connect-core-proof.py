#!/usr/bin/env python3
"""Compare dApp sign-and-broadcast results using the same independent Bitcoin Core on two app revisions."""
import argparse
import io
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
from bitcoin_core_regtest import BIN, ROOT, execute, sha
from source_state import require_source_state

BASE='e4d48f85ee43236c388b987dfec52feadfae2551'
SUITE='BitcoinConnectCoreTests'
CASE='testConfirmedWalletConnectSignatures'

def accepted(row, text, before):
    markers=re.findall(r'^Bitcoin Core accepted and mined WalletConnect (\w+)$',text,re.M)
    if len(markers)!=len(set(markers)):return False
    rejects=re.findall(r'^Rejected by Core: (\d+), (.+)$',text,re.M)
    if row['network_active'] or row['peers']!=0 or row['chain']!='regtest':return False
    if not before:return not rejects and row['status']=='passed' and set(markers)=={'44','49','84','86'} and row['blocks']==109
    name=f'-[OathBitcoinTests.{SUITE} {CASE}]'
    errors=[line.split(': error: ',1)[-1] for line in text.splitlines() if ': error:' in line]
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    expected=[name+' : failed - Bitcoin Core rejected wallet signatures for 84,86']
    reasons={'84':'mempool-script-verify-flag-failed (Signature must be zero for failed CHECK(MULTI)SIG operation)',
             '86':'mempool-script-verify-flag-failed (Invalid Schnorr signature)'}
    return len(rejects)==2 and dict(rejects)==reasons and row['exit_code']==1 and sorted(errors)==sorted(expected) and events==[(name,'started'),(name,'failed')] and set(markers)=={'44','49'} and row['blocks']==107

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--core-bin',type=Path,required=True)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-commit')
    a=p.parse_args();src=a.source.resolve();out=a.output.resolve();out.mkdir(exist_ok=True,parents=True)
    fixed=require_source_state(src,a.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI'}}
    for key,digest in BIN.items():
        if sha(a.core_bin/key)!=digest:raise ValueError('Wrong Core executable')
    fixture=ROOT/'fixtures/bitcoin-core/BitcoinConnectCoreTests.swift';overlay=fixture.read_bytes();rows=[]
    for phase,rev in [('before',BASE),('after',fixed)]:
        d=out/phase;d.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='oath-wc-core-') as tmp:
            with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','-C',src,'archive',rev,'Packages/OathBitcoin','Packages/OathSecp256k1','Packages/OathDiagnostics']))) as tar:tar.extractall(tmp,filter='data')
            pkg=Path(tmp)/'Packages/OathBitcoin'
            with (pkg/'Tests/OathBitcoinTests'/fixture.name).open('xb') as f:f.write(overlay)
            prefix=['swift','build','--package-path',pkg,'--scratch-path',a.scratch.resolve()/phase,'--build-system','native','--force-resolved-versions']
            with (d/'compile.log').open('w') as log:subprocess.run([*prefix,'--build-tests','--jobs','4'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
            bundle=Path(subprocess.check_output([*prefix,'--show-bin-path'],env=env,text=True).strip())/'OathBitcoinPackageTests.xctest'
            row=execute((SUITE,CASE,19743,'oath-connect-proof','OATH_CONNECT_REGTEST_DIR',109),a.core_bin.resolve(),bundle,d,env)
            ok=accepted(row,(d/row['log']).read_text(),phase=='before')
            row.update(phase=phase,source_commit=rev,evidence_valid=ok)
            rows.append(row);print(phase,row['status'],row['blocks'],ok,flush=True)
    require_source_state(src,fixed)
    result=dict(check='bitcoin-connect-core-proof',source_commit=fixed,baseline_commit=BASE,fixture_sha256=hashlib.sha256(overlay).hexdigest(),binary_sha256=BIN,
                status='passed' if all(r['evidence_valid'] for r in rows) else 'failed',executions=rows,
                scope='Synthetic signer and 4 locally funded scripts. WalletConnect signet address envelope, Core regtest consensus and mining. No public chain or relay.')
    log=out/'bitcoin-connect-core-proof.log';log.write_text(json.dumps(result,indent=2)+'\n');result.update(log=log.name,log_sha256=sha(log));(out/'bitcoin-connect-core-proof.json').write_text(json.dumps(result,indent=2)+'\n')
    return int(result['status']!='passed')

if __name__=='__main__':raise SystemExit(main())
