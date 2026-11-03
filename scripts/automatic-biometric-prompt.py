#!/usr/bin/env python3
"""Replay the release's pure prompt policy without OS authentication or Keychain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from source_state import require_source_state

PIN = 'c7acd23bb139864a40273f405d18b479589d2b20'
FILES = ['OathAtmosphere/Passcode/OathAutomaticBiometricPrompt.swift',
         'Tools/CheckAutomaticBiometricPrompt.swift']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    require_source_state(source, PIN)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items()
           if k in {'PATH', 'HOME', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
    record = dict(source_commit=PIN, status='failed', assertion_count=0,
                  scope='Pure prompt lifecycle; no OS authentication, Keychain or simulator',
                  sources={p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in FILES})
    try:
        with tempfile.TemporaryDirectory(prefix='oath-prompt-policy-') as temp:
            binary = Path(temp) / 'prompt-check'
            commands = [('compile', ['swiftc', *FILES, '-o', str(binary)]),
                        ('execute', ['sandbox-exec', '-p', '(version 1)(allow default)(deny network*)', str(binary)])]
            for name, command in commands:
                result = subprocess.run(command, cwd=source, env=env, capture_output=True, timeout=120)
                log = result.stdout + result.stderr
                log = log.replace(str(source).encode(), b'<source>').replace(temp.encode(), b'<work>')
                (out / (name + '.log')).write_bytes(log)
                record[name + '_exit'] = result.returncode
                result.check_returncode()
            if log.strip() != b'Passed 19 automatic biometric prompt lifecycle checks.':
                raise ValueError('Unexpected test summary')
            record.update(status='passed', assertion_count=19, network_denied=True)
    finally:
        record['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.log')}
        (out / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Passed 19 production prompt-policy checks; no simulator or Keychain used.')


if __name__ == '__main__':
    main()
