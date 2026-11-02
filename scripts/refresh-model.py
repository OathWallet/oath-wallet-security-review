#!/usr/bin/env python3
"""Exercise the shipping refresh state machine on macOS with network access disabled."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--expected-commit')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    pin = require_source_state(source, args.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    rules = (
        ('events', ['RefreshPullGesture', 'RefreshPullFeedback', 'RefreshCycle'], ROOT/'fixtures/native-refresh/Events.swift', '100000 seeded events passed; activations=4617, feedback=99'),
        ('settlement', ['RefreshCompletion'], source/'Tools/CheckRefreshCompletion.swift', 'Passed 251 refresh lifecycle checks'),
        ('observation', ['RefreshCycle', 'RefreshIndicatorModel'], source/'Tools/CheckRefreshObservation.swift', 'PASS: idle observation is quiet across 20,000 repeated stops; active and partial refresh cancel once'),
        ('geometry', ['RefreshCycle', 'OathRefreshMark'], source/'Tools/CheckBrandedRefresh.swift', 'Passed 6182 branded refresh lifecycle and SVG geometry checks'),
    )
    base = source/'Packages/OathNativeRefresh/Sources/OathNativeRefresh'
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, inputs, test, expected in rules:
            files = [base/(f+'.swift') for f in inputs] + [test]
            binary = Path(tmp)/name
            subprocess.run(['swiftc', '-parse-as-library', *files, '-o', binary], check=True, timeout=180)
            summary = subprocess.check_output(['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)', binary], text=True, timeout=60).strip()
            if summary != expected:
                raise ValueError('Unexpected assertion result from '+name)
            results[name] = dict(summary=summary, files={f.name:sha(f) for f in files})
    require_source_state(source, pin)
    args.output.mkdir(parents=True, exist_ok=True)
    log = args.output/'refresh-model.log'
    log.write_text(json.dumps(results, indent=2)+'\n')
    result = dict(check='refresh-model', source_commit=pin, status='passed', cases=results, log=log.name, log_sha256=sha(log))
    (args.output/'refresh-model.json').write_text(json.dumps(result, indent=2)+'\n')
    print('All four refresh host probes passed')

if __name__ == '__main__':
    main()
