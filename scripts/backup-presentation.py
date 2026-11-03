#!/usr/bin/env python3
"""Replay stale all-wallet backup presentation callbacks on pinned models."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from bounded_process import logged_command
from source_state import require_source_state

BASE='00d26c005fbc3f811615b23b865bb50ef7b6619f'
FIX='a904515793b087289140e4411924f030b3fe61ff'
MODEL='OathAtmosphere/Home/OathAllWalletBackupPage.swift'
OVERLAYS=['Tools/CheckBackupPresentation.py','Tools/CheckBackupPresentation.swift']
TAILS=['old completion cannot set new failure','old completion cannot advance new progress','new preparation remains active','old record is not published','current completion counts once','current record appears']
NAMES=[p+': '+n for p in ['successful read','failed read'] for n in TAILS]+['current failure remains visible','current failure counts once','failed read cannot invent a record']
FAILURES={'failed read: '+TAILS[i] for i in (0,1,4)}

def sha(data): return hashlib.sha256(data).hexdigest()

def validate(stage,code,text):
    if stage not in ('before','after'): raise ValueError('Unknown stage')
    expected=[('FAIL' if stage=='before' and n in FAILURES else 'PASS',n) for n in NAMES]
    failures=3 if stage=='before' else 0
    if re.findall(r'^(PASS|FAIL): (.+)$',text,re.M)!=expected: raise ValueError('Incorrect case identities or results')
    if text.splitlines().count(f'Backup presentation checks: {15-failures} passed, {failures} failed')!=1: raise ValueError('Missing or duplicate summary')
    if code!=(1 if failures else 0): raise ValueError('Unexpected harness exit')
    return {'passed':15-failures,'failed':failures,'cases':[{'name':n,'status':s.lower()} for s,n in expected]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();repo=args.repo.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    files={p:subprocess.check_output(['git','-C',str(repo),'show',f'{FIX}:{p}']) for p in OVERLAYS}
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    rows=[]
    with tempfile.TemporaryDirectory(prefix='backup-presentation-replay-') as temp:
        for stage,rev in [('before',BASE),('after',FIX)]:
            app=Path(temp)/stage
            subprocess.run(['git','clone','--quiet','--local','--no-checkout',str(repo),str(app)],check=True)
            subprocess.run(['git','-C',str(app),'checkout','--quiet','--detach',rev],check=True)
            require_source_state(app,rev)
            model_sha=sha((app/MODEL).read_bytes())
            for name,data in files.items():(app/name).write_bytes(data)
            raw_log=Path(temp)/(stage+'.log');start=time.monotonic()
            with raw_log.open('w') as stream:
                code,timed=logged_command(['python3',str(app/OVERLAYS[0])],stream=stream,timeout=180,env=env)
            raw=raw_log.read_bytes();text=raw.decode(errors='replace')
            sanitized=re.sub(r'/(?:private/)?var/folders/[^\s:]+','<temporary-file>',text)
            sanitized=re.sub(r'/(?:Users|home)/[^\s:]+','<local-file>',sanitized).encode()
            (out/(stage+'.log')).write_bytes(sanitized)
            if timed:raise ValueError('Replay timed out')
            result=validate(stage,code,text)
            if model_sha!=sha((app/MODEL).read_bytes()):raise ValueError('Production model changed')
            rows.append(dict(stage=stage,source_commit=rev,production_sha256=model_sha,
                fixture_hashes={p:sha(b) for p,b in files.items()},exit_code=code,duration_seconds=round(time.monotonic()-start,2),
                raw_log_sha256=sha(raw),log=stage+'.log',log_sha256=sha(sanitized),**result))
            (out/'result.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(stage,result['passed'],'passed',result['failed'],'failed (expected)',flush=True)

if __name__=='__main__':main()
