#!/usr/bin/env python3
"""Exercise real account-read suspension, signing and permission-grant removal."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from source_state import require_source_state

COMMIT='0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d'
ROOT=Path(__file__).resolve().parents[1]
VAULT='OathAtmosphere/Wallet/OathWalletVault.swift'
OPERATIONS=['soft removal','permanent removal','remove and restore','other wallet removal','failed save','lock']

def expected_cases(vulnerable=False):
    result=[]
    for op in OPERATIONS:
        result.append(('PASS',op+' biometric read held'))
        if op=='failed save': result.append(('PASS',op+' expected save failure'))
        result.append(('FAIL' if vulnerable and op=='remove and restore' else 'PASS',op+' delayed consent'))
        if op=='remove and restore': result.append(('PASS',op+' fresh consent'))
    return result

def validate(code,text,vulnerable=False):
    cases=re.findall(r'^(PASS|FAIL): (.+)$',text,re.M)
    if cases!=expected_cases(vulnerable) or code!=(1 if vulnerable else 0):raise ValueError('Unexpected consent cases/results/exit')
    if text.splitlines().count(f'Pending consent checks: {13 if vulnerable else 14} passed, {1 if vulnerable else 0} failed')!=1:raise ValueError('Missing exact summary')
    return cases

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('scratch',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--commit',default=COMMIT)
    p.add_argument('--expect-vulnerable',action='store_true')
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,a.commit)
    fixture=ROOT/'fixtures/connect-removal-read/PendingConsent.swift';original=(source/VAULT).read_bytes()
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    env['OATH_VALIDATION_SCRATCH']=str(a.scratch.resolve())
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oath-removal-auth-') as directory:
        clone=Path(directory)/'source'
        with (out/'checkout.log').open('w') as log:
            subprocess.run(['git','clone','--no-hardlinks','--no-checkout',str(source),str(clone)],stdout=log,stderr=log,check=True)
            subprocess.run(['git','-C',str(clone),'checkout','--detach',a.commit],stdout=log,stderr=log,check=True)
        (clone/'Tools/CheckWalletConnectAuthorization.swift').write_bytes(fixture.read_bytes())
        compiled=original.decode()
        # Keep inherited production/host adapters; separate build from execution
        # so the actual fixture binary cannot make network connections.
        harness=(clone/'Tools/CheckMultiWallet.py').read_text()
        old='subprocess.run(["swift", "run", "--build-system", "native", "--package-path", str(work),'
        if harness.count(old)!=1:raise ValueError('Host harness command changed')
        harness=harness.replace(old,'subprocess.run(["swift", "build", "--build-system", "native", "--package-path", str(work),')
        tail='"/tmp/oath-multiwallet-validation-build"), "WalletValidation"], check=True, env=environment)'
        if harness.count(tail)!=1:raise ValueError('Host harness product changed')
        harness=harness.replace(tail,'"/tmp/oath-multiwallet-validation-build"), "--product", "WalletValidation"], check=True, env=environment)')
        harness+='''\n    bin_path = subprocess.check_output(["swift","build","--build-system","native","--package-path",str(work),"--scratch-path",os.environ["OATH_VALIDATION_SCRATCH"],"--show-bin-path"],env=environment,text=True).strip()\n    completed = subprocess.run(["/usr/bin/sandbox-exec","-p","(version 1) (allow default) (deny network*)",str(Path(bin_path)/"WalletValidation")],env=environment)\n    sys.exit(completed.returncode)\n'''
        (clone/'Tools/CheckMultiWallet.py').write_text(harness)
        with (out/'checks.log').open('w') as log:
            proc=subprocess.run(['python3','Tools/CheckMultiWallet.py','--walletconnect'],cwd=clone,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
        raw=(out/'checks.log').read_bytes();cases=re.findall(r'^(PASS|FAIL): (.+)$',raw.decode(),re.M)
    require_source_state(source,a.commit)
    report={'source_commit':a.commit,'source_sha256':sha(original),'compiled_vault_sha256':sha(compiled.encode()),'fixture_sha256':sha(fixture.read_bytes()),'harness_original_sha256':sha((source/'Tools/CheckMultiWallet.py').read_bytes()),'harness_executed_sha256':sha(harness.encode()),'script_sha256':sha(Path(__file__).read_bytes()),'expected_vulnerable':a.expect_vulnerable,'exit_code':proc.returncode,'cases':[{'name':n,'status':s.lower()} for s,n in cases],'log_sha256':sha(raw),'duration_seconds':round(time.monotonic()-start,2),'runtime_network':'denied','scope':'Production vault/encrypted envelope/SQLite/EVM imported-key message and typed-data signing; memory credential and biometric stores; inherited synthetic HD and unrelated chain/service adapters. No UI, OS authentication, simulator, device or relay.'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    validate(proc.returncode,raw.decode(),a.expect_vulnerable)
    print(json.dumps({'exit_code':proc.returncode,'passed':sum(s=='PASS' for s,n in cases),'failed':sum(s=='FAIL' for s,n in cases)}))

if __name__=='__main__':main()
