#!/usr/bin/env python3
"""Verify shipped Bitcoin signers against a fresh, peerless Bitcoin Core regtest for each suite."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BIN = {
    'bitcoin-cli': '5310684b6028bdc48e2155645408f02bd2b46e0ee0799317168e74ce9b823aba',
    'bitcoind': '58f9e3b5b8cf0cecd268cc6bf02993f3244e1a93fe8d67949ced6b52c2fdd9fb',
}
# Only these named tests and their local-fixture variables may be enabled.
CASES = [
    ('BitcoinSendTests', 'testBitcoinCoreAcceptsAndMinesRealTypeMatrix', 19543, 'oath-send', 'OATH_BITCOIN_REGTEST_DIR', 165),
    ('BitcoinSendTests', 'testBitcoinCoreMixedPoolSweepsDustAndImportedKey', 19543, 'oath-send', 'OATH_BITCOIN_REGTEST_DIR', 109),
    ('BitcoinMultisigTests', 'testBitcoinCoreMultisigConsensus', 19555, 'oath-multisig-fixture', 'OATH_MULTISIG_REGTEST_DIR', 111),
    ('AezeedBitcoinTests', 'testCoreFundedRecoveryAndMixedInputTransfer', 19643, 'aezeed-test', 'OATH_AEZEED_REGTEST_DIR', 103),
    ('ElectrumMnemonicTests', 'testCoreFundedRecoveryAndTransfersForEverySeedType', 19653, 'electrum-test', 'OATH_ELECTRUM_REGTEST_DIR', 123),
]

def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def classify(text, code, suite, case):
    name=f'-[OathBitcoinTests.{suite} {case}]'
    return code==0 and re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)", text, re.M)==[(name,'started'),(name,'passed')] and ': error:' not in text

def execute(item, core, bundle, out, env):
    suite,case,port,wallet,flag,expected_blocks = item
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', port))
    with tempfile.TemporaryDirectory(prefix='oath-regtest-') as tmp:
        datadir=Path(tmp)
        base=['-regtest',f'-datadir={datadir}',f'-rpcport={port}','-conf=unused.conf']
        (datadir/'unused.conf').touch()
        cmd=[core/'bitcoind',*base,'-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-listen=0','-networkactive=0',
             '-dnsseed=0','-fixedseeds=0','-listenonion=0','-discover=0','-txindex=1','-fallbackfee=0.00002','-printtoconsole=0']
        def cli(*args):
            return subprocess.check_output([core/'bitcoin-cli',*base,'-rpcconnect=127.0.0.1',*args],env=env,stderr=subprocess.DEVNULL,text=True,timeout=45).strip()
        node=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+45
            while time.monotonic()<deadline and node.poll() is None:
                if (datadir/'regtest/.cookie').exists():
                    try:
                        if json.loads(cli('getblockchaininfo'))['chain']=='regtest': break
                    except subprocess.CalledProcessError: pass
                time.sleep(.15)
            else: raise RuntimeError('Failed to start isolated regtest')
            assert cli('getblockcount')=='0' and json.loads(cli('getnetworkinfo'))['networkactive'] is False
            assert json.loads(cli('getpeerinfo'))==[]
            cli('createwallet',wallet)
            # No public sockets. The host test may reach only this dedicated local RPC port.
            profile=f'(version 1)(allow default)(deny network*)(allow network-outbound (remote ip "localhost:{port}"))'
            command=['/usr/bin/sandbox-exec','-p',profile,'xcrun','xctest','-XCTest',f'OathBitcoinTests.{suite}/{case}',str(bundle)]
            start=time.monotonic()
            raw=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**env,flag:tmp},timeout=240)
            text=raw.stdout.decode(errors='replace').replace(tmp,'<REGTEST>')
            log=out/(case+'.log');log.write_text(text)
            info=json.loads(cli('getblockchaininfo'));network=json.loads(cli('getnetworkinfo'))
            ok=classify(text,raw.returncode,suite,case) and info['chain']=='regtest' and info['blocks']==expected_blocks and network['networkactive'] is False and json.loads(cli('getpeerinfo'))==[]
            return dict(case=case,suite=suite,status='passed' if ok else 'failed',exit_code=raw.returncode,blocks=info['blocks'],
                        chain=info['chain'],peers=network['connections'],network_active=network['networkactive'],
                        duration_seconds=round(time.monotonic()-start,3),log=log.name,log_sha256=sha(log))
        finally:
            if node.poll() is None:
                node.terminate()
                try: node.wait(timeout=15)
                except subprocess.TimeoutExpired: node.kill();node.wait()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--core-bin',required=True,type=Path)
    p.add_argument('--expected-commit');p.add_argument('--output',required=True,type=Path);p.add_argument('--scratch',required=True,type=Path)
    a=p.parse_args();source=a.source.resolve();core=a.core_bin.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    pin=require_source_state(source,a.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    for name,digest in BIN.items():
        if sha(core/name)!=digest:raise ValueError('Unexpected Bitcoin Core 32.1 executable: '+name)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI'}}
    pkg=source/'Packages/OathBitcoin'; prefix=['swift','build','--package-path',str(pkg),'--scratch-path',str(a.scratch.resolve()),'--force-resolved-versions','--build-system','native']
    with (out/'compile.log').open('w') as log: subprocess.run([*prefix,'--build-tests','--jobs','4'],stdout=log,stderr=subprocess.STDOUT,env=env,check=True,timeout=900)
    binary=Path(subprocess.check_output([*prefix,'--show-bin-path'],env=env,text=True).strip())/'OathBitcoinPackageTests.xctest'
    rows=[]
    for case in CASES:
        row=execute(case,core,binary,out,env);rows.append(row);print(row['case'],row['status'],row['blocks'],flush=True)
    assert require_source_state(source,pin)==pin
    result=dict(check='bitcoin-core-regtest',source_commit=pin,status='passed' if all(x['status']=='passed' for x in rows) else 'failed',
                core_version='32.1',binary_sha256=BIN,executions=rows,fixture_sha256={f'{s}.swift':sha(pkg/'Tests/OathBitcoinTests'/f'{s}.swift') for s,*_ in CASES},
                scope='Five existing XCTest processes, ground-up regtest per case. Local cookie and ephemeral node wallet excluded. No public network for tests and no peers on the node.')
    log=out/'bitcoin-core-regtest.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=sha(log));(out/'bitcoin-core-regtest.json').write_text(json.dumps(result,indent=2)+'\n')
    return int(result['status']!='passed')

if __name__=='__main__':raise SystemExit(main())
