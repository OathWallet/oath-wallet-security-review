#!/usr/bin/env python3
"""Run Oath's existing BCH signing matrix against a temporary, peerless Bitcoin Cash Node."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from bitcoin_core_regtest import classify
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BIN = {'bitcoind':'84aee425e62a580c17cc9defc370b499ee1cba04942d6cca7e036680ea88e77d',
       'bitcoin-cli':'47c9e49a4700b2b8468409d10e8ee82dd7d5aea37168cc6fbade87af1eb22f14'}
CASES = [('BitcoinCashSendTests','testBCHNAcceptsMinesAddressAndFeeMatrix',141),
         ('BitcoinCashSendTests','testBCHNRejectsNonForkIDSignatureAndModifiedRecipientAmount',102),
         ('BitcoinCashMultisigTests','testBitcoinCashCoreMultisigConsensus',343)]

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def compile_tests(source, scratch, temp, out, env):
    packages = temp/'Packages'
    packages.mkdir()
    pkg = packages/'OathBitcoin'
    shutil.copytree(source/'Packages/OathBitcoin',pkg,ignore=shutil.ignore_patterns('.build','.swiftpm','._*'))
    for name in ('OathDiagnostics','OathSecp256k1'):
        (packages/name).symlink_to(source/'Packages'/name,target_is_directory=True)
    fixture = pkg/'Tests/OathBitcoinTests/BitcoinCashSendTests.swift'
    original = sha(fixture)
    text = fixture.read_text()
    replacements = [
        ('URL(fileURLWithPath:"/opt/homebrew/bin/docker")','URL(fileURLWithPath:ProcessInfo.processInfo.environment["OATH_BCH_TEST_CLI"]!)'),
        ('["exec","oath-bch-send-regtest","/bchn/bitcoin-cli","-regtest","-datadir=/data","-rpcwallet=oath-bch-send",method]',
         '["-regtest","-rpcconnect=127.0.0.1","-datadir="+ProcessInfo.processInfo.environment["OATH_BCH_TEST_DATA"]!,"-rpcport="+ProcessInfo.processInfo.environment["OATH_BCH_TEST_PORT"]!,"-rpcwallet=oath-bch-send",method]'),
        ('URL(fileURLWithPath:"/tmp/oath-bch-regtest-receipts.json")','URL(fileURLWithPath:ProcessInfo.processInfo.environment["OATH_BCH_TEST_RECEIPTS"]!)')]
    for old,new in replacements:
        if text.count(old)!=1:
            raise ValueError('RPC fixture transport or receipt location changed')
        text=text.replace(old,new)
    fixture.write_text(text)
    args=['swift','build','--package-path',pkg,'--scratch-path',scratch.resolve(),'--build-system','native','--force-resolved-versions']
    with (out/'compile.log').open('w') as log:
        subprocess.run([*args,'--build-tests','--jobs','4'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
    binary=Path(subprocess.check_output([*args,'--show-bin-path'],env=env,text=True).strip())/'OathBitcoinPackageTests.xctest'
    return binary, original, sha(fixture)

def run_case(binary,tools,env,temp,out,suite,case,expected_blocks):
    multisig = suite == 'BitcoinCashMultisigTests'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',19566 if multisig else 0));port=sock.getsockname()[1]
    data=temp/case;data.mkdir(mode=0o700)
    args=['-regtest',f'-datadir={data}',f'-rpcport={port}']
    # Use only loopback. The node starts with no peers or P2P listeners, then RPC disables P2P entirely.
    profile=f'(version 1)(allow default)(deny network*)(allow network-bind (local ip "localhost:{port}"))(allow network-inbound (local ip "localhost:{port}"))'
    cmd=['/usr/bin/sandbox-exec','-p',profile,tools/'bitcoind',*args,'-rpcbind=127.0.0.1','-rpcallowip=127.0.0.1','-listen=0','-connect=0','-dnsseed=0','-listenonion=0','-discover=0','-txindex=1','-fallbackfee=0.00002']
    def cli(*params):
        return subprocess.check_output([tools/'bitcoin-cli',*args,'-rpcconnect=127.0.0.1',*params],text=True,stderr=subprocess.DEVNULL,timeout=20).strip()
    receipts=data/'receipts.json'
    with (out/(case+'-node.log')).open('w') as stream:
        process=subprocess.Popen(cmd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+35
            while time.monotonic()<deadline and process.poll() is None:
                try:
                    if (data/'regtest/.cookie').is_file() and json.loads(cli('getblockchaininfo'))['chain']=='regtest':
                        break
                except subprocess.CalledProcessError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError('Test node did not start')
            cli('setnetworkactive','false')
            if cli('getblockcount')!='0' or json.loads(cli('getpeerinfo')) or json.loads(cli('getnetworkinfo'))['networkactive']:
                raise RuntimeError('Test chain isolation failed')
            cli('createwallet','oath-multisig-fixture' if multisig else 'oath-bch-send')
            case_env=dict(env,OATH_BCH_REGTEST='1',OATH_BCH_TEST_CLI=str(tools/'bitcoin-cli'),OATH_BCH_TEST_DATA=str(data),
                          OATH_BCH_TEST_PORT=str(port),OATH_BCH_TEST_RECEIPTS=str(receipts))
            if multisig:
                case_env['OATH_BCH_MULTISIG_REGTEST_DIR']=str(data)
            selector='OathBitcoinTests.'+suite+'/'+case
            local=f'(version 1)(allow default)(deny network*)(allow network-outbound (remote ip "localhost:{port}"))'
            result=subprocess.run(['/usr/bin/sandbox-exec','-p',local,'xcrun','xctest','-XCTest',selector,binary],env=case_env,capture_output=True,text=True,timeout=600)
            output=result.stdout+result.stderr
            (out/(case+'.log')).write_text(output)
            if not classify(output,result.returncode,suite,case):
                raise RuntimeError('Missing real passing BCH test: '+case)
            height=int(cli('getblockcount'))
            if height!=expected_blocks or json.loads(cli('getpeerinfo')) or json.loads(cli('getnetworkinfo'))['networkactive']:
                raise RuntimeError('Unexpected local chain result')
            row=dict(selector=selector,blocks=height,peers=0,network_active=False)
            if multisig:
                confirmed=[]
                for block in range(103,height+1,2):
                    block_hash=cli('getblockhash',str(block))
                    txids=json.loads(cli('getblock',block_hash,'1'))['tx']
                    if len(txids)!=2:
                        raise ValueError('Missing confirmed multisig spend')
                    confirmed.append(txids[1])
                if len(set(confirmed))!=121:
                    raise ValueError('Incomplete multisig policy coverage')
                path=out/'multisig-confirmations.json'
                path.write_text(json.dumps(confirmed,indent=2)+'\n')
                row.update(confirmed_policies=121,confirmed_txids_sha256=sha(path))
            if receipts.exists():
                entries=json.loads(receipts.read_bytes())
                if len(entries)!=20 or len({v['txid'] for v in entries})!=20 or max(v['inputs'] for v in entries)!=255:
                    raise ValueError('Incomplete confirmed transaction matrix')
                (out/'receipts.json').write_bytes(receipts.read_bytes())
                row.update(receipts=len(entries),receipt_sha256=sha(receipts))
            return row
        finally:
            process.terminate()
            try:process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill();process.wait()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    for name in ('node-bin','scratch','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected-commit')
    args=parser.parse_args();source=args.source.resolve();tools=args.node_bin.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    pin=require_source_state(source,args.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    for name,digest in BIN.items():
        if sha(tools/name)!=digest:raise ValueError('Unexpected BCHN executable: '+name)
    env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','TMPDIR','SDKROOT','DEVELOPER_DIR','LC_ALL','LANG','CI')}
    with tempfile.TemporaryDirectory(prefix='oath-bchn-regtest-') as scratch:
        temp=Path(scratch)
        binary,original,adapted=compile_tests(source,args.scratch,temp,out,env)
        rows=[run_case(binary,tools,env,temp,out,suite,case,blocks) for suite,case,blocks in CASES]
    result=dict(check='bchn-regtest',source_commit=pin,status='passed',tools=BIN,upstream_version='29.2.0',
                original_test_sha256=original,adapted_test_sha256=adapted,results=rows,
                scope='Unmodified production package; existing assertions, isolated native RPC test adapter and temporary receipt path. The three test chains are private regtest. The multisig fixture runs unchanged.')
    log=out/'bchn-regtest.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=sha(log));(out/'bchn-regtest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified three isolated BCHN test chains')

if __name__=='__main__':
    main()
