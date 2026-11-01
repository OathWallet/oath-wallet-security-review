#!/usr/bin/env python3
"""Run BIP32 invalid-key vector 5 and its valid root control against the real importer."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from package_corpus import run

REV='c0644a054fd1568ecbfc9c2b656ad5200b16ff74'
DIGEST='e5e00a8289db2f681052cf24a745320afc225e66b25d1e489a7c884d2fc7f11f'
SUITE='OathBitcoinTests.BIP32PublishedWireTests'
def fixture(raw):
    if hashlib.sha256(raw).hexdigest()!=DIGEST:raise ValueError('Unexpected published BIP32 document')
    doc=raw.decode()
    part=doc.split('===Test vector 5===')[1].split('==Acknowledgements==')[0]
    vectors=re.findall(r'^\* ([1-9A-HJ-NP-Za-km-z]+) \((.+)\)$',part,re.M)
    if len(vectors)!=16:raise ValueError('Missing published invalid vectors')
    valid=re.search(r'^\*\* ext prv: ([1-9A-HJ-NP-Za-km-z]+)$',doc.split('===Test vector 1===')[1].split('===Test vector 2===')[0],re.M)[1]
    cases={};tests=[]
    for i,(key,reason) in enumerate(vectors,1):
        case=f'testInvalidVector{i:02}';cases[case]=reason
        tests.append('func '+case+'() {\n  reject('+json.dumps(key)+')\n}')
    tests.append('func testValidMasterControl() throws { let s='+json.dumps(valid)+'; let result=try UTXONetwork.bitcoin.decodeImport(s); XCTAssertTrue(result.extended==s && result.bytes.count==32) }')
    code='''import XCTest
@testable import OathBitcoin
final class BIP32PublishedWireTests: XCTestCase {
    func reject(_ value: String) {
        do { _ = try UTXONetwork.bitcoin.decodeImport(value); XCTFail("Published invalid private import was accepted") } catch {}
    }
'''+ '\n'.join(tests)+'\n}\n';cases['testValidMasterControl']=None
    return code,cases

def outcome(text,code,case,before):
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors=[line.split(': error: ',1)[-1] for line in text.splitlines() if ': error:' in line]
    if before and case in {'testInvalidVector02','testInvalidVector04','testInvalidVector06'}:
        return 'reproduced' if code==1 and events==[(name,'started'),(name,'failed')] and errors==[name+' : failed - Published invalid private import was accepted'] else 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raw=subprocess.check_output(['curl','-fsSL','--retry','2','--max-time','60','https://raw.githubusercontent.com/bitcoin/bips/'+REV+'/bip-0032.mediawiki'])
    code,cases=fixture(raw)
    with tempfile.TemporaryDirectory() as t:
        overlay=Path(t)/'BIP32PublishedWireTests.swift';overlay.write_text(code)
        raise SystemExit(run(check='bip32-import-vectors',base='7a737d938422d2a6d50ae3143bbca27bd95a87c2',suite=SUITE,cases=cases,outcome=outcome,overlay=overlay,package='OathBitcoin',
            local_dependencies=('OathDiagnostics','OathSecp256k1'),pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
            scope='Pinned BIP32 vector 5, 16 invalids, plus valid vector 1 root. Public inputs only. Private-import API, not a general watch-only import test. Each case runs network-denied.'))
