#!/usr/bin/env python3
"""Reproduce pairing URI query-boundary confusion using identical production-parser tests."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time

from run import sdk_case_counts
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'e352f56d0fb3be035c3600e646e3f9133adb9ef4'
TEST = 'Tools/WalletConnectSDKValidation/URIBoundaryTests.swift'
INPUTS = ['Vendor/Reown/Sources', 'Vendor/Reown/Tests', 'Packages/OathDiagnostics',
          'Tools/WalletConnectSDKValidation', 'Tools/CheckWalletConnectSDK.py']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    sha = require_source_state(source, json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    fixture = (source/TEST).read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    command = ['python3','Tools/CheckWalletConnectSDK.py','--build-system','native','--filter','URIBoundaryTests']
    results = []
    for stage, revision, expected, expected_code in [
        ('before',BASELINE,dict(passed=3,skipped=0,failed=5),1),
        ('after',sha,dict(passed=8,skipped=0,failed=0),0),
    ]:
        with tempfile.TemporaryDirectory(prefix='oath-uri-repro-') as temporary:
            work = Path(temporary)
            archive = subprocess.check_output(['git','-C',str(source),'archive',revision,*INPUTS])
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(work, filter='data')
            (work/TEST).write_bytes(fixture)
            start = time.monotonic()
            log = output/(stage+'.log')
            with log.open('w') as stream:
                run = subprocess.run(command,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=360)
            text = log.read_text(errors='replace').replace(str(work),'<SOURCE-COPY>').replace(str(source),'<SOURCE>').replace(os.path.expanduser('~'),'<HOME>')
            text = re.sub(r'/(?:private/)?var/folders/[^\s:]+/oath-sdk-validation-[^/\s]+','<SDK-HARNESS>',text)
            log.write_text(text)
            cases = sdk_case_counts(text)
            results.append(dict(stage=stage,source_commit=revision,final_commit=sha,
                added_fixture=TEST,fixture_sha256=hashlib.sha256(fixture).hexdigest(),
                source_archive_sha256=hashlib.sha256(archive).hexdigest(),
                command=command,exit_code=run.returncode,cases=cases,expected_cases=expected,
                duration_seconds=round(time.monotonic()-start,3),
                log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                runtime_scope='host; synthetic URI strings through the production WalletConnectURI implementation; no relay or wallet',
                reproduced=cases==expected and run.returncode==expected_code))
            (output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
            print(stage,cases,'exit',run.returncode,flush=True)
            if not results[-1]['reproduced']:
                print('\n'.join(text.splitlines()[-45:]),flush=True)
                raise SystemExit('Unexpected regression outcome; evidence retained')
    require_source_state(source,sha)

if __name__ == '__main__':
    main()
