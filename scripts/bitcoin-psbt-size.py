#!/usr/bin/env python3
"""Reproduce the Bitcoin WalletConnect PSBT budget with synthetic shared parents."""
from package_corpus import run
import re

BASE='005a2fbf683773f3dffc51abe82f6d794271249a'
SUITE='OathBitcoinTests.ConnectPlanSizeTests'
OVERSIZED='testCompactRequestCannotReturnOversizedUnusableReviewPlan'
EXACT='testPacketLimitIncludesMapFieldsAndTerminators'
CASES=[OVERSIZED,EXACT,'testSmallerRequestStillValidates']

def outcome(text, code, case, before):
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)", text, re.M)
    errors=[line.split(': error: ',1)[-1] for line in text.splitlines() if ': error:' in line]
    if case not in CASES: return 'failed'
    if before and case in (OVERSIZED, EXACT):
        expected=(
            ['failed - Review returned a packet of 509260 bytes beyond the signing limit',
             'XCTAssertNoThrow failed: threw error "invalidPSBT" - A returned plan must pass revalidation']
            if case==OVERSIZED else ['XCTAssertThrowsError failed: did not throw an error']
        )
        if code==1 and events==[(name,'started'),(name,'failed')] and [x.rstrip() for x in errors]==[(name+' : '+x).rstrip() for x in expected]:
            return 'expected-size-failure'
        return 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raise SystemExit(run(check='bitcoin-psbt-size',base=BASE,suite=SUITE,cases=CASES,outcome=outcome,
        package='OathBitcoin',local_dependencies=('OathSecp256k1','OathDiagnostics'),
        pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
        scope='Public Bitcoin request/review, signed-plan revalidation and encoder byte boundary. Synthetic parents, no keys exported, network denied per process.'))
