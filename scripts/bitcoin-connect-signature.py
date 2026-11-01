#!/usr/bin/env python3
"""Compare the app's real signing and journal-verification boundaries using synthetic keys."""
from package_corpus import run
import re

BASE='e4d48f85ee43236c388b987dfec52feadfae2551'
SUITE='OathBitcoinTests.BitcoinConnectSignatureProofTests'
PEER=['testPeerECDSAPartialCannotReplaceWalletSignature','testPeerTaprootPartialCannotReplaceWalletSignature']
REJECT=['testEmptyFinalScriptCannotEnterJournalVerification','testTaprootProofMustUseReviewedHashType']+[f'testForeignFinal{kind}ProofRejected' for kind in ['Legacy','Nested','Native','Taproot']]
CONTROL='testValidRequestedInputsRemainVerifiable'
CASES=PEER+REJECT+[CONTROL]

def outcome(text,code,case,before):
    if case not in CASES:return 'failed'
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors=[line.split(': error: ',1)[-1] for line in text.splitlines() if ': error:' in line]
    if before and case!=CONTROL:
        assertion='XCTAssertFalse failed - Foreign signature was returned for a different transaction' if case in PEER else 'XCTAssertThrowsError failed: did not throw an error'
        if code==1 and events==[(name,'started'),(name,'failed')] and errors==[name+' : '+assertion]:return 'expected-signature-failure'
        return 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raise SystemExit(run(check='bitcoin-connect-signature',base=BASE,suite=SUITE,cases=CASES,outcome=outcome,
        package='OathBitcoin',local_dependencies=('OathSecp256k1','OathDiagnostics'),
        pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
        scope='Nine synthetic host cases per revision. Peer partials, final-data substitution, empty unlocking and requested Taproot hash mode. No network during test execution.'))
