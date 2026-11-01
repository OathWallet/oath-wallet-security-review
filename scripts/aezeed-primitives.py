#!/usr/bin/env python3
"""Run independent AES checks against the aezeed bridge's pinned Go crypto dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from bounded_process import logged_command
from source_state import require_source_state
from blake_vectors import vectors
from aezeed_source import prepared_bridge

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'TestEverySBoxInputInEveryLane', 'TestKnownAnswerAndDeterministicDifferential', 'TestResetAndShortBuffersReject', 'TestCT32EverySBoxInputInEveryLane', 'TestCT32KnownAnswerAndDeterministicDifferential', 'TestCT32ResetAndShortBuffersReject', 'TestGHASHIndependentPolynomial', 'TestBlakeIndependentVectors', 'TestAEZBoundariesAndTamperRejection', 'TestBlockModesDifferential', 'TestKnownUnusedCBCPartialBlockHazard', 'TestKnownUnusedBlakeStateHazard', 'TestKnownUnusedGCMLengthHazard'}


def successful(text, code, expected=EXPECTED):
    try:
        events = [json.loads(line) for line in text.splitlines()]
    except json.JSONDecodeError:
        return False
    passes = [row['Test'] for row in events if row.get('Action') == 'pass' and row.get('Test')]
    return (code == 0 and len(passes) == len(expected) and set(passes) == expected
            and not any(row.get('Action') in ['fail', 'skip'] for row in events)
            and any(row.get('Action') == 'pass' and not row.get('Test') for row in events))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    sha = require_source_state(source, args.expected_commit)
    output.mkdir(parents=True, exist_ok=True)
    fixture = ROOT/'tests/aezeed_primitives_test.go'
    dependencies = ROOT/'tests/aezeed_dependencies_test.go'
    vector_data = json.dumps(vectors(), sort_keys=True).encode()
    (output/'blake-vectors.json').write_bytes(vector_data)
    log = output/'aezeed-primitives.jsonl'
    env = {k: v for k, v in os.environ.items() if k in ['HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL']}
    env.update(GOTOOLCHAIN='go1.26.5', GOWORK='off', GOFLAGS='')
    started = time.monotonic()
    with prepared_bridge(source, output) as (bridge, preparation), tempfile.TemporaryDirectory(prefix='oath-aes-properties-') as temp:
        work = Path(temp)
        for name in ['go.mod', 'go.sum']:
            shutil.copyfile(source/'Tools/AezeedBridge'/name, work/name)
        shutil.copyfile(fixture, work/'primitives_test.go')
        shutil.copyfile(dependencies, work/'dependencies_test.go')
        (work/'blake-vectors.json').write_bytes(vector_data)
        expected = EXPECTED if preparation is None else {name for name in EXPECTED if not name.startswith('TestKnownUnused')}
        if preparation:
            (work/'vendor').symlink_to(bridge/'vendor', target_is_directory=True)
        command = ['go', '-C', str(work), 'test', '-mod=vendor' if preparation else '-mod=readonly',
                   '-race', '-count=1', '-json', '-run', '^('+ '|'.join(sorted(expected)) +')$', '.']
        with log.open('w') as stream:
            code, timed_out = logged_command(command, env=env, stream=stream, timeout=600)
        for name in ['go.mod', 'go.sum']:
            if (work/name).read_bytes() != (source/'Tools/AezeedBridge'/name).read_bytes():
                raise RuntimeError('Pinned dependency graph changed')
    require_source_state(source, sha)
    passed = successful(log.read_text(), code, expected)
    result = {'check': 'aezeed-primitives', 'source_commit': sha, 'status': 'passed' if passed else 'failed',
              'exit_code': code, 'timed_out': timed_out, 'tests_passed': len(expected) if passed else None,
              'seed': '0x4f41544841455331', 'sbox_lane_comparisons': 24576, 'aes_differential_samples': 1536,
              'ghash_lengths': 514, 'blake_vectors': 220, 'known_unused_hazards_reproduced': 0 if preparation else 3, 'positive_validation_cases': 10,
              'source_preparation_sha256': hashlib.sha256((output/'prepared-source.json').read_bytes()).hexdigest() if preparation else None,
              'duration_seconds': round(time.monotonic()-started, 2),
              'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
              'dependencies_fixture_sha256': hashlib.sha256(dependencies.read_bytes()).hexdigest(),
              'blake_vectors_sha256': hashlib.sha256(vector_data).hexdigest(),
              'go_sum_sha256': hashlib.sha256((source/'Tools/AezeedBridge/go.sum').read_bytes()).hexdigest(),
              'log': log.name, 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
              'runtime_scope': 'macOS host, patched ct32/ct64/GHASH/BLAKE2b/AEZ, positive synthetic checks; repair regressions run separately; not a timing proof' if preparation else 'macOS host, pinned ct32/ct64/GHASH/BLAKE2b/AEZ, synthetic inputs; characterization passes do not repair hazards; not a timing proof'}
    (output/'aezeed-primitives.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
