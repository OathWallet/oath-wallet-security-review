#!/usr/bin/env python3
"""Compile actual installation protection with deterministic adversarial host inputs."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
from source_state import require_source_state
ROOT = Path(__file__).resolve().parents[1]
COMMIT = '32701474fefbed3840878e35f6111e8d494e1f02'
SOURCE = 'OathAtmosphere/Wallet/OathInstallationSecurity.swift'
BASELINE = 'Tools/CheckInstallationSecurity.swift'
FIXTURE = 'fixtures/installation-binding/InstallationBindingReview.swift'
GUARD = 'Data("org.oathwallet.installation.v1:\\(id.uuidString):\\(context)".utf8)'
MUTANT = 'Data("org.oathwallet.installation.v1:\\(id.uuidString)".utf8)'

def sha(b): return hashlib.sha256(b).hexdigest()

def validate_mutant(code, result):
    expected = {f'purpose-{i}-{j}' for i in range(4) for j in range(4) if i != j}
    if code != 1 or (result['passed'], result['failed'], result['skipped']) != (0,12,0):
        raise ValueError('Mutation did not fail by the expected assertions')
    if len(result['cases']) != 12 or {c['case'] for c in result['cases']} != expected or any(c['passed'] for c in result['cases']):
        raise ValueError('Wrong mutation case failures')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['source','scratch','output']: p.add_argument(key,type=Path)
    a=p.parse_args(); source,scratch,out=[getattr(a,k).resolve() for k in ['source','scratch','output']]
    require_source_state(source,COMMIT)
    if scratch.exists() or out.exists():raise ValueError('Fresh directories required')
    scratch.mkdir(parents=True);out.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    started=time.monotonic()
    def cmd(args,name):
        r=subprocess.run(args,env=env,capture_output=True,timeout=180)
        raw=(r.stdout+r.stderr).decode(errors='replace')
        for path,label in [(scratch,'<SCRATCH>'),(source,'<SOURCE>'),(out,'<OUTPUT>'),(Path.home(),'<HOME>')]:raw=raw.replace(str(path),label)
        (out/name).write_text(raw)
        return r.returncode
    for args,name in [(['xcodebuild','-version'],'xcode.log'),(['swift','--version'],'swift.log'),(['python3','--version'],'python.log')]:
        if cmd(args,name):raise ValueError('Toolchain unavailable')
    data=subprocess.check_output(['git','-C',str(source),'show',COMMIT+':'+SOURCE])
    baseline=subprocess.check_output(['git','-C',str(source),'show',COMMIT+':'+BASELINE])
    fixture=(ROOT/FIXTURE).read_bytes()
    sourcepath=scratch/'OathInstallationSecurity.swift';sourcepath.write_bytes(data)
    baselinepath=scratch/'CheckInstallationSecurity.swift';baselinepath.write_bytes(baseline)
    fixturepath=scratch/'InstallationBindingReview.swift';fixturepath.write_bytes(fixture)
    (out/'production-source.swift').write_bytes(data);(out/'baseline-fixture.swift').write_bytes(baseline)
    stages=[]
    for stage,test in [('baseline',baselinepath),('production',fixturepath),('mutation-control',fixturepath)]:
        if stage=='mutation-control':
            text=data.decode()
            if text.count(GUARD)!=1:raise ValueError('Guard no longer matches')
            sourcepath.write_text(text.replace(GUARD,MUTANT))
        binary=scratch/stage
        args=['xcrun','swiftc','-swift-version','6','-O','-o',str(binary),str(sourcepath),str(test)]
        if cmd(args,stage+'-build.log'):raise ValueError('Build failed; not a test pass')
        (out/(stage+'-source.swift')).write_bytes(sourcepath.read_bytes())
        args=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(binary)]
        if stage=='mutation-control':args.append('--purpose-only')
        code=cmd(args,stage+'.log')
        result=None
        if stage=='baseline':
            if code!=0 or (out/(stage+'.log')).read_text().strip()!='Passed 56 installation ownership, encryption, reinstall, failure recovery and protected-file host checks.':
                raise ValueError('Inherited baseline did not complete')
        else:
            result=json.loads((out/(stage+'.log')).read_text())
            if stage=='mutation-control':validate_mutant(code,result)
            elif code!=0 or result['failed'] or result['skipped'] or not result['cases'] or not all(c['passed'] for c in result['cases']):raise ValueError('Production assertions failed')
        stages.append(dict(stage=stage,build_exit_code=0,exit_code=code,source_sha256=sha(sourcepath.read_bytes()),fixture_sha256=sha(test.read_bytes()),executable_sha256=sha(binary.read_bytes()),runtime_network='denied',totals=({k:result[k] for k in ['passed','failed','skipped']} if result else dict(passed=56,failed=0,skipped=0))))
    require_source_state(source,COMMIT)
    result=dict(source_commit=COMMIT,production_source=SOURCE,source_sha256=sha(data),fixture=FIXTURE,fixture_sha256=sha(fixture),baseline_fixture=BASELINE,baseline_sha256=sha(baseline),driver_sha256=sha(Path(__file__).read_bytes()),helper_sha256=sha((ROOT/'scripts/source_state.py').read_bytes()),stages=stages,duration_seconds=round(time.monotonic()-started,3),new_app_finding=False,app_modified=False,whole_wallet_complete=False,files=[dict(path=str(f.relative_to(out)),sha256=sha(f.read_bytes())) for f in sorted(out.rglob('*')) if f.is_file()])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['source_commit','duration_seconds','stages']},indent=2))
if __name__=='__main__':main()
