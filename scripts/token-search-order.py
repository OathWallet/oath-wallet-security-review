#!/usr/bin/env python3
"""Test catalog refresh ordering against production code and an explicit guard-removal mutant."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from bounded_process import logged_command
from source_state import require_source_state

PIN = 'b57d05196be319d1f0530e28f667eb89023a1c4a'
BASE = 'c7acd23bb139864a40273f405d18b479589d2b20'
MODEL = 'OathAtmosphere/Tokens/OathTokenSearchModel.swift'
HARNESS = 'Tools/CheckTokenLookup.py'
FIXTURE = 'Tools/TokenLookupValidation/TokenLookupTests.swift'
CASES = {'testOldRefreshCannotReplaceNewWalletNetworkResults': 4,
         'testResetDuringCatalogRefreshCannotPublishResults': 2}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mutate(text):
    start = text.index('            if await catalog.refreshIfNeeded() {')
    end = text.index('            return\n        }', start)
    block = text[start:end]
    guard = '                guard !Task.isCancelled, generation == request else { return }\n'
    if block.count(guard) != 2:
        raise ValueError('Expected exactly the two catalog refresh publication guards')
    return text[:start] + block.replace(guard, '') + text[end:]


def verify(name, mutant, code, text):
    case = f'-[TokenLookupTests.TokenLookupTests {name}]'
    failures = CASES[name] if mutant else 0
    state = 'failed' if mutant else 'passed'
    if code != int(mutant) or text.count(': error: ') != failures:
        raise ValueError('Unexpected assertion count or exit status')
    if f"Test Case '{case}' started." not in text or f"Test Case '{case}' {state}" not in text:
        raise ValueError('Requested XCTest case did not execute and finish')
    return failures


def sanitized(raw):
    text = raw.decode(errors='replace')
    for pattern in [r'/private/var/folders/[^\s:]+', r'/var/folders/[^\s:]+', r'/Users/[^\s:]+', r'/home/[^\s:]+']:
        text = re.sub(pattern, '<local-file>', text)
    return text.encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'scratch', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k in {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
    original = subprocess.check_output(['git', '-C', args.repo, 'show', f'{BASE}:{MODEL}'])
    current = subprocess.check_output(['git', '-C', args.repo, 'show', f'{PIN}:{MODEL}'])
    if original != current:
        raise ValueError('This replay requires the unchanged baseline production implementation')
    rows = []
    with tempfile.TemporaryDirectory(prefix='token-order-replay-') as temporary:
        for mutant in [False, True]:
            stage = 'guards-removed' if mutant else 'production'
            app = Path(temporary) / stage
            subprocess.run(['git', 'clone', '--quiet', '--local', '--no-checkout', args.repo.resolve(), app], check=True)
            subprocess.run(['git', '-C', app, 'checkout', '--quiet', '--detach', PIN], check=True)
            require_source_state(app, PIN)
            if mutant:
                (app / MODEL).write_text(mutate(current.decode()))
            hashes = {name: sha((app / name).read_bytes()) for name in (MODEL, HARNESS, FIXTURE)}
            build_log = Path(temporary) / (stage + '-build.log')
            scratch = args.scratch.resolve() / stage
            with build_log.open('w') as stream:
                code, timed = logged_command(['python3', str(app / HARNESS), '--scratch', str(scratch),
                    '--filter', 'TokenLookupTests.test(OldRefresh|ResetDuring)'], stream=stream, timeout=700, env=env)
            raw = build_log.read_bytes()
            public = sanitized(raw)
            (out / build_log.name).write_bytes(public)
            if timed or code != int(mutant) or 'Build complete!' not in raw.decode(errors='replace'):
                raise ValueError('Harness did not build or returned an unexpected result; retained log: ' + str(out / build_log.name))
            bundles = [p for p in scratch.rglob('TokenLookupTests.xctest') if p.is_dir()]
            if len(bundles) != 1:
                raise ValueError('Expected exactly one compiled host bundle')
            for name in CASES:
                log = Path(temporary) / (stage + '-' + name + '.log')
                with log.open('w') as stream:
                    code, timed = logged_command(['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)',
                        'xcrun', 'xctest', '-XCTest', 'TokenLookupTests.TokenLookupTests/' + name, str(bundles[0])],
                        stream=stream, timeout=40, env=env)
                raw = log.read_bytes()
                if timed:
                    raise ValueError('Case timed out')
                count = verify(name, mutant, code, raw.decode(errors='replace'))
                public = sanitized(raw); (out / log.name).write_bytes(public)
                rows.append(dict(source_commit=PIN, baseline_commit=BASE, stage=stage, case=name,
                    status='expected-mutation-failure' if mutant else 'passed', assertions_failed=count,
                    exit_code=code, source_hashes=hashes, log=log.name, log_sha256=sha(public),
                    raw_log_sha256=sha(raw), network_denied=True))
                (out / 'result.json').write_text(json.dumps(rows, indent=2) + '\n')
                print(stage, name, 'verified', flush=True)


if __name__ == '__main__':
    main()
