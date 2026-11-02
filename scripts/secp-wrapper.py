#!/usr/bin/env python3
"""Test the shipped Swift/FFI curve wrapper with independent points and signatures."""
import re
import runpy
import tempfile
from pathlib import Path
from package_corpus import ROOT, run

SUITE='OathBitcoinTests.CurveBoundaryTests'
CASES=['testIndependentRecoverableAndDERSignatures','testMalformedAndMalleableSignatures','testScalarAndTweakLimits','testNonzeroStartOffsetOfValidBuffers']

def outcome(text,code,case,before):
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|passed|skipped|failed)",text,re.M)
    return 'passed' if code==0 and events==[(name,'started'),(name,'passed')] and ': error: ' not in text else 'failed'

if __name__=='__main__':
    vectors=runpy.run_path(str(Path(__file__).with_name('secp-wrapper-vectors.py')))['vector']()
    data=(ROOT/'fixtures/secp256k1/CurveBoundaryTests.swift.in').read_text()
    for key,value in vectors.items():
        marker='@'+key+'@'
        assert marker in data
        data=data.replace(marker,value)
    assert not re.search(r'@[A-Za-z]+@',data)
    with tempfile.TemporaryDirectory() as temp:
        fixture=Path(temp)/'CurveBoundaryTests.swift';fixture.write_text(data)
        raise SystemExit(run(check='secp-wrapper',base='7ecfa2c163704d363ebe6dc16b60151dc8a7cd78',suite=SUITE,cases=CASES,
            outcome=outcome,overlay=fixture,compare=False,package='OathBitcoin',local_dependencies=('OathDiagnostics','OathSecp256k1'),
            pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
            scope='Network-denied production Swift curve wrapper, seven exported operations including both tweak overloads. Independent RFC6979 computation and OpenSSL secp256k1 point multiplication; neither constant-time behavior nor memory erasure is demonstrated.'))
