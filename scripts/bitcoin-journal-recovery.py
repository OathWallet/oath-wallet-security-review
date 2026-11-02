#!/usr/bin/env python3
"""Exercise stored payment substitution and reset-time upgrades in isolated host processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from source_state import require_source_state

BEFORE = '8425bc0597b6bd4ab36f8710d0e8d939d786a7fa'
AFTER = '5071662dc0700d7011795035aa14b5795a4a1e3a'
SUITE = 'BitcoinSendSettlementTests'
SUBSTITUTION = 'testRecoveryRejectsSignedBytesForAnotherPaymentUsingTheSameInputs'
UPGRADE = [
    ('BalanceHistoryTests','testUpgradeDuringPendingResetDoesNotTripTheSnapshotWriteFence'),
    ('HomeReadIndexTests','testMigrationBackfillsExistingRows'),
    ('WalletNamingTests','testUpgradeDoesNotBlockAnInterruptedWalletReset'),
]
CONTROLS = ['testRecoveryJournalChecksNetworkReceiptAndLegacyRowsOnEveryChain',
            'testDigestMigrationReopensAnExistingSignedPaymentWithoutRewritingIt',
            'testRecoveryJournalDetectsWitnessChangeThatPreservesBitcoinTxid']

def fixture(source, revision, suite, name):
    path = f'Packages/OathDatabase/Tests/OathDatabaseTests/{suite}.swift'
    data = subprocess.check_output(['git','-C',source,'show',revision+':'+path])
    match = re.findall(rb'^    func '+name.encode()+rb'\(.*?^    }\n',data,re.M|re.S)
    if len(match) != 1: raise ValueError('Missing or ambiguous test '+name)
    return match[0]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--before',action='store_true')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--scratch',required=True,type=Path)
    args=parser.parse_args()
    source=args.source.resolve(); output=args.output.resolve(); output.mkdir(parents=True,exist_ok=True)
    pin=require_source_state(source,BEFORE if args.before else AFTER)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL','SDKROOT'}}
    build=['swift','build','--package-path',str(source/'Packages/OathDatabase'),'--scratch-path',str(args.scratch.resolve()),
           '--build-system','native','--force-resolved-versions']
    with (output/'build.log').open('w') as log:
        subprocess.run(build+['--build-tests','--jobs','4'],env=env,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=1500)
    binary=Path(subprocess.check_output(build+['--show-bin-path'],env=env,text=True).strip())/'OathDatabasePackageTests.xctest'
    selected=[(SUITE,SUBSTITUTION),*UPGRADE]
    if not args.before: selected.extend((SUITE,k) for k in CONTROLS)
    rows=[]
    for suite,name in selected:
        data=fixture(source,pin,suite,name)
        if name not in CONTROLS and data!=fixture(source,BEFORE,suite,name):raise ValueError('Compared test changed: '+name)
        selector='OathDatabaseTests.'+suite+'/'+name
        start=time.monotonic()
        proc=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)','xcrun','xctest','-XCTest',selector,str(binary)],env=env,capture_output=True,timeout=120)
        body=(proc.stdout+proc.stderr).decode(errors='replace').replace(str(source),'<SOURCE>').replace(str(args.scratch.resolve()),'<SCRATCH>')
        label=f'-[OathDatabaseTests.{suite} {name}]'
        events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",body,re.M)
        errors=[l.partition(': error: ')[2] for l in body.splitlines() if ': error: ' in l]
        if args.before:
            reason='Substituted payment was eligible for rebroadcast after an empty history' if name==SUBSTITUTION else 'SQLite error 19: Wallet reset in progress'
            ok=(events==[(label,'started'),(label,'failed')] and proc.returncode==1 and len(errors)==1 and reason in errors[0])
        else:
            ok=(events==[(label,'started'),(label,'passed')] and proc.returncode==0 and not errors and 'Executed 1 test, with 0 failures' in body)
        log=output/(name+'.log');log.write_text(body)
        if not ok:raise RuntimeError('Unexpected outcome: '+selector)
        rows.append(dict(selector=selector,status='reproduced' if args.before else 'passed',exit_code=proc.returncode,
                         fixture_sha256=hashlib.sha256(data).hexdigest(),log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                         duration_seconds=round(time.monotonic()-start,3)))
    require_source_state(source,pin)
    result=dict(check='bitcoin-journal-and-reset',source_commit=pin,status='reproduced' if args.before else 'passed',cases=rows,
                scope='Local synthetic signed payments and migrated SQLite stores; execution denied network access.')
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified',len(rows),'isolated recovery cases on',pin)
if __name__=='__main__':main()
