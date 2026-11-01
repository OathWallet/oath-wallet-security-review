#!/usr/bin/env python3
"""Verify the SVG decoder regression on two pinned app commits."""
import re
import signal
from package_corpus import run

BASE = '34ba87a3e0b2beb27bd1acdb618e480f5faefb9d'
SUITE = 'OathTokenImagesTests.ArtworkReferenceDepthTests'
CRASH = 'testShadowedCycleCannotReachRenderer'
OVER = 'testSharedLeafFirstCannotBypassDepthBudget'
CASES = [OVER,CRASH,'testSharedRootFirstCannotBypassDepthBudget','testExactlyAtDepthBudgetInBothOrders','testSiblingReferencesMayShareOneID']

def outcome(text, code, case, before):
    name = '-['+SUITE+' '+case+']'
    events = re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors = [line for line in text.splitlines() if ': error:' in line]
    if case not in CASES: return 'failed'
    if before and case == CRASH:
        return 'expected-signal-11' if code==-signal.SIGSEGV and events==[(name,'started')] and not errors else 'failed'
    if before and case == OVER:
        suffix = name+' : XCTAssertThrowsError failed: did not throw an error - Over-budget SVG must be rejected before rendering'
        ok = code==1 and events==[(name,'started'),(name,'failed')] and len(errors)==1 and errors[0].endswith(suffix)
        return 'expected-depth-assertion' if ok else 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raise SystemExit(run(check='svg-reference-graph',base=BASE,suite=SUITE,cases=CASES,outcome=outcome,
        scope='Production token decoder and pinned drawing dependency; five synthetic images/cases per revision. Separate offline host XCTest process per case.'))
