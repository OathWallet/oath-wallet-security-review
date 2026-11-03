#!/usr/bin/env python3
"""Exercise delayed real vault authorization around wallet lifecycle changes."""
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

ROOT=Path(__file__).resolve().parents[1]
VAULT='OathAtmosphere/Wallet/OathWalletVault.swift'

def expected_cases(before=False, recovery=False):
    result=[]
    if recovery:
        for mode in ['passcode','biometric','device key']:
            for committed in [False,True]:
                prefix=mode+(' / after encrypted commit' if committed else ' / before encrypted commit')
                for label in [('metadata failure observed' if committed else 'durable reservation before key write'),
                    'fence persists before restart','authenticated replay releases fence',
                    'replay follows encrypted membership','both retained wallets survive']:
                    result.append(('PASS',prefix+' / '+label))
        return result
    for order in ['journal first','journal during vault write','removal first','vault write fails']:
        names=['production vault signature verifies']
        if order=='journal first': names+=['pending work rejects removal']
        elif order=='removal first': names+=['removed wallet rejects journal']
        else: names+=['held after pending preflight before encrypted commit']
        if order=='vault write fails': names+=['removal failure expected']
        names+=['removal and new pending work are exclusive']
        if order=='vault write fails': names+=['retry can persist after rejected encrypted write']
        names+=['every saved pending row remains recoverable','restart preserves recoverability']
        if order=='journal during vault write': names+=['pending row survives retention']
        for name in names:
            failed=before and order=='journal during vault write' and name in [
                'removal and new pending work are exclusive','every saved pending row remains recoverable',
                'restart preserves recoverability','pending row survives retention']
            result.append(('FAIL' if failed else 'PASS',order+' / '+name))
    return result

def validate(code,text,before=False,recovery=False):
    cases=re.findall(r'^(PASS|FAIL): (.+)$',text,re.M)
    expected=expected_cases(before,recovery)
    if cases!=expected or code!=(1 if before else 0): raise ValueError('Unexpected test identities/results/exit')
    failures=4 if before else 0
    summary=('Passed 30 wallet removal recovery checks. Synthetic memory credentials and real encrypted vault/database; no device or network.' if recovery else
        f'Removal journal race checks: {23-failures} passed, {failures} failed')
    if text.splitlines().count(summary)!=1:raise ValueError('Missing exact summary')
    return cases

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('scratch',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--commit',required=True);p.add_argument('--before',action='store_true');p.add_argument('--recovery',action='store_true')
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,a.commit)
    fixture=source/('Tools/CheckWalletRemovalRecovery.swift' if a.recovery else 'Tools/CheckWalletRemovalJournalRace.swift');original=(source/VAULT).read_bytes()
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    env['OATH_VALIDATION_SCRATCH']=str(a.scratch.resolve())
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oath-removal-auth-') as directory:
        clone=Path(directory)/'source'
        with (out/'checkout.log').open('w') as log:
            subprocess.run(['git','clone','--no-hardlinks','--no-checkout',str(source),str(clone)],stdout=log,stderr=log,check=True)
            subprocess.run(['git','-C',str(clone),'checkout','--detach',a.commit],stdout=log,stderr=log,check=True)
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
            proc=subprocess.run(['python3','Tools/CheckMultiWallet.py','--removal-recovery' if a.recovery else '--removal-journal-race'],cwd=clone,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
        raw=(out/'checks.log').read_bytes();cases=validate(proc.returncode,raw.decode(),a.before,a.recovery)
    require_source_state(source,a.commit)
    report={'source_commit':a.commit,'source_sha256':sha(original),'fixture_sha256':sha(fixture.read_bytes()),'harness_original_sha256':sha((source/'Tools/CheckMultiWallet.py').read_bytes()),'harness_executed_sha256':sha(harness.encode()),'script_sha256':sha(Path(__file__).read_bytes()),'expected_failure_reproduced':a.before,'recovery':a.recovery,'exit_code':proc.returncode,'cases':[{'name':n,'status':s.lower()} for s,n in cases],'log_sha256':sha(raw),'duration_seconds':round(time.monotonic()-start,2),'runtime_network':'denied','scope':'Production vault/encrypted envelope/SQLite/XRP imported-key signing and journal; gated in-memory credential store; inherited synthetic HD and unrelated service adapters. No UI, OS authentication, simulator, device or relay; no broadcast.'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Four removal-journal failures reproduced' if a.before else '30 recovery checks passed' if a.recovery else '23 removal-journal checks passed')

if __name__=='__main__':main()
