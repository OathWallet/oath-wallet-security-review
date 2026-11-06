#!/usr/bin/env python3
"""Exercise EVM signed intent, replay protection and Safe thresholds in production code."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
from isolated_tests import classify
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '32701474fefbed3840878e35f6111e8d494e1f02'
FIXTURE = 'fixtures/evm-consent/EVMConsentReviewTests.swift'
TARGET = 'Packages/OathAnkr/Tests/OathAnkrTests/EVMConsentReviewTests.swift'
CRYPTO = 'Packages/OathAnkr/Sources/OathAnkr/EVMSendCrypto.swift'
GUARD = 'signed.bytes == (try signedBytes(plan,signed.signature,authorization:signed.authorizationSignature)),'
MUTANT_CASE = 'OathAnkrTests.EVMConsentReviewTests/testWireBindingMutationControl'
NETWORK_DENIAL = '(version 1) (allow default) (deny network*)'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def validate_mutant(cases, out):
    if len(cases) != 1 or cases[0]['selector'] != MUTANT_CASE:
        raise ValueError('Wrong mutation-control selection')
    c = cases[0]
    body = (out / c['log']).read_text()
    errors = re.findall(r'^.* error: .* : (.*)$', body, re.M)
    if c['status'] != 'failed' or c['exit_code'] != 1 or not errors:
        raise ValueError('Mutation control did not fail by assertion')
    if len(errors) != 4 or set(re.findall(r'Wire binding removed: (\d+)', '\n'.join(errors))) != {'0', '1', '2', '3'} or not all('Wire binding removed:' in e for e in errors):
        raise ValueError('Unexpected failure in mutation control')
    if 'Executed 1 test' not in body:
        raise ValueError('Missing terminal test summary')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'scratch', 'output']:
        parser.add_argument(name, type=Path)
    a = parser.parse_args()
    source, scratch, out = [getattr(a, n).resolve() for n in ['source', 'scratch', 'output']]
    require_source_state(source, COMMIT)
    if scratch.exists() or out.exists():
        raise ValueError('Fresh directories required')
    scratch.mkdir(parents=True); out.mkdir(parents=True)
    env = {k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    started = time.monotonic()
    def clean(text):
        for path, label in [(scratch,'<SCRATCH>'),(source,'<SOURCE>'),(out,'<OUTPUT>'),(Path.home(),'<HOME>')]:
            text=text.replace(str(path),label)
        return text
    def command(cmd, log, timeout=120):
        start=time.monotonic()
        try:
            r=subprocess.run(cmd,env=env,capture_output=True,timeout=timeout)
            code,text=r.returncode,(r.stdout+r.stderr).decode(errors='replace')
        except subprocess.TimeoutExpired as e:
            code,text=-1,(e.stdout or b'').decode(errors='replace')+'\nAUDIT COMMAND TIMEOUT\n'
        log.write_text(clean(text))
        return code,round(time.monotonic()-start,3)
    for cmd,name in [(['xcodebuild','-version'],'xcode.log'),(['swift','--version'],'swift.log'),(['python3','--version'],'python.log')]:
        if command(cmd,out/name)[0]: raise ValueError('Toolchain discovery failed')
    stages=[]
    for stage in ['production','mutation-control']:
        work=scratch/stage; dest=out/stage;work.mkdir();dest.mkdir()
        archive=work/'packages.tar'
        with archive.open('wb') as f:
            subprocess.run(['git','-C',str(source),'archive',COMMIT,'Packages'],stdout=f,env=env,check=True)
        tree=work/'source';tree.mkdir()
        with tarfile.open(archive) as tar: tar.extractall(tree,filter='data')
        archive_hash=sha(archive);archive.unlink()
        (tree/TARGET).write_bytes((ROOT/FIXTURE).read_bytes())
        if stage == 'mutation-control':
            p=tree/CRYPTO; text=p.read_text()
            if text.count(GUARD)!=1: raise ValueError('Mutation no longer matches pinned source')
            p.write_text(text.replace(GUARD,''))
        manifest=[{'path':str(p.relative_to(tree)),'sha256':sha(p)} for p in sorted((tree/'Packages').rglob('*')) if p.is_file()]
        (dest/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        lock=tree/'Packages/OathAnkr/Package.resolved';lock_hash=sha(lock)
        (dest/'Package.resolved').write_bytes(lock.read_bytes())
        prefix=['--package-path',str(tree/'Packages/OathAnkr'),'--scratch-path',str(work/'build'),
                '--build-system','native','--force-resolved-versions']
        print(stage,'building production implementations',flush=True)
        code,duration=command(['swift','build',*prefix,'--build-tests','--jobs','4'],dest/'build.log',1800)
        if code: raise ValueError('Build failed; retained evidence; not a vulnerability')
        if sha(lock)!=lock_hash: raise ValueError('Dependency lock changed')
        r=subprocess.run(['swift','test',*prefix,'list','--skip-build','--disable-swift-testing'],env=env,capture_output=True,timeout=120)
        (dest/'discovery.log').write_text(clean(r.stdout.decode(errors='replace')))
        (dest/'discovery-stderr.log').write_text(clean(r.stderr.decode(errors='replace')))
        selectors=r.stdout.decode().splitlines()
        if r.returncode or any(not re.fullmatch(r'[\w.]+/\w+',s) for s in selectors): raise ValueError('Discovery failed')
        selected=([MUTANT_CASE] if stage=='mutation-control' else [s for s in selectors if s.startswith(('OathAnkrTests.EVMConsentReviewTests/','OathAnkrTests.EVMSendTests/','OathAnkrTests.EVMMultisigTests/','OathAnkrTests.WalletConnectEVMRequestTests/','OathAnkrTests.WalletConnectEVMQuoteTests/','OathAnkrTests.WalletConnectApprovalEditingTests/','OathAnkrTests.WalletConnectEVMActionTests/','OathAnkrTests.PermissionTests/'))])
        selected=[s for s in selected if s != 'OathAnkrTests.EVMMultisigTests/testSafeExecutionNativeTokensThresholdsAndReplays']
        if len(selected) != (1 if stage=='mutation-control' else 28): raise ValueError('Unexpected inherited test selection')
        fixture_cases=[s for s in selectors if s.startswith('OathAnkrTests.EVMConsentReviewTests/')]
        if len(fixture_cases)!=6 or not set(selected).issubset(selectors): raise ValueError('Wrong test selection')
        bundles=list((work/'build').glob('*/debug/*.xctest'))
        if len(bundles)!=1: raise ValueError('Ambiguous test executable')
        binary=bundles[0]/'Contents/MacOS/OathAnkrPackageTests'
        logs=dest/'cases';logs.mkdir()
        def run(selector):
            log=logs/(hashlib.sha256(selector.encode()).hexdigest()[:16]+'.log')
            code,duration=command(['/usr/bin/sandbox-exec','-p',NETWORK_DENIAL,'xcrun','xctest','-XCTest',selector,str(bundles[0])],log)
            return {'selector':selector,'status':classify(log.read_text(),code),'exit_code':code,
                    'duration_seconds':duration,'log':str(log.relative_to(out)),'log_sha256':sha(log)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: cases=list(pool.map(run,selected))
        totals={s:sum(c['status']==s for c in cases) for s in ['passed','skipped','failed']}
        (dest/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
        if stage=='mutation-control': validate_mutant(cases,out)
        elif totals['skipped'] or totals['failed']: raise ValueError('Production tests failed; investigate retained logs')
        stages.append({'stage':stage,'source_commit':COMMIT,'source_archive_sha256':archive_hash,
                       'dependency_lock_sha256':lock_hash,'build_exit_code':code,'build_duration_seconds':duration,
                       'executable_sha256':sha(binary),'runtime_network':'denied','totals':totals,'cases':cases})
        print(stage,totals,flush=True)
    require_source_state(source,COMMIT)
    result={'schema_version':1,'source_commit':COMMIT,'fixture':FIXTURE,'fixture_sha256':sha(ROOT/FIXTURE),
            'driver_sha256':sha(Path(__file__)),'helper_sha256':{n:sha(ROOT/'scripts'/n) for n in ['isolated_tests.py','source_state.py']},
            'duration_seconds':round(time.monotonic()-started,3),'stages':stages,
            'mutation_is_production_vulnerability':False,'whole_wallet_complete':False,
            'files':[{'path':str(p.relative_to(out)),'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__': main()
