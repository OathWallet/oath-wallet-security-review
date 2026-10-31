#!/usr/bin/env python3
"""Bounded, offline TON properties against the pinned production Swift package."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from source_state import require_source_state
from bounded_process import logged_command

ROOT = Path(__file__).resolve().parents[1]
SEED = 0x4F415448544F4E31
EXPECTED = {'testIndependentIntegerVectors', 'testBitWidthBoundaries',
            'testSeededCellRoundTripsAndMutations', 'testStructuralBoundsAndTruncation',
            'testDictionarySubsetsAndLimits'}

def passed_cases(text):
    # Xcode's native XCTest formatter uses Objective-C selector notation while
    # the legacy SwiftPM formatter uses Class.method. Admit only these five
    # exact cases, and never accept repeated or empty selections.
    return re.findall(r"^Test Case '(?:-\[TonAudit\.TonAuditProductionTests (\w+)\]|TonAuditProductionTests\.(\w+))' passed \(", text, re.M)

def successful(text, code):
    cases = [a or b for a, b in passed_cases(text)]
    return code == 0 and len(cases) == len(EXPECTED) and set(cases) == EXPECTED

def amount_vectors():
    # Python arbitrary precision is an independent arithmetic oracle, rather than
    # copying the wallet's byte-array carry/borrow implementation.
    state = SEED
    def next_word():
        nonlocal state
        state ^= (state << 13) & ((1 << 64) - 1)
        state ^= state >> 7
        state ^= (state << 17) & ((1 << 64) - 1)
        return state
    numbers = [0, (1 << 64) - 1, 1 << 64, (1 << 120) - 1]
    numbers += [((next_word() << 64) | next_word()) & ((1 << 120) - 1) for _ in range(1000)]
    result = []
    for value in numbers:
        lesser = next_word() % (value + 1)
        result.append(dict(decimal=str(value), hex=format(value, 'x'), lesser=str(lesser), difference=str(value-lesser)))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    sha = require_source_state(source, json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    out.mkdir(parents=True, exist_ok=True)
    fixture = (ROOT/'tests/TonProductionProperties.swift').read_bytes()
    vectors = (json.dumps(amount_vectors(), indent=2)+'\n').encode()
    (out/'amounts.json').write_bytes(vectors)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oath-ton-properties-') as temporary:
        work = Path(temporary)
        tests = work/'Tests/TonAudit'; tests.mkdir(parents=True)
        (tests/'TonProductionProperties.swift').write_bytes(fixture)
        (tests/'amounts.json').write_bytes(vectors)
        package = '''// swift-tools-version: 6.1
import PackageDescription
let package = Package(name: "TonAudit", platforms: [.macOS(.v14)],
 dependencies: [.package(path: SOURCE)],
 targets: [.testTarget(name: "TonAudit", dependencies: [.product(name: "OathAnkr", package: "OathAnkr")], resources: [.copy("amounts.json")])])
'''.replace('SOURCE', json.dumps(str(source/'Packages/OathAnkr')))
        (work/'Package.swift').write_text(package)
        # Carry the reviewed package's exact remote revisions into this audit
        # package. Version 2 omits the root-path-dependent originHash; the three
        # dependency identities and commits remain unchanged and mandatory.
        pins = json.loads((source/'Packages/OathAnkr/Package.resolved').read_text())['pins']
        (work/'Package.resolved').write_text(json.dumps({'version':2,'pins':pins},indent=2)+'\n')
        log = out/'ton-properties.log'
        command = ['swift','test','--package-path',str(work),'--scratch-path',str(args.scratch.resolve()),'--force-resolved-versions','--jobs','4','--filter','TonAuditProductionTests']
        with log.open('w') as stream:
            code,timed_out = logged_command(command,env=env,stream=stream,timeout=900)
        text = log.read_text(errors='replace').replace(str(work),'<HARNESS>').replace(str(source),'<SOURCE>').replace(os.path.expanduser('~'),'<HOME>')
        log.write_text(text)
        resolved = work/'Package.resolved'
        if resolved.exists():
            (out/'Package.resolved').write_bytes(resolved.read_bytes())
            if json.loads(resolved.read_text())['pins'] != pins:
                raise RuntimeError('Resolved dependencies differ from the reviewed package')
    require_source_state(source, sha)
    passed = len(passed_cases(text))
    success = successful(text, code)
    result = dict(check='ton-properties',source_commit=sha,status='passed' if success else 'failed',exit_code=code,timed_out=timed_out,
        tests_passed=passed,duration_seconds=round(time.monotonic()-started,2),seed=hex(SEED),
        fixture_sha256=hashlib.sha256(fixture).hexdigest(),vectors_sha256=hashlib.sha256(vectors).hexdigest(),
        log='ton-properties.log',log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        runtime_scope='macOS host; production OathAnkr module; synthetic inputs; no blockchain, simulator or device')
    (out/'ton-properties.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if success else 1)

if __name__ == '__main__': main()
