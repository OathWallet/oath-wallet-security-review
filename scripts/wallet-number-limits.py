#!/usr/bin/env python3
"""Run the release-tag traps and repair controls on a disposable wallet checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
RELEASE = 'c7acd23bb139864a40273f405d18b479589d2b20'
FIX = 'dce615da563de5d0510dbfc86325f61cfe925f62'
CASES = ('testExistingMaximumDisplayIndexAllowsAnUnrelatedWallet', 'testMaximumSortOrderKeepsRelativeOrderWhenAppending')
PATCHES = ('family-index', 'sql-counters')
ADDRESS_FIX = '3e33b299fab0d4c1a6d5e245cc5881f878d243e0'
GAP_CASE = 'testNewHDAddressesLeaveRoomForTheFullDiscoveryGap'
ADDRESS_CASES = ('testReceiveRejectsOverflowingStoredChildIndex', 'testChangeRejectsOverflowingStoredChildIndex',
                 'testStateRejectsUnrepresentableDiscoveryIndex', GAP_CASE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('repo', 'scratch', 'output'):
        parser.add_argument(field, type=Path)
    parser.add_argument('--bitcoin-addresses', action='store_true', help='Replay the Bitcoin address allocation and discovery window cases')
    args = parser.parse_args()
    patches = ('bitcoin-indices',) if args.bitcoin_addresses else PATCHES
    fixture_files = ['Packages/OathDatabase/Tests/OathDatabaseTests/BitcoinLedgerTests.swift'] if args.bitcoin_addresses else [
        'Tools/CheckMultiWalletEnvelope.swift', 'Packages/OathDatabase/Tests/OathDatabaseTests/WalletNamingTests.swift']
    suite = 'BitcoinLedgerTests' if args.bitcoin_addresses else 'WalletNamingTests'
    scratch, out = args.scratch.resolve(), args.output.resolve()
    out.mkdir(exist_ok=True, parents=True)
    env = {k: v for k, v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    results = []
    with tempfile.TemporaryDirectory(prefix='wallet-numbering-') as tmp:
        checkout = Path(tmp)/'app'
        subprocess.run(['git','clone','--local','--quiet','--no-checkout',args.repo.resolve(),checkout],check=True)
        for stage, sha in [('before', RELEASE), ('after', ADDRESS_FIX if args.bitcoin_addresses else FIX)]:
            subprocess.run(['git','-C',checkout,'checkout','--quiet','--detach',sha],check=True)
            require_source_state(checkout,sha)
            if stage=='before':
                for folder in patches:
                    subprocess.run(['git','-C',checkout,'apply',ROOT/'evidence/5.0.1-build103'/folder/'tag-failure.patch'],check=True)
            env['OATH_VALIDATION_SCRATCH'] = str(scratch/'envelope')
            def run(label, command, exit_codes, required):
                raw = Path(tmp)/(stage+'-'+label+'.log')
                with raw.open('w') as stream:
                    code, timed_out = logged_command(command,stream=stream,timeout=1200,cwd=checkout,env=env)
                data = raw.read_bytes()
                text = data.decode(errors='replace')
                if timed_out or code not in exit_codes or not all(re.search(pattern,text) for pattern in required):
                    # The checkout uses public synthetic inputs. Limit output to build and test diagnostics.
                    for line in text.splitlines():
                        if ': error:' in line or 'Test Case ' in line or 'SIGTRAP' in line:
                            print(line.replace(str(checkout), '<SOURCE>')[:500])
                    raise RuntimeError(f'{stage}/{label} had an unexpected result, exit {code}')
                results.append(dict(stage=stage, check=label, source_commit=sha, exit_code=code,
                                    raw_log_sha256=hashlib.sha256(data).hexdigest(), matched=required))
                (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
                print(stage, label, code, flush=True)
            if not args.bitcoin_addresses:
                envelope = [sys.executable,'Tools/CheckMultiWallet.py','--envelope']
                run('envelope',envelope,[1] if stage=='before' else [0],
                    [r"Build of product 'WalletValidation' complete!",r'SIGTRAP' if stage=='before' else r'Passed 87 multi-wallet envelope checks'])
            args_build = ['swift','build','--package-path','Packages/OathDatabase','--build-system','native','--scratch-path',str(scratch/'sql')]
            run('database-build',args_build+['--build-tests','--jobs','4'],[0],[r'Build complete!'])
            binary = Path(subprocess.check_output(args_build+['--show-bin-path'],cwd=checkout,env=env,text=True).strip())/'OathDatabasePackageTests.xctest'
            cases = ADDRESS_CASES if args.bitcoin_addresses else CASES
            if args.bitcoin_addresses and stage=='after':
                cases += ('testReservedChangeDoesNotConsumeTheDiscoveryGap',)
            for case in cases:
                command = ['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest','OathDatabaseTests.'+suite+'/'+case,str(binary)]
                conditions = [re.escape(case)+r"\]' started\."]
                if stage=='after':
                    conditions.append(re.escape(case)+r"\]' passed \(")
                expected_codes = [-5,133] if stage=='before' else [0]
                if stage=='before' and case==GAP_CASE:
                    expected_codes = [1]
                    conditions += [r'with 4 failures \(0 unexpected\)', 'Issued an address whose payment', 'A refused address must never be marked issued']
                run(case,command,expected_codes,conditions)
            if stage=='before':
                # Only discard the known fixture overlays in this script's disposable checkout.
                subprocess.run(['git','-C',checkout,'restore','--',*fixture_files],check=True)
            require_source_state(checkout,sha)

if __name__=='__main__':
    main()
