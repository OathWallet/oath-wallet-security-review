#!/usr/bin/env python3
"""Exercise the production parent fetcher with an intercepted URLSession and no network."""
from pathlib import Path
import re
from package_corpus import run

BASE='005a2fbf683773f3dffc51abe82f6d794271249a'
SUITE='OathBitcoinTests.BitcoinParentBudgetTests'
OVER='testParentsCannotRetainMoreThanOnePacket'
CASES=[OVER,'testSmallBatchReturnsBothHashVerifiedParents']

def outcome(text,code,case,before):
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors=[line.split(': error: ',1)[-1] for line in text.splitlines() if ': error:' in line]
    if case not in CASES: return 'failed'
    if case == OVER and before:
        return 'expected-retention-failure' if code==1 and events==[(name,'started'),(name,'failed')] and errors==[name+' : failed - Six hash-verified parents exceeded the packet budget'] else 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raise SystemExit(run(check='bitcoin-parent-budget',base=BASE,suite=SUITE,cases=CASES,outcome=outcome,
        package='OathBitcoin',local_dependencies=('OathSecp256k1','OathDiagnostics'),
        pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
        overlay=Path(__file__).resolve().parents[1]/'fixtures/bitcoin-psbt-size/BitcoinParentBudgetTests.swift',
        scope='Same synthetic URLProtocol test overlay on both pinned app archives. Six unique hash-verified parents over budget and two below budget. OS network denied.'))
