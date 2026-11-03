#!/usr/bin/env python3
"""Run existing offline NEAR ledger/journal/refresh cases from the paired replay build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from isolated_tests import classify
from source_state import require_source_state

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','build','output'):p.add_argument(name,type=Path)
    p.add_argument('--expected-commit',required=True)
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve()
    require_source_state(source,a.expected_commit)
    out.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    prefix=['--package-path',str(source/'Packages/OathDatabase'),'--build-system','native','--scratch-path',str(a.build.resolve())]
    bindir=Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],env=env,text=True).strip())
    bundles=list(bindir.glob('*.xctest'))
    if len(bundles)!=1:raise ValueError('Ambiguous bundle')
    methods=[];files=[];sha=lambda raw:hashlib.sha256(raw).hexdigest()
    for suite in ('NearLedgerTests','NearSendJournalTests','PostSendBalanceRefreshTests'):
        path=source/'Packages/OathDatabase/Tests/OathDatabaseTests'/(suite+'.swift')
        files.append({'path':str(path.relative_to(source)),'sha256':sha(path.read_bytes())})
        methods.extend(suite+'/'+name for name in re.findall(r'func (test\w+)\(',path.read_text()) if not name.startswith('testLive'))
    if len(methods)!=24 or len(set(methods))!=24:raise ValueError('Unexpected offline test selection')
    results=[]
    for method in methods:
        command=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathDatabaseTests.'+method,str(bundles[0])]
        run=subprocess.run(command,env=env,capture_output=True,timeout=120)
        raw=run.stdout+run.stderr;name=method.replace('/','-')+'.log';(out/name).write_bytes(raw)
        results.append({'method':method,'exit_code':run.returncode,'status':classify(raw.decode(errors='replace'),run.returncode),'log':name,'log_sha256':sha(raw)})
    require_source_state(source,a.expected_commit)
    report={'source_commit':a.expected_commit,'methods':results,'source_fixtures':files,'driver_sha256':sha(Path(__file__).read_bytes()),'runtime_network':'denied by sandbox-exec','excluded_live_method':'NearLedgerTests/testLiveProductionSyncAndOfflineReopen','build_requirement':'Use the unchanged after-build/source and after-build/build produced by near-balance-freshness.py at the same commit.'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    failed=[r for r in results if r['status']!='passed']
    print(json.dumps({'passed':len(results)-len(failed),'failed':len(failed)}))
    if failed:raise SystemExit(1)

if __name__=='__main__':main()
