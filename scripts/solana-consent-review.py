#!/usr/bin/env python3
"""Replay one identical Solana consent regression on two immutable source commits."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import tarfile
import time
from pathlib import Path

from isolated_tests import classify
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '7ffd0f449c3312d9fafd01eda59c6b9eb813f9ca'
AFTER = '247ac898168cc8f97be28398c69337f569fb5f96'
FIX = '7c79fe5bf89de44168fc9bc25e7e781d9051fdfe'
FIXTURE = 'fixtures/solana-consent/WalletConnectSolanaConsentRegressionTests.swift'
TARGET = 'Packages/OathAnkr/Tests/OathAnkrTests/WalletConnectSolanaConsentRegressionTests.swift'
CASE = 'OathAnkrTests.WalletConnectSolanaConsentRegressionTests/testPermissionChangeWithIdenticalBalancesMustChangeReview'
ASSERTION = 'A different token delegate must not be represented by an identical review'
NETWORK_DENIAL = '(version 1) (allow default) (deny network*)'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'scratch', 'output']:
        p.add_argument(name, type=Path)
    a = p.parse_args()
    source, scratch, out = [getattr(a, name).resolve() for name in ['source', 'scratch', 'output']]
    require_source_state(source, AFTER)
    if scratch.exists() or out.exists():
        raise ValueError('Fresh scratch and output directories required')
    scratch.mkdir(parents=True)
    out.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if k in {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL'}}
    started = time.monotonic()
    fixture = ROOT / FIXTURE
    if fixture.read_bytes() != (source / TARGET).read_bytes():
        raise ValueError('Fixture differs from the pinned repaired source')
    subprocess.run(['git', '-C', str(source), 'merge-base', '--is-ancestor', FIX, AFTER], check=True, env=env)

    def sanitize(text):
        for path, replacement in [(str(scratch), '<SCRATCH>'), (str(source), '<SOURCE>'),
                                  (str(out), '<OUTPUT>'), (str(Path.home()), '<HOME>')]:
            text = text.replace(path, replacement)
        return text

    def command(cmd, log, timeout=120):
        start = time.monotonic()
        try:
            r = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=timeout)
            text, code = r.stdout.decode(errors='replace'), r.returncode
        except subprocess.TimeoutExpired as e:
            text = (e.stdout or b'').decode(errors='replace') + '\nAUDIT COMMAND TIMEOUT\n'
            code = -1
        log.write_text(sanitize(text))
        return code, round(time.monotonic() - start, 3)

    for cmd, name in [(['xcodebuild', '-version'], 'xcode.log'), (['swift', '--version'], 'swift.log'),
                      (['python3', '--version'], 'python.log')]:
        if command(cmd, out / name)[0]:
            raise ValueError('Toolchain discovery failed; retained logs')
    stages = []
    for stage, commit in [('before', BEFORE), ('after', AFTER)]:
        work, dest = scratch / stage, out / stage
        work.mkdir(); dest.mkdir()
        archive = work / 'packages.tar'
        with archive.open('wb') as f:
            subprocess.run(['git', '-C', str(source), 'archive', commit, 'Packages'], env=env, stdout=f, check=True)
        tree = work / 'source'
        tree.mkdir()
        with tarfile.open(archive) as tar:
            tar.extractall(tree, filter='data')
        archive_hash = sha(archive)
        archive.unlink()
        injected = tree / TARGET
        if injected.exists() and injected.read_bytes() != fixture.read_bytes():
            raise ValueError('Existing regression does not match the paired fixture')
        injected.write_bytes(fixture.read_bytes())
        lock = tree / 'Packages/OathAnkr/Package.resolved'
        lock_hash = sha(lock)
        (dest / 'Package.resolved').write_bytes(lock.read_bytes())
        manifest = [{'path': str(f.relative_to(tree)), 'sha256': sha(f)}
                    for f in sorted((tree / 'Packages').rglob('*')) if f.is_file()]
        (dest / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        prefix = ['--package-path', str(tree / 'Packages/OathAnkr'), '--build-system', 'native',
                  '--scratch-path', str(work / 'build'), '--force-resolved-versions']
        print(stage, 'building pinned production package and host tests', flush=True)
        build_code, build_duration = command(['swift', 'build', *prefix, '--build-tests', '--jobs', '4'],
                                             dest / 'build.log', timeout=1800)
        if build_code:
            raise ValueError(stage + ' failed to compile; not a reproduced vulnerability; retained build.log')
        if sha(lock) != lock_hash:
            raise ValueError('Build changed dependency lock')
        # Keep stderr separate: a compiler deprecation warning can otherwise
        # interleave into a selector midway through SwiftPM's stdout write.
        discovery = subprocess.run(['swift', 'test', *prefix, 'list', '--skip-build', '--disable-swift-testing'],
                                   env=env, capture_output=True, timeout=120)
        (dest / 'discovery.log').write_text(sanitize(discovery.stdout.decode(errors='replace')))
        (dest / 'discovery-stderr.log').write_text(sanitize(discovery.stderr.decode(errors='replace')))
        if discovery.returncode:
            raise ValueError('Test discovery failed')
        selectors = (dest / 'discovery.log').read_text().splitlines()
        if any(not re.fullmatch(r'[\w.]+/\w+', s) for s in selectors):
            raise ValueError('Unexpected discovery output')
        selected = [s for s in selectors if s == CASE] if stage == 'before' else [s for s in selectors if s.startswith('OathAnkrTests.WalletConnectSolana')]
        if CASE not in selected or not selected:
            raise ValueError('Missing paired regression')
        if command(['swift', 'build', *prefix, '--show-bin-path'], dest / 'bin-path.log')[0]:
            raise ValueError('Missing build path')
        # The native SwiftPM product directory is discovered from the fresh build,
        # never reused from a previous source revision.
        bundles = list((work / 'build').glob('*/debug/*.xctest'))
        if len(bundles) != 1:
            raise ValueError('Expected exactly one test bundle')
        binary = bundles[0] / 'Contents/MacOS/OathAnkrPackageTests'
        executable_hash = sha(binary)
        logs = dest / 'cases'; logs.mkdir()

        def run(selector):
            log = logs / (hashlib.sha256(selector.encode()).hexdigest()[:16] + '.log')
            code, duration = command(['/usr/bin/sandbox-exec', '-p', NETWORK_DENIAL,
                                      'xcrun', 'xctest', '-XCTest', selector, str(bundles[0])], log)
            body = log.read_text()
            return {'selector': selector, 'status': classify(body, code), 'exit_code': code,
                    'duration_seconds': duration, 'log': str(log.relative_to(out)), 'log_sha256': sha(log)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            cases = list(pool.map(run, selected))
        totals = {status: sum(c['status'] == status for c in cases) for status in ['passed', 'skipped', 'failed']}
        paired = next(c for c in cases if c['selector'] == CASE)
        body = (out / paired['log']).read_text()
        if stage == 'before':
            failures = re.findall(r'^.* error: .* : (.*)$', body, re.M)
            if totals != {'passed': 0, 'skipped': 0, 'failed': 1} or paired['exit_code'] != 1 or len(failures) != 1 or ASSERTION not in failures[0]:
                raise ValueError('Baseline did not fail exactly the expected consent assertion; retained logs')
        elif totals['failed'] or paired['status'] != 'passed':
            raise ValueError('Repaired regression or adjacent test failed; retained logs')
        stages.append({'stage': stage, 'source_commit': commit, 'source_archive_sha256': archive_hash,
                       'fixture_sha256': sha(fixture), 'dependency_lock_sha256': lock_hash,
                       'build_exit_code': build_code, 'build_duration_seconds': build_duration,
                       'executable_sha256': executable_hash, 'runtime_network': 'denied',
                       'totals': totals, 'cases': cases})
        (dest / 'cases.json').write_text(json.dumps(cases, indent=2) + '\n')
        print(stage, totals, flush=True)
    require_source_state(source, AFTER)
    result = {'schema_version': 1, 'finding': 'OW-2026-073', 'baseline_commit': BEFORE,
              'fix_commit': FIX, 'retest_commit': AFTER, 'fixture': FIXTURE, 'fixture_sha256': sha(fixture),
              'driver_sha256': sha(Path(__file__)),
              'helper_sha256': {name: sha(ROOT / 'scripts' / name) for name in ['isolated_tests.py', 'source_state.py']},
              'duration_seconds': round(time.monotonic() - started, 3), 'stages': stages,
              'limitations': ['Injected RPC account states; no validator execution or production transaction.',
                              'Targeted XCTest host cases, not full app runtime or an independent audit.',
                              'Skipped live cases are not passing evidence.'],
              'files': [{'path': str(f.relative_to(out)), 'sha256': sha(f)} for f in sorted(out.rglob('*')) if f.is_file()]}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
