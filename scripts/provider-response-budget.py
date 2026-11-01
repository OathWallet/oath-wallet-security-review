#!/usr/bin/env python3
"""Replay production transports against deterministic oversized and interrupted responses."""
import re
import sys
from pathlib import Path
from package_corpus import run

BASE = '8c2eec02bddeafd9fadb1aae1db9d49a67bc4a64'
BITCOIN = {
    'testUnknownLengthStopsAtTheLimit': 'Reader waited for the oversized response tail',
    'testActualBytesOverrideShortLengthHeader': 'Reader waited for the oversized response tail',
    'testOversizedThrottleStillAppliesCooldown': 'Reader waited for the oversized response tail',
    'testMissing404DoesNotConsumeTheBody': 'Reader waited for an irrelevant 404 body',
    'testExactAndZeroLimitsAcceptCompleteBodies': None,
    'testCancelDuringBodyReleasesAdmission': None,
    'testSmallThrottleEnvelopeStillAppliesCooldown': None,
    'testSmallHTTPPolicyErrorKeepsItsClassification': None,
    'testInterruptedBodyPreservesCauseAndReleasesAdmission': None,
}
RATES = {
    'testOversizePrecedesRemoteDisconnect': 'Downloaded past the rate limit until disconnect',
    'testOversizedFailureKeepsHTTPStatus': 'Lost the HTTP status while waiting for oversized tail',
    'testBodyExactlyAtLimitIsComplete': None,
    'testInterruptedSmallBodyPreservesError': None,
}

def verdict(suite, cases, text, code, case, before):
    name = f'-[{suite} {case}]'
    events = re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)", text, re.M)
    errors = [line.split(': error: ', 1)[-1] for line in text.splitlines() if ': error:' in line]
    if before and cases[case]:
        if code == 1 and events == [(name, 'started'), (name, 'failed')] and errors == [name+' : failed - '+cases[case]]:
            return 'reproduced'
    elif code == 0 and events == [(name, 'started'), (name, 'passed')] and not errors:
        return 'passed'
    return 'failed'

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('bitcoin', 'rates', 'fallbacks'):
        raise SystemExit('Choose bitcoin, rates or fallbacks, followed by source and output arguments')
    mode = sys.argv.pop(1)
    bitcoin = mode != 'rates'
    package, cls, cases = ('OathBitcoin','BitcoinResponseBudgetTests',BITCOIN) if bitcoin else ('OathExchangeRates','RateResponseBudgetTests',RATES)
    overlay = None
    if mode == 'fallbacks':
        cls = 'BitcoinFallbackStreamTests'
        cases = dict.fromkeys(['testFeeFallbackMovesToNextHostAtLimit','testParentFallbackAuthenticatesNextHostsTransaction'],'Fallback consumed the oversized response tail')
        overlay = Path(__file__).resolve().parents[1]/'fixtures/provider-response/BitcoinFallbackStreamTests.swift'
    suite = package+'Tests.'+cls
    deps = ('OathSecp256k1','OathDiagnostics')
    pins = {'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'}
    if not bitcoin:
        deps += ('OathDatabase','OathBitcoin','OathAnkr','OathTokenImages')
        pins.update({'GRDB.swift':'533286eab041d826ed4a46c56b213fa3d2cebb7a','SwiftDraw':'82699f4bdf2f075793cfa0d392eb27c59b41a3fe','stellar-ios-mac-sdk':'b5dac0a6e8ff312d597c9a3b4269b03131d66e0d'})
    raise SystemExit(run(check=mode+'-response-budget', base=BASE,
        suite=suite, cases=cases, outcome=lambda *args: verdict(suite,cases,*args), package=package,
        overlay=overlay,local_dependencies=deps,pins=pins,scope='Synthetic URLProtocol stream against the production transport. Separate network-denied host process for each case and revision.'))
