#!/usr/bin/env python3
"""Reproduce OW-2026-004 offline in a temporary SDK-only source copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import shutil
import tempfile
import time

from source_state import require_source_state
from run import sdk_case_counts

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = 'Vendor/Reown/Sources/WalletConnectNetworking/NetworkingInteractor.swift'
TEST = 'Tools/WalletConnectSDKValidation/RelayEnvelopeAuthenticationTests.swift'
BASELINE_HASH = '02557722fbebada8281aef1b1671273f8a6fc9df651f47b3789c3c096dd30728'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    config = json.loads((ROOT/'scope/source.json').read_text())
    sha = require_source_state(source, config['reviewed_commit'])
    baseline = subprocess.check_output(['git', '-C', str(source), 'show', config['historical_baseline_commit']+':'+PRODUCTION])
    assert hashlib.sha256(baseline).hexdigest() == BASELINE_HASH, 'Unexpected baseline implementation'
    fixed = (source/PRODUCTION).read_bytes()
    assert baseline != fixed, 'No production repair present'
    output.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    command = ['python3','Tools/CheckWalletConnectSDK.py','--build-system','native','--filter','RelayEnvelopeAuthenticationTests']
    results = []
    with tempfile.TemporaryDirectory(prefix='oath-relay-repro-') as temporary:
        work = Path(temporary)
        for name in ['Vendor/Reown/Sources', 'Vendor/Reown/Tests', 'Packages/OathDiagnostics', 'Tools/WalletConnectSDKValidation']:
            shutil.copytree(source/name, work/name, ignore=shutil.ignore_patterns('._*','.build','.swiftpm'))
        shutil.copy(source/'Tools/CheckWalletConnectSDK.py',work/'Tools/CheckWalletConnectSDK.py')
        path = work/PRODUCTION
        for stage, implementation, expected, expected_code in [
            ('before', baseline, {'passed':2,'skipped':0,'failed':2}, 1),
            ('after', fixed, {'passed':4,'skipped':0,'failed':0}, 0),
        ]:
            path.write_bytes(implementation)
            log = output/(stage+'.log')
            start = time.monotonic()
            with log.open('w') as stream:
                run = subprocess.run(command, cwd=work, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=360)
            text = log.read_text(errors='replace').replace(str(work),'<SOURCE-COPY>').replace(str(source),'<SOURCE>').replace(str(ROOT),'<AUDIT>').replace(os.path.expanduser('~'),'<HOME>')
            text = re.sub(r'/(?:private/)?var/folders/[^\s:]+/oath-sdk-validation-[^/\s]+', '<SDK-HARNESS>', text)
            log.write_text(text)
            cases = sdk_case_counts(text)
            result = dict(stage=stage, source_commit=sha, baseline_commit=config['historical_baseline_commit'],
                reproduction_tree='final source with only the production ingress file restored from baseline' if stage=='before' else 'exact final source',
                production_sha256=hashlib.sha256(implementation).hexdigest(),
                test_sha256=hashlib.sha256((source/TEST).read_bytes()).hexdigest(),
                command=command, exit_code=run.returncode, cases=cases,
                expected_cases=expected, duration_seconds=round(time.monotonic()-start,3),
                log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                runtime_scope='host; synthetic relay dispatcher and memory key storage; no live relay or wallet',
                reproduced=cases==expected and run.returncode==expected_code)
            results.append(result)
            (output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
            print(stage, cases, 'exit',run.returncode,flush=True)
            if not result['reproduced']:
                print('\n'.join(text.splitlines()[-45:]),flush=True)
                raise SystemExit('Unexpected regression outcome; evidence retained')
    require_source_state(source, sha)

if __name__ == '__main__':
    main()
