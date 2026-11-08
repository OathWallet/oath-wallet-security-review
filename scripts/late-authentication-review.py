#!/usr/bin/env python3
"""Exercise captured late credentials after changes to the production vault session."""
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

COMMIT='a9c062a3a1d492799b9f6e9d083630c7006183ea'
ROOT=Path(__file__).resolve().parents[1]
VAULT='OathAtmosphere/Wallet/OathWalletVault.swift'
OPERATIONS=['unchanged','lock and reopen','rotate passcode','disable biometrics','disable passcode','cancel','switch wallet','cross-wallet account']

def expected_cases(mutant=False):
    result=[]
    for kind in ['message','typed']:
        for operation in OPERATIONS:
            prefix=kind+' / '+operation
            result.extend([('PASS',prefix+' initial signature'),('PASS',prefix+' captured credential held')])
            result.append(('FAIL' if mutant and operation=='lock and reopen' else 'PASS',prefix+' delayed result'))
            if operation=='rotate passcode': result.append(('PASS',prefix+' old passcode rejected'))
            result.append(('PASS',prefix+' fresh request remains usable'))
    return result

def validate(code,text,mutant=False):
    cases=re.findall(r'^(PASS|FAIL): (.+)$',text,re.M)
    if cases!=expected_cases(mutant) or code!=(1 if mutant else 0): raise ValueError('Unexpected test identities/results/exit')
    failures=2 if mutant else 0
    if text.splitlines().count(f'Late authentication checks: {66-failures} passed, {failures} failed')!=1:
        raise ValueError('Missing exact summary')
    return cases


def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('scratch',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--mutate-generation',action='store_true')
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    if a.scratch.exists(): raise ValueError('Fresh build directory required')
    require_source_state(source,COMMIT)
    fixture=ROOT/'fixtures/late-authentication/Checks.swift';original=(source/VAULT).read_bytes()
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    env['OATH_VALIDATION_SCRATCH']=str(a.scratch.resolve())
    env['OATH_AUDIT_OUTPUT']=str(out)
    start=time.monotonic()
    for cmd,name in [(['xcodebuild','-version'],'xcode.log'),(['swift','--version'],'swift.log'),(['python3','--version'],'python.log')]:
        p=subprocess.run(cmd,env=env,capture_output=True,check=True); (out/name).write_bytes(p.stdout+p.stderr)
    with tempfile.TemporaryDirectory(prefix='oath-removal-auth-') as directory:
        clone=Path(directory)/'source'
        with (out/'checkout.log').open('w') as log:
            subprocess.run(['git','clone','--no-hardlinks','--no-checkout',str(source),str(clone)],stdout=log,stderr=log,check=True)
            subprocess.run(['git','-C',str(clone),'checkout','--detach',COMMIT],stdout=log,stderr=log,check=True)
        (clone/'Tools/CheckWalletConnectAuthorization.swift').write_bytes(fixture.read_bytes())
        compiled=original.decode()
        if a.mutate_generation:
            guards={
                'guard token == authenticationGeneration, !resetting else { throw CancellationError() }': 'guard !resetting else { throw CancellationError() }',
                '        guard token == authenticationGeneration else { throw CancellationError() }\n        guard let stored = try storage.read("vault-v1")': '        // Deliberate generation-check mutation.\n        guard let stored = try storage.read("vault-v1")'
            }
            for old,new in guards.items():
                if compiled.count(old)!=1: raise ValueError('Mutation boundary changed')
                compiled=compiled.replace(old,new,1)
            (clone/VAULT).write_text(compiled)
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
        build_marker='    subprocess.run(["swift", "build",'
        if harness.count(build_marker)!=1: raise ValueError('Build marker mismatch')
        harness=harness.replace(build_marker,'    shutil.copyfile(root / "Packages/OathDatabase/Package.resolved", work / "Package.resolved")\n'+build_marker)
        # Keep every generated source/adapter and exact dependency resolution for inspection.
        runtime_marker='    completed = subprocess.run('
        injected = '''    audit_out = Path(os.environ["OATH_AUDIT_OUTPUT"])
    import hashlib
    pins = json.loads((work / "Package.resolved").read_text())["pins"]
    expected = json.loads((root / "Packages/OathDatabase/Package.resolved").read_text())["pins"]
    assert pins == expected, "Resolved dependencies differ from pinned application"
    shutil.copyfile(work / "Package.resolved", audit_out / "Package.resolved")
    (audit_out / "executable.sha256").write_text(hashlib.sha256((Path(bin_path)/"WalletValidation").read_bytes()).hexdigest()+"\\n")
    snapshot = audit_out / "generated-host"
    shutil.copytree(sources, snapshot / "Sources")
    shutil.copyfile(work / "Package.swift", snapshot / "Package.swift")
    for file in snapshot.rglob("*"):
        if file.is_file(): file.write_text(file.read_text().replace(str(root),"<SOURCE>").replace(str(work),"<HOST>"))
    (audit_out / "generated-manifest.json").write_text(json.dumps([{ "path":str(p.relative_to(snapshot)), "sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(snapshot.rglob("*")) if p.is_file()],indent=2)+"\\n")
'''
        if harness.count(runtime_marker)!=1: raise ValueError('Runtime marker mismatch')
        harness=harness.replace(runtime_marker,injected+runtime_marker)
        (clone/'Tools/CheckMultiWallet.py').write_text(harness)
        (out/'executed-harness.py').write_text(harness)

        with (out/'checks.log').open('w') as log:
            proc=subprocess.run(['python3','Tools/CheckMultiWallet.py','--walletconnect'],cwd=clone,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
        raw=(out/'checks.log').read_bytes()
        text=raw.decode().replace(str(clone),'<SOURCE>').replace(str(a.scratch.resolve()),'<BUILD>').replace(str(Path.home()),'<HOME>')
        (out/'checks.log').write_text(text)
        raw=(out/'checks.log').read_bytes();cases=validate(proc.returncode,text,a.mutate_generation)
    require_source_state(source,COMMIT)
    report={'source_commit':COMMIT,'source_sha256':sha(original),'compiled_vault_sha256':sha(compiled.encode()),'fixture_sha256':sha(fixture.read_bytes()),'harness_original_sha256':sha((source/'Tools/CheckMultiWallet.py').read_bytes()),'harness_executed_sha256':sha(harness.encode()),'script_sha256':sha(Path(__file__).read_bytes()),'deliberate_mutation':a.mutate_generation,'dependency_lock_sha256':sha((out/'Package.resolved').read_bytes()),'executable_sha256':(out/'executable.sha256').read_text().strip(),'exit_code':proc.returncode,'cases':[{'name':n,'status':s.lower()} for s,n in cases],'log_sha256':sha(raw),'duration_seconds':round(time.monotonic()-start,2),'runtime_network':'denied','scope':'Production vault/encrypted envelope/SQLite/EVM imported-key message and typed-data signing; memory credential and biometric stores; inherited synthetic HD and unrelated chain/service adapters. No UI, OS authentication, simulator, device or relay.'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Two deliberate generation-control failures detected' if a.mutate_generation else '66 late authentication assertions passed')

if __name__=='__main__':main()
