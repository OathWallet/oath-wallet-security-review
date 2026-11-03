#!/usr/bin/env python3
"""Replay address checksum boundaries using synthetic and public known-answer vectors."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile

from bounded_process import logged_command
from source_state import require_source_state

BASE = 'c7acd23bb139864a40273f405d18b479589d2b20'
FIX = 'b128544044a5d3043fca99c7d4c94af1af3b511c'
HARNESS = Path('Tools/CheckWalletConnectSDK.py')
FIXTURE = Path('Tools/WalletConnectSDKValidation/AddressChecksumBoundaryTests.swift')
SIGNER_ROOT = Path('Vendor/Reown/Sources/WalletConnectSigner')
VECTORS = Path('Tools/WalletConnectSDKValidation/AddressChecksumVectors.swift')
CRASHES = set()
FAILURES = {'testEmbeddedAndRepeatedPrefixesAreNotRemoved': 3, 'testInvalidHashLengthCannotTruncateOutput': 7, 'testInvalidNibblesRejectInsteadOfChangingAddress': 7, 'testNonAddressByteLengthsRejectBeforeHashing': 8, 'testUnicodeAndWhitespaceAreNotCoerced': 6, 'testUppercasePrefixPreservesAddress': 24, 'testWrongHexLengthsRejectBeforeHashing': 10}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sanitized(raw):
    text = raw.decode('utf-8', errors='replace')
    text = re.sub(r'/private/var/folders/[^\s:]+', '<temporary-file>', text)
    text = re.sub(r'/var/folders/[^\s:]+', '<temporary-file>', text)
    text = re.sub(r'/Users/[^\s:]+', '<local-file>', text)
    text = re.sub(r'/home/[^\s:]+', '<runner-file>', text)
    return text.encode()


def validate_case(name, stage, code, text):
    full_name = f"-[SDKTests.AddressChecksumBoundaryTests {name}]"
    if f"Test Case '{full_name}' started." not in text:
        raise ValueError('Requested case did not start')
    if stage == 'before' and name in CRASHES:
        if code != -signal.SIGTRAP or f"Test Case '{full_name}' passed" in text:
            raise ValueError('Expected isolated original process to trap')
        return 'trapped'
    failures = FAILURES.get(name, 0) if stage == 'before' else 0
    state = 'failed' if failures else 'passed'
    if code != int(failures > 0) or text.count(': error: ') != failures:
        raise ValueError('Unexpected case exit or assertion count')
    if f"Test Case '{full_name}' {state}" not in text:
        raise ValueError('Missing case completion')
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'scratch', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if k in {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
    rows = []
    fixture = subprocess.check_output(['git', '-C', str(args.repo), 'show', f'{FIX}:{FIXTURE}'])
    harness = subprocess.check_output(['git', '-C', str(args.repo), 'show', f'{FIX}:{HARNESS}'])
    vectors = subprocess.check_output(['git', '-C', str(args.repo), 'show', f'{FIX}:{VECTORS}'])
    names = re.findall(r'func (test\w+)\(', fixture.decode())
    if len(names) != 9 or len(set(names)) != 9:
        raise ValueError('Fixture case list changed')
    with tempfile.TemporaryDirectory(prefix='address-checksum-replay-') as temporary:
        for stage, rev in [('before', BASE), ('after', FIX)]:
            app = Path(temporary) / stage
            subprocess.run(['git', 'clone', '--quiet', '--local', '--no-checkout',
                            args.repo.resolve(), app], check=True)
            subprocess.run(['git', '-C', app, 'checkout', '--quiet', '--detach', rev], check=True)
            require_source_state(app, rev)
            production_hashes = {str(p.relative_to(app)): sha(p.read_bytes())
                                 for p in sorted((app / SIGNER_ROOT).rglob('*.swift'))}
            # Overlay only the regression fixture and build harness. Every SDK
            # implementation remains exactly at the revision being replayed.
            (app / FIXTURE).write_bytes(fixture)
            (app / VECTORS).write_bytes(vectors)
            (app / HARNESS).write_bytes(harness)
            scratch = args.scratch.resolve() / stage
            env['OATH_SDK_VALIDATION_SCRATCH'] = str(scratch)
            build_log = Path(temporary) / (stage + '-build.log')
            with build_log.open('w') as stream:
                code, timed = logged_command(
                    ['python3', str(app / HARNESS), '--filter',
                     'AddressChecksumBoundaryTests.testNonzeroOriginDataSliceRetainsAddress'],
                    stream=stream, timeout=600, env=env)
            if code or timed:
                raise ValueError('Harness build or valid control failed: ' + build_log.read_text()[-1000:])
            candidates = [p for p in scratch.rglob('*.xctest') if p.is_dir()]
            if len(candidates) != 1:
                raise ValueError('Expected exactly one compiled host test bundle')
            for name in names:
                log = Path(temporary) / (stage + '-' + name + '.log')
                command = ['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)',
                           'xcrun', 'xctest', '-XCTest', 'SDKTests.AddressChecksumBoundaryTests/' + name,
                           str(candidates[0])]
                with log.open('w') as stream:
                    code, timed = logged_command(command, stream=stream, timeout=30, env=env)
                raw = log.read_bytes()
                if timed:
                    raise ValueError('Case timed out')
                status = validate_case(name, stage, code, raw.decode(errors='replace'))
                public_log = sanitized(raw)
                log_name = stage + '-' + name + '.log'
                (out / log_name).write_bytes(public_log)
                rows.append(dict(stage=stage, source_commit=rev, case=name, status=status,
                                 exit_code=code, raw_log_sha256=sha(raw),
                                 log=log_name, log_sha256=sha(public_log),
                                 fixture_sha256=sha(fixture), harness_sha256=sha(harness),
                                 source_hashes=production_hashes, vectors_sha256=sha(vectors)))
                (out / 'result.json').write_text(json.dumps(rows, indent=2) + '\n')
                print(stage, name, status, flush=True)


if __name__ == '__main__':
    main()
