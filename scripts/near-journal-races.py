#!/usr/bin/env python3
"""Production NEAR database journal replay with synthetic providers and no runtime network."""
import argparse
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
COMMIT = '5d91d1e4dfd36c56031c7a8fb1ee305446dc54de'
OVERLAY = ROOT / 'fixtures/near-journal-races/NearAuditJournalRaceTests.swift'
PRODUCTION = 'Packages/OathDatabase/Sources/OathDatabase/NearSend.swift'
NEEDLE = 'guard try !others.contains(where:{ try NearIdentity.address($0.senderAddress) == plan.sender }) else { throw NearSendError.busy }'
REPLACEMENT = '_ = others // audit-only sender reservation bypass'
MUTANT_FAILURES = {'testConcurrentDuplicateWalletsReserveExactlyOneSender', 'testCrossWalletReservationAndCancelledAuthenticationReleasesOnlyUnsigned', 'testExactSignedBytesSurviveReopenAndUnknownBroadcastReservesSender'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','scratch','output'): p.add_argument(n,type=Path)
    p.add_argument('--mutant',action='store_true');a=p.parse_args()
    source,scratch,out=[getattr(a,n).resolve() for n in ('source','scratch','output')]
    require_source_state(source,COMMIT)
    if scratch.exists() or out.exists(): raise ValueError('Use fresh scratch and output paths')
    scratch.mkdir(parents=True);out.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    start=time.monotonic()
    def run(command,log):
        with (out/log).open('w') as f:
            r=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
        if r.returncode: raise RuntimeError(log+' failed; original log retained')
    copy=scratch/'source'
    run(['git','clone','--shared','--no-checkout',str(source),str(copy)],'clone.log')
    run(['git','-C',str(copy),'checkout','--detach',COMMIT],'checkout.log')
    production=copy/PRODUCTION
    original=production.read_text()
    if a.mutant:
        if original.count(NEEDLE)!=1:raise ValueError('Unexpected sender reservation source')
        production.write_text(original.replace(NEEDLE,REPLACEMENT))
    overlay=copy/'Packages/OathDatabase/Tests/OathDatabaseTests'/OVERLAY.name
    shutil.copyfile(OVERLAY,overlay)
    methods=[]
    for name in ('NearAuditJournalRaceTests','NearSendJournalTests'):
        file=overlay if name=='NearAuditJournalRaceTests' else copy/'Packages/OathDatabase/Tests/OathDatabaseTests/NearSendJournalTests.swift'
        methods.extend(name+'/'+m for m in re.findall(r'func (test\w+)\(',file.read_text()))
    if len(methods)!=9 or len(set(methods))!=9:raise ValueError('Unexpected test selection')
    for command,log in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['python3','--version'],'python-version.log')]:run(command,log)
    package=['--package-path',str(copy/'Packages/OathDatabase'),'--build-system','native','--scratch-path',str(scratch/'build')]
    run(['swift','build',*package,'--build-tests','--jobs','4'],'build.log')
    bindir=Path(subprocess.check_output(['swift','build',*package,'--show-bin-path'],env=env,text=True).strip())
    bundles=list(bindir.glob('*.xctest'))
    if len(bundles)!=1:raise ValueError('Ambiguous test bundle')
    results=[]
    for method in methods:
        command=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathDatabaseTests.'+method,str(bundles[0])]
        r=subprocess.run(command,env=env,capture_output=True,timeout=120)
        raw=r.stdout+r.stderr;log=out/(method.replace('/','-')+'.log');log.write_bytes(raw)
        results.append({'method':method,'exit_code':r.returncode,'status':classify(raw.decode(errors='replace'),r.returncode),'log':log.name,'log_sha256':sha(log)})
    diff=subprocess.check_output(['git','-C',str(copy),'diff'],env=env,text=True)
    changed=subprocess.check_output(['git','-C',str(copy),'diff','--name-only'],env=env,text=True).splitlines()
    if changed != ([PRODUCTION] if a.mutant else []):raise ValueError('Unexpected tracked source changes')
    if a.mutant:(out/'mutation.patch').write_text(diff)
    require_source_state(source,COMMIT)
    report={'source_commit':COMMIT,'mutant':a.mutant,'source_sha256':sha(source/PRODUCTION),'executed_source_sha256':sha(production),
            'overlay_sha256':sha(OVERLAY),'existing_fixture_sha256':sha(source/'Packages/OathDatabase/Tests/OathDatabaseTests/NearSendJournalTests.swift'),'driver_sha256':sha(Path(__file__)),'isolation_classifier_sha256':sha(ROOT/'scripts/isolated_tests.py'),
            'methods':results,'runtime_network':'denied by sandbox-exec','duration_seconds':round(time.monotonic()-start,3),
            'scope':'Production SQLite journal and real synthetic Ed25519 signatures. Concurrent duplicate-wallet reservations, database reopen, terminal receipt integrity and malformed-receipt rollback. No app UI, OS authentication, provider, blockchain, simulator or device execution.'}
    report['files']=[{'path':str(f.relative_to(out)),'sha256':sha(f)} for f in sorted(out.rglob('*')) if f.is_file()]
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    failures={r['method'] for r in results if r['status']!='passed'}
    expected={m for m in methods if m.split('/')[-1] in MUTANT_FAILURES} if a.mutant else set()
    if failures!=expected or any(r['status'] not in ('passed','failed') for r in results):raise RuntimeError('Unexpected method results: '+str(results))
    print(json.dumps({'passed':9-len(failures),'expected_mutant_failures':len(failures)}))
if __name__=='__main__':main()
