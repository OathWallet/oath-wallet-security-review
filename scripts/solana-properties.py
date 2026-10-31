#!/usr/bin/env python3
"""Bounded, offline Solana properties against the pinned production Swift package."""
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
SEED = 0x4F415448534F4C31
EXPECTED = {'testIndependentBase58Vectors', 'testIndependentCurveExistenceVectors', 'testAllTruncationsAndNoncanonicalLengths',
            'testSignatureSlotsAndImmutableMessages', 'testSeededMutationsCannotRewriteUnselectedBytes'}

def passed_cases(text):
    # Xcode's native XCTest formatter uses Objective-C selector notation while
    # the legacy SwiftPM formatter uses Class.method. Admit only these named
    # exact cases, and never accept repeated or empty selections.
    return re.findall(r"^Test Case '(?:-\[SolanaAudit\.SolanaAuditProductionTests (\w+)\]|SolanaAuditProductionTests\.(\w+))' passed \(", text, re.M)

def successful(text, code):
    cases = [a or b for a, b in passed_cases(text)]
    return code == 0 and len(cases) == len(EXPECTED) and set(cases) == EXPECTED

def encoding_vectors():
    # Independent Python big-integer division, not a port of the byte carry loop.
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    state = SEED
    def byte():
        nonlocal state
        state ^= (state << 13) & ((1 << 64) - 1)
        state ^= state >> 7
        state ^= (state << 17) & ((1 << 64) - 1)
        return state & 255
    rows = []
    inputs = [bytes([v])*n for n in [1,2,31,32,33,63,64,16] for v in [0,255]]
    inputs += [bytes(byte() for _ in range(32 if i % 2 == 0 else 64)) for i in range(512)]
    for data in inputs:
        value = int.from_bytes(data, 'big'); digits = ''
        while value:
            value, digit = divmod(value,58); digits = alphabet[digit] + digits
        leading = len(data) - len(data.lstrip(b'\0'))
        rows.append({'hex':data.hex(), 'base58':'1'*leading+digits})
    return rows

def curve_vectors():
    # Edwards equation -x^2+y^2 = 1+d*x^2*y^2 over F_(2^255-19).
    # Python modular inversion + Euler's criterion is independent of the
    # production TweetNaCl limb multiplication and square-root exponentiation.
    p = 2**255 - 19
    d = -121665 * pow(121666, -1, p) % p
    state = SEED
    values = [0, 1, 2, p-1, p, p+1, 2**255-1]
    for _ in range(512):
        raw = bytearray()
        for _ in range(32):
            state ^= (state << 13) & ((1 << 64)-1)
            state ^= state >> 7
            state ^= (state << 17) & ((1 << 64)-1)
            raw.append(state & 255)
        values.append(int.from_bytes(raw, 'little') & (2**255-1))
    rows = []
    for y in values:
        denominator = (d*y*y + 1) % p
        x2 = (y*y - 1) * pow(denominator, -1, p) % p
        exists = x2 == 0 or pow(x2, (p-1)//2, p) == 1
        for sign in [0,1]:
            rows.append({'hex':(y | (sign << 255)).to_bytes(32,'little').hex(), 'isPoint':exists})
    return rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    sha = require_source_state(source, json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    out.mkdir(parents=True, exist_ok=True)
    fixture = (ROOT/'tests/SolanaProductionProperties.swift').read_bytes()
    vectors = (json.dumps(encoding_vectors(), indent=2)+'\n').encode()
    (out/'encodings.json').write_bytes(vectors)
    curve = (json.dumps(curve_vectors(), indent=2)+'\n').encode()
    (out/'curve.json').write_bytes(curve)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oath-solana-properties-') as temporary:
        work = Path(temporary)
        tests = work/'Tests/SolanaAudit'; tests.mkdir(parents=True)
        (tests/'SolanaProductionProperties.swift').write_bytes(fixture)
        (tests/'encodings.json').write_bytes(vectors)
        (tests/'curve.json').write_bytes(curve)
        transactions = (source/'Packages/OathAnkr/Tests/OathAnkrTests/Fixtures/WalletConnect/solana.json').read_bytes()
        (tests/'transactions.json').write_bytes(transactions)
        (out/'transactions.json').write_bytes(transactions)
        package = '''// swift-tools-version: 6.1
import PackageDescription
let package = Package(name: "SolanaAudit", platforms: [.macOS(.v14)],
 dependencies: [.package(path: SOURCE)],
 targets: [.testTarget(name: "SolanaAudit", dependencies: [.product(name: "OathAnkr", package: "OathAnkr")], resources: [.copy("encodings.json"), .copy("curve.json"), .copy("transactions.json")])])
'''.replace('SOURCE', json.dumps(str(source/'Packages/OathAnkr')))
        (work/'Package.swift').write_text(package)
        # Carry the reviewed package's exact remote revisions into this audit
        # package. Version 2 omits the root-path-dependent originHash; the three
        # dependency identities and commits remain unchanged and mandatory.
        pins = json.loads((source/'Packages/OathAnkr/Package.resolved').read_text())['pins']
        (work/'Package.resolved').write_text(json.dumps({'version':2,'pins':pins},indent=2)+'\n')
        log = out/'solana-properties.log'
        command = ['swift','test','--package-path',str(work),'--scratch-path',str(args.scratch.resolve()),'--force-resolved-versions','--jobs','4','--filter','SolanaAuditProductionTests']
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
    result = dict(check='solana-properties',source_commit=sha,status='passed' if success else 'failed',exit_code=code,timed_out=timed_out,
        tests_passed=passed,duration_seconds=round(time.monotonic()-started,2),seed=hex(SEED),
        fixture_sha256=hashlib.sha256(fixture).hexdigest(),vectors_sha256=hashlib.sha256(vectors).hexdigest(),
        transactions_sha256=hashlib.sha256(transactions).hexdigest(),curve_sha256=hashlib.sha256(curve).hexdigest(),
        log='solana-properties.log',log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        runtime_scope='macOS host; production OathAnkr module; synthetic inputs; no blockchain, simulator or device')
    (out/'solana-properties.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if success else 1)

if __name__ == '__main__': main()
