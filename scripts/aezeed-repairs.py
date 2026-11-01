#!/usr/bin/env python3
"""Identical regression corpus against original and prepared bridge dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from aezeed_source import prepared_bridge
from bounded_process import logged_command
from source_state import require_source_state

TESTS = {'TestCBCRejectsPartialBlocksWithoutMutation', 'TestCBCRejectsShortOutputWithoutMutation',
         'TestBlakeRejectsInvalidStateWithoutMutation', 'TestBlakeValidStateRoundTrips', 'TestGCMLargeLengthEncoding'}
BASELINE_FAILURES = TESTS - {'TestBlakeValidStateRoundTrips'}


def outcomes(path):
    events = [json.loads(line) for line in path.read_text().splitlines()]
    states = {action: [e['Test'] for e in events if e.get('Action') == action and e.get('Test')]
              for action in ['pass', 'fail', 'skip']}
    states['top_level'] = {action: sorted(name for name in names if '/' not in name)
                           for action, names in list(states.items())}
    return states


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('--expected-commit', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); source = args.source.resolve(); out = args.output.resolve()
    require_source_state(source, args.expected_commit); out.mkdir(parents=True, exist_ok=True)
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR']}
    env.update(GOTOOLCHAIN='go1.26.5', GOWORK='off', GOFLAGS='')
    rows = []; started = time.monotonic()
    with prepared_bridge(source, out) as (after, manifest), tempfile.TemporaryDirectory(prefix='oath-aezeed-repairs-') as temp:
        if manifest is None: raise ValueError('Application has no dependency repair preparation')
        before = Path(temp)/'before'
        shutil.copytree(source/'Tools/AezeedBridge', before, ignore=shutil.ignore_patterns('._*', '__pycache__'))
        fixture_hash = hashlib.sha256((before/'dependency_repairs_test.go').read_bytes()).hexdigest()
        if hashlib.sha256((after/'dependency_repairs_test.go').read_bytes()).hexdigest() != fixture_hash:
            raise ValueError('Before and after fixtures differ')
        for stage, bridge, mod in [('before',before,'readonly'), ('after',after,'vendor')]:
            log = out/(stage+'.jsonl')
            command = ['go','test','-mod='+mod,'-race','-count=1','-json','-run','^('+ '|'.join(sorted(TESTS)) +')$','.']
            begin = time.monotonic()
            with log.open('w') as stream:
                code, expired = logged_command(command, stream=stream, timeout=900, cwd=bridge, env=env)
            states = outcomes(log)
            valid = (not expired and not states['skip'] and
                     (code == 1 and set(states['top_level']['fail']) == BASELINE_FAILURES and set(states['top_level']['pass']) == {'TestBlakeValidStateRoundTrips'} if stage == 'before' else
                      code == 0 and set(states['top_level']['pass']) == TESTS and not states['fail'] and len(states['pass']) == 30))
            rows.append(dict(stage=stage, exit_code=code, timed_out=expired, expected_outcome_observed=valid,
                             duration_seconds=round(time.monotonic()-begin,3), outcomes=states,
                             fixture_sha256=fixture_hash, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
            (out/'stages.json').write_text(json.dumps(rows,indent=2)+'\n')
            if not valid: raise RuntimeError(stage+' did not produce the expected result; evidence retained')
        for name in ['go.mod','go.sum','dependency_repairs_test.go']:
            if (before/name).read_bytes() != (source/'Tools/AezeedBridge'/name).read_bytes():
                raise ValueError('Baseline input changed during execution')
    require_source_state(source,args.expected_commit)
    result = dict(check='aezeed-repairs',source_commit=args.expected_commit,status='passed',stages=rows,
                  duration_seconds=round(time.monotonic()-started,3),
                  patch_sha256=manifest['patch_sha256'],
                  prepared_manifest_sha256=hashlib.sha256((out/'prepared-source.json').read_bytes()).hexdigest(),
                  log_sha256=hashlib.sha256((out/'after.jsonl').read_bytes()).hexdigest(),
                  runtime_scope='Go host race detector; real dependencies, public synthetic inputs; no App Store equivalence claim')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
