#!/usr/bin/env python3
"""Check published CashTokens vectors, every flag byte and deterministic parser boundaries."""
import argparse
import base64
import hashlib
import json
import random
import re
import subprocess
import tempfile
from pathlib import Path
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = '41d2444c17bbfb456d4061953a3ed0e32161571b'
SEED = 20261102

def compact(n):
    if n < 253:
        return bytes([n])
    size = 2 if n <= 0xffff else 4 if n <= 0xffffffff else 8
    return bytes([{2:253, 4:254, 8:255}[size]]) + n.to_bytes(size, 'little')

def corpus(upstream, source):
    cases = []
    hashes = {}
    script = bytes.fromhex('76a914' + 'ab'*20 + '88ac')
    for kind in ('valid', 'invalid'):
        path = 'test-vectors/token-prefix-'+kind+'.json'
        raw = subprocess.check_output(['git', '-C', upstream, 'show', UPSTREAM+':'+path])
        local = source/'Packages/OathBitcoin/Tests/OathBitcoinTests/Fixtures'/('bitcoincash-tokens-'+kind+'.json')
        if local.read_bytes() != raw:
            raise ValueError('Published prefix fixture differs from the pinned upstream')
        hashes[kind] = hashlib.sha256(raw).hexdigest()
        for item in json.loads(raw):
            token = bytes.fromhex(item['prefix'])
            if kind == 'valid':
                cases.append((token + script, script))
                for end in range(1, len(token)):
                    cases.append((token[:end], None))
            else:
                cases.append((token, None))
    rng = random.Random(SEED)
    header = b'\xef' + rng.randbytes(32)
    for flags in range(256):
        body = bytearray(header + bytes([flags]))
        if flags & 64:
            body.extend(b'\x01\x44')
        if flags & 16:
            body.extend(b'\x01')
        # Enumerate the permitted encodings from the specification rather than reproducing the parser.
        legal = flags in {0x10, 0x20, 0x21, 0x22, 0x30, 0x31, 0x32, 0x60, 0x61, 0x62, 0x70, 0x71, 0x72}
        cases.append((bytes(body) + script, script if legal else None))
    for amount in [0, 1, 252, 253, 65535, 65536, 2**32-1, 2**32, 2**63-1, 2**63, 2**64-1]:
        cases.append((header + b'\x10' + compact(amount) + script, script if 0 < amount < 2**63 else None))
    # A future commitment size can be parsed without interpreting it as a spendable BCH-only output.
    for size in [1, 40, 41, 128, 252, 253, 255, 65535, 65536]:
        data = rng.randbytes(size)
        cases.extend([(header+b'\x60'+compact(size)+data+script, script), (header+b'\x60'+compact(size)+data[:-1], None)])
    for _ in range(2048):
        tail = rng.randbytes(rng.randrange(96))
        amount = rng.randrange(1, 2**63)
        cases.extend([(header+b'\x10'+compact(amount)+tail, tail), (b'\x6a'+tail, b'\x6a'+tail)])
        forbidden = rng.randrange(128, 256)
        cases.append((header+bytes([forbidden])+tail, None))
    return cases, hashes

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--expected-commit')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    pin = require_source_state(source, args.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        subprocess.run(['git','init','-q',work], check=True)
        subprocess.run(['git','-C',work,'fetch','--quiet','--depth=1','https://github.com/cashtokens/cashtokens.git',UPSTREAM], check=True)
        cases, hashes = corpus(work,source)
        b64 = lambda b: base64.b64encode(b).decode('ascii')
        payload = json.dumps([dict(wire=b64(raw),locking=None if lock is None else b64(lock)) for raw,lock in cases],separators=(',',':')).encode()
        (work/'corpus.json').write_bytes(payload)
        base=source/'Packages/OathBitcoin/Sources/OathBitcoin'
        enum = re.search(r'^public enum BitcoinError: Error, Equatable, Sendable \{[^}]+\}',(base/'BitcoinKeys.swift').read_text(),re.M)
        if enum is None:
            raise ValueError('Could not isolate the unchanged production error type')
        (work/'BitcoinError.swift').write_text(enum.group())
        subprocess.run(['swiftc','-parse-as-library',work/'BitcoinError.swift',base/'BitcoinCashTokens.swift',ROOT/'fixtures/cash-tokens/PrefixChecks.swift','-o',work/'check'], check=True)
        line = subprocess.check_output(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',work/'check',work/'corpus.json'],text=True,timeout=90).strip()
        accepted = 2*sum(lock is not None for _, lock in cases)
        rejected = 2*len(cases)-accepted
        if line != f'accepted={accepted} rejected={rejected}':
            raise ValueError('Incomplete parser corpus')
    result = dict(check='cash-token-prefixes',source_commit=pin,status='passed',upstream_revision=UPSTREAM,upstream_sha256=hashes,seed=SEED,
                  corpus_sha256=hashlib.sha256(payload).hexdigest(),accepted=accepted,rejected=rejected,unique_test_positions=len(cases),
                  scope='Unchanged production prefix reader, owned and sliced buffers, host only. Node consensus, coin selection and signing have separate evidence.')
    args.output.mkdir(parents=True,exist_ok=True)
    log=args.output/'cash-token-prefixes.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (args.output/'cash-token-prefixes.json').write_text(json.dumps(result,indent=2)+'\n')
    print(line)

if __name__=='__main__':
    main()
