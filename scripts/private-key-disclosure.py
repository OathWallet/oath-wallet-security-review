#!/usr/bin/env python3
"""Replay OW-2026-058 against pinned production models with identical host fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from bounded_process import logged_command
from source_state import require_source_state

BASE = 'e8e6ba9fb910a1ca31c60e0d8dac8ac84583091b'
FIX = 'b5621109b64d606dcf6cd906d2c4f2c2f9e78686'
MODEL = 'OathAtmosphere/Wallet/OathPrivateKeyModel.swift'
OVERLAYS = ['Tools/CheckMultiWallet.py', 'Tools/CheckPrivateKeyDisclosure.swift']
NAMES = [
    'authorization stops at warning',
    'acknowledged value is available while active',
    'native back removes displayed value',
    'active warning may re-reveal same authorization',
    'lock or background clears revealed value and selection',
    'old acknowledgement cannot reveal after cancellation',
    'repeated cleanup preserves only public accounts',
    'reopening requires another authorization and warning',
    'unacknowledged value is discarded',
    'new authorization keeps its own value',
    'fresh disclosure also clears on background',
]
FAILURES = {NAMES[i] for i in (4, 5, 6, 10)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(stage, code, text):
    if stage not in ('before', 'after'):
        raise ValueError('Unknown stage')
    cases = re.findall(r'^(PASS|FAIL): (.+)$', text, re.M)
    expected = [('FAIL' if stage == 'before' and name in FAILURES else 'PASS', name) for name in NAMES]
    passed, failed = (7, 4) if stage == 'before' else (11, 0)
    summary = f'Private-key disclosure checks: {passed} passed, {failed} failed; synthetic reader, production model; no UIKit or OS authentication.'
    if cases != expected or text.splitlines().count(summary) != 1 or code != (1 if failed else 0):
        raise ValueError('Unexpected case identities, outcomes, completion or exit status')
    return {'passed': passed, 'failed': failed, 'cases': [{'name': n, 'status': s.lower()} for s, n in cases]}


def sanitized(data):
    text = data.decode('utf-8', errors='replace')
    for pattern, replacement in [(r'/private/var/folders/[^\s:]+', '<temporary-file>'),
                                 (r'/var/folders/[^\s:]+', '<temporary-file>'),
                                 (r'/Users/[^\s:]+', '<local-file>'),
                                 (r'/home/[^\s:]+', '<runner-file>')]:
        text = re.sub(pattern, replacement, text)
    return text.encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'scratch', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    repo, scratch, out = (p.resolve() for p in (args.repo, args.scratch, args.output))
    out.mkdir(parents=True, exist_ok=True)
    overlays = {p: subprocess.check_output(['git', '-C', str(repo), 'show', f'{FIX}:{p}']) for p in OVERLAYS}
    rows = []
    with tempfile.TemporaryDirectory(prefix='private-key-disclosure-') as temporary:
        for stage, revision in [('before', BASE), ('after', FIX)]:
            app = Path(temporary) / stage
            subprocess.run(['git', 'clone', '--quiet', '--local', '--no-checkout', str(repo), str(app)], check=True)
            subprocess.run(['git', '-C', str(app), 'checkout', '--quiet', '--detach', revision], check=True)
            require_source_state(app, revision)
            model_hash = sha((app / MODEL).read_bytes())
            for name, data in overlays.items():
                (app / name).write_bytes(data)
            env = {k: v for k, v in os.environ.items() if k in {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
            env['OATH_VALIDATION_SCRATCH'] = str(scratch / stage)
            raw_log = Path(temporary) / (stage + '.log')
            command = ['python3', str(app / OVERLAYS[0]), '--private-key-disclosure']
            start = time.monotonic()
            with raw_log.open('w') as stream:
                code, timed = logged_command(command, stream=stream, timeout=1200, env=env)
            raw = raw_log.read_bytes()
            public_log = sanitized(raw)
            log_name = stage + '.log'
            (out / log_name).write_bytes(public_log)
            if timed:
                raise ValueError('Timed out; no passing result')
            result = validate(stage, code, raw.decode(errors='replace'))
            if model_hash != sha((app / MODEL).read_bytes()):
                raise ValueError('Production model changed during replay')
            rows.append(dict(stage=stage, source_commit=revision, production_model_sha256=model_hash,
                             overlays={p: sha(data) for p, data in overlays.items()},
                             command=['python3', OVERLAYS[0], '--private-key-disclosure'],
                             exit_code=code, duration_seconds=round(time.monotonic() - start, 2),
                             raw_log_sha256=sha(raw), log=log_name, log_sha256=sha(public_log), **result))
            (out / 'result.json').write_text(json.dumps(rows, indent=2) + '\n')
            print(stage, result['passed'], 'passed;', result['failed'], 'failed (expected)', flush=True)


if __name__ == '__main__':
    main()
