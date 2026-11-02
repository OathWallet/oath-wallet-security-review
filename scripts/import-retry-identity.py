#!/usr/bin/env python3
"""Replay the same interrupted import on build 103 and the repaired wallet source."""
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

RELEASE = 'c7acd23bb139864a40273f405d18b479589d2b20'
REGRESSION = '270b3c3c20af17192b571bd176ecee1313084907'
FIX = 'e1857158db600fc171cdcca7cedd37da2722f8ad'
FIXTURE = 'Tools/CheckAezeedImport.swift'
FAILURES = ['FAIL: reused request accepted BIP39 for a committed aezeed wallet',
            'FAIL: reused request accepted a private key for a committed aezeed wallet']
SUCCESS = 'Passed 37 aezeed host integration checks:'

def fixture_case(contents):
    return contents.split('        let priorProfile = try await vault.unlockedProfile()', 1)[1].split('        let hdWallet =', 1)[0]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True,parents=True)
    out = args.output.resolve()
    before = subprocess.check_output(['git','-C',args.repository,'show',REGRESSION+':'+FIXTURE])
    after = subprocess.check_output(['git','-C',args.repository,'show',FIX+':'+FIXTURE])
    shared = fixture_case(before.decode())
    if fixture_case(after.decode()) != shared or not all(message in shared for message in FAILURES):
        raise ValueError('Compared behavior fixture changed')
    results = []
    env = {k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    with tempfile.TemporaryDirectory(prefix='wallet-import-retry-') as temporary:
        base = Path(temporary)
        for stage, commit in [('before', RELEASE), ('after', FIX)]:
            source = base/stage
            subprocess.run(['git','clone','--quiet','--no-checkout','--local',args.repository.resolve(),source],check=True)
            subprocess.run(['git','-C',source,'checkout','--quiet','--detach',commit],check=True)
            require_source_state(source,commit)
            if stage == 'before':
                (source/FIXTURE).write_bytes(before)
            env['OATH_VALIDATION_SCRATCH'] = str(base/'build')
            raw = base/(stage+'.log')
            start = time.monotonic()
            with raw.open('w') as output:
                code,expired = logged_command(['python3','Tools/CheckMultiWallet.py','--aezeed'],stream=output,timeout=1500,cwd=source,env=env)
            text = raw.read_text(errors='replace')
            changes = subprocess.check_output(['git','-C',source,'diff','--name-only','HEAD'],text=True).splitlines()
            if changes != ([FIXTURE] if stage == 'before' else []):
                raise ValueError('Unexpected changes to application code')
            actual_fixture=(source/FIXTURE).read_bytes()
            if actual_fixture!=(before if stage=='before' else after):
                raise ValueError('Fixture changed during run')
            failures = [line for line in text.splitlines() if line.startswith('FAIL:')]
            summaries = [line for line in text.splitlines() if line.startswith('Passed ') and 'aezeed host integration checks' in line]
            if stage == 'before':
                ok = code == 1 and failures == FAILURES and not summaries
            else:
                ok = code == 0 and not failures and len(summaries) == 1 and summaries[0].startswith(SUCCESS)
            if expired or not ok or not re.search(r"Build of product 'WalletValidation' complete!",text):
                raise RuntimeError(f'Unexpected {stage} outcome, exit code {code}')
            log = out/(stage+'.log')
            log.write_text('\n'.join(failures or summaries)+'\n')
            results.append(dict(stage=stage,source_commit=commit,status='reproduced' if stage=='before' else 'passed',
                                exit_code=code,fixture_sha256=hashlib.sha256(actual_fixture).hexdigest(),
                                shared_case_sha256=hashlib.sha256(shared.encode()).hexdigest(),log=log.name,
                                log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),duration_seconds=round(time.monotonic()-start,2)))
    (out/'result.json').write_text(json.dumps(dict(check='wallet-import-retry-identity',cases=results,
        scope='Production vault and SQLite, synthetic overlap and key, memory protected storage. BIP39 display adapter is substituted by the host harness; Bitcoin addresses are independently checked.'),indent=2)+'\n')

if __name__=='__main__':
    main()
