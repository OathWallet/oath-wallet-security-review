#!/usr/bin/env python3
"""Host-test the pinned production restore model with synthetic boundary adapters."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from source_state import require_source_state

COMMIT = 'a904515793b087289140e4411924f030b3fe61ff'
MODEL = 'OathAtmosphere/Wallet/OathCloudRestoreModel.swift'
ROOT = Path(__file__).resolve().parents[1]
NAMES = ['discovery publishes current entries', 'unknown entry cannot be selected',
    'download owns busy state', 'download progress uses current entry',
    'busy selection cannot replace attempt', 'duplicate restore cannot start another read',
    'successful restore saves exactly once', 'successful restore clears busy without error',
    'stop clears discovered and selected entries', 'wrong password permits retry',
    'wrong password replaces secure field identity', 'wrong password never reaches local save',
    'account change after decryption prevents save', 'canceled read failure cannot set current error',
    'canceled failure cannot reset new discovery', 'local save remains busy until completion',
    'late old save cannot finish new discovery', 'late old save cannot complete newer attempt',
    'new failed attempt cannot repeat old save', 'discovery failure clears restore selection',
    'invalidated read cannot overwrite discovery failure', 'discovery invalidation prevents pending save']
MUTANT_FAILURES = {'canceled read failure cannot set current error',
    'canceled failure cannot reset new discovery', 'invalidated read cannot overwrite discovery failure'}

def validate(code, text, mutant=False):
    expected = [('FAIL' if mutant and n in MUTANT_FAILURES else 'PASS', n) for n in NAMES]
    cases = re.findall(r'^(PASS|FAIL): (.+)$', text, re.M)
    failures = 3 if mutant else 0
    if cases != expected or code != (1 if mutant else 0):
        raise ValueError('Incorrect lifecycle case identities, results or exit code')
    if text.splitlines().count(f'Cloud restore lifecycle checks: {22-failures} passed, {failures} failed') != 1:
        raise ValueError('Incorrect lifecycle summary')
    return cases

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--mutate-catch-guard', action='store_true', help='Negative control: remove one guard in a temporary model copy only')
    args = parser.parse_args()
    source = args.source.resolve(); out = args.output.resolve()
    require_source_state(source, COMMIT)
    original = (source / MODEL).read_bytes()
    # Remove only the two imports satisfied by explicitly synthetic adapters.
    model = original.decode()
    for line in ['import OathDiagnostics\n', 'import OathCloudBackup\n']:
        if model.count(line) != 1: raise ValueError('Unexpected production import boundary')
        model = model.replace(line, '')
    if args.mutate_catch_guard:
        guard = '                guard let self, self.generation == token, self.attempt == attempt, !Task.isCancelled else { return }'
        if model.count(guard) != 1: raise ValueError('Mutation boundary changed')
        model = model.replace(guard, '                guard let self else { return }')
    fixture = ROOT / 'fixtures/cloud-restore-lifecycle/Checks.swift'
    env = {k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    out.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='restore-lifecycle-') as directory:
        path = Path(directory); (path/'Model.swift').write_text(model)
        compile_result = subprocess.run(['xcrun','swiftc','-swift-version','6','-parse-as-library', str(fixture),str(path/'Model.swift'),'-o',str(path/'checks')], env=env, capture_output=True, timeout=120)
        (out/'compile.log').write_bytes(compile_result.stdout+compile_result.stderr)
        if compile_result.returncode: raise ValueError('Host compilation failed; see compile.log')
        result = subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(path/'checks')], env=env,capture_output=True,timeout=45)
        log = result.stdout + result.stderr
        (out/'checks.log').write_bytes(log)
        cases = validate(result.returncode, log.decode(), args.mutate_catch_guard)
    require_source_state(source, COMMIT)
    report = dict(source_commit=COMMIT,source_file=MODEL,source_sha256=sha(original),compiled_model_sha256=sha(model.encode()),
        fixture_sha256=sha(fixture.read_bytes()),script_sha256=sha(Path(__file__).read_bytes()),
        passed=19 if args.mutate_catch_guard else 22, failed=3 if args.mutate_catch_guard else 0,
        deliberate_mutation=args.mutate_catch_guard, exit_code=result.returncode,duration_seconds=round(time.monotonic()-start,2),
        log_sha256=sha(log),cases=[dict(name=n,status=s.lower()) for s,n in cases],
        scope='Unchanged production model body; synthetic cloud, cryptography, diagnostics and local-save boundaries. No iCloud, database, real secrets, UI, simulator or device.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Mutation detected: 3 expected failures' if args.mutate_catch_guard else '22 cloud restore lifecycle checks passed')

if __name__ == '__main__': main()
