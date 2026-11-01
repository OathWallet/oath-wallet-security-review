#!/usr/bin/env python3
"""Reproduce artwork URL filtering at source, thumbnail, loader and redirect boundaries."""
import re
from package_corpus import run

BASE='7da0cd82a81bce01a0f6ed29ccae9d33f5c13a95'
SUITE='OathTokenImagesTests.ArtworkHostPolicyTests'
literal_inputs=['0x7f.0.0.1','127.0x0.1','0x7f.1','0x7f.0x1','0xA9.0xfe.0.1','%30%78%37%66.1','0xc0.0250.1.1']
EXPECT={
 'testResolverRecognizedIPv4SpellingsAreRejected':[r'XCTAssertFalse failed - '+re.escape(host) for host in literal_inputs],
 'testEscapedDelimitersAndMalformedLabelsAreRejected':[re.escape(f'XCTAssertNil failed: "https://{h}/a" - {h}') for h in ['cdn..example','-cdn.example','cdn-.example']],
 'testHomeZoneIsRejected':[re.escape(f'XCTAssertNil failed: "https://{h}/a" - {h}') for h in ['home.arpa','pRiNtEr.HOME.arpa']],
 'testSignedThumbnailCannotIntroduceNumericOriginal':[r'XCTAssertEqual failed: .*https://0x7f\.1/asset.* is not equal to .*cache\.tonapi\.io/.*'],
 'testUntrustedLogoNeverReachesLoaderTransport':[r'XCTAssertNil failed: "vector\(SwiftDraw\.SVG.*',re.escape('XCTAssertEqual failed: ("1") is not equal to ("0")')],
 'testRedirectRejectsNumericHost':[re.escape('XCTAssertNil failed: "https://0x7f.0.0.1/asset"')]
}
CASES=list(EXPECT)+['testPublicDNSAndGatewayCompatibility','testRedirectPreservesPublicDestination']
def outcome(text,code,case,before):
    if case not in CASES: return 'failed'
    name=f'-[{SUITE} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors=[line.partition(': error: ')[2] for line in text.splitlines() if ': error:' in line]
    prefix=name+' : '
    if before and case in EXPECT:
        wanted=EXPECT[case]
        if code!=1 or events!=[(name,'started'),(name,'failed')] or len(errors)!=len(wanted):return 'failed'
        if any(not e.startswith(prefix) for e in errors):return 'failed'
        if any(sum(bool(re.fullmatch(pattern,e[len(prefix):])) for e in errors)!=1 for pattern in wanted):return 'failed'
        return 'expected-admission-failure'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raise SystemExit(run(check='artwork-host-policy',base=BASE,suite=SUITE,cases=CASES,outcome=outcome,
        scope='Eight offline cases per revision. Darwin numeric parser, production artwork gate, thumbnail expansion, injected loader transport and unresumed URLSession redirect delegate. No TLS, DNS or private service contact.'))
