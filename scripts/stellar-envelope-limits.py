#!/usr/bin/env python3
"""Exercise app and pinned Stellar SDK decoder boundaries with independent wire fixtures."""
from pathlib import Path
from package_corpus import run
import re

SUITE='OathAnkrTests.StellarEnvelopeLimitTests'
CASES=['testNestedEnvelopeMatchesIndependentDigest','testRecursiveVectorHitsDepthGuard','testForgedArgumentCountHitsRemainingBytesGuard','testNoncanonicalVectorPresenceRejectedByApp','testTrailingWordRejectedByApp']
def outcome(text,code,case,before):
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    return 'passed' if code==0 and ': error:' not in text and events==[(name,'started'),(name,'passed')] else 'failed'
if __name__=='__main__':
    raise SystemExit(run(check='stellar-envelope-limits',base=None,suite=SUITE,cases=CASES,outcome=outcome,package='OathAnkr',
        local_dependencies=('OathSecp256k1','OathDiagnostics','OathTokenImages'),compare=False,
        pins={'SwiftDraw':'82699f4bdf2f075793cfa0d392eb27c59b41a3fe','stellar-ios-mac-sdk':'b5dac0a6e8ff312d597c9a3b4269b03131d66e0d','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
        overlay=Path(__file__).resolve().parents[1]/'fixtures/stellar/StellarEnvelopeLimitTests.swift',
        scope='Five network-denied synthetic Soroban XDR cases through Oath request construction, SDK decoding, canonical checks, signing and verification. No public chain or live transaction.'))
