#!/usr/bin/env python3
"""Trace synthetic pairing inputs through unchanged app scanner/link implementations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    sha = require_source_state(source, json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    fixture = (ROOT/'tests/PairingLinkBoundary.swift').read_bytes()
    out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oath-link-repro-') as temporary:
        work = Path(temporary)
        (work/'Tools').mkdir()
        # The harness copies production sources unchanged. Only its selected
        # test executable is supplied by this audit repository.
        for name in ['OathAtmosphere', 'Packages']:
            (work/name).symlink_to(source/name, target_is_directory=True)
        (work/'Tools/CheckScanner.py').write_bytes((source/'Tools/CheckScanner.py').read_bytes())
        (work/'Tools/CheckWalletLinks.swift').write_bytes(fixture)
        log = out/'app-boundary.log'
        with log.open('w') as stream:
            run = subprocess.run(['python3','Tools/CheckScanner.py','--links'],cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=360)
        text = log.read_text(errors='replace').replace(str(work),'<TEST-HARNESS>').replace(str(source),'<SOURCE>').replace(os.path.expanduser('~'),'<HOME>')
        log.write_text(text)
    require_source_state(source,sha)
    passed = run.returncode == 0 and 'App pairing boundary: 5 assertions passed;' in text
    result = dict(check='pairing-link-boundary',source_commit=sha,status='passed' if passed else 'failed',exit_code=run.returncode,
        duration_seconds=round(time.monotonic()-start,2),fixture_sha256=hashlib.sha256(fixture).hexdigest(),
        log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),runtime_scope='macOS host; unchanged production app parsers, no pairing, network, simulator or wallet')
    (out/'app-boundary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],result['duration_seconds'])
    raise SystemExit(0 if passed else 1)

if __name__ == '__main__': main()
