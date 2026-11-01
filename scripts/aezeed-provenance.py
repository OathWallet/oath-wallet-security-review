#!/usr/bin/env python3
"""Verify recorded aezeed inputs; optionally reproduce all slices twice on macOS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from source_state import require_source_state

BRIDGE = Path('Tools/AezeedBridge')
FRAMEWORK = Path('Packages/OathAezeed/OathAezeedCore.xcframework')


def hashes(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink is not a reproducible input: ' + str(path))
        if path.is_file() and not path.name.startswith('._'):
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify_manifest(source):
    manifest = json.loads((source/'Packages/OathAezeed/BuildProvenance.json').read_text())
    inputs = {str(BRIDGE/path): digest for path, digest in hashes(source/BRIDGE).items()}
    outputs = hashes(source/FRAMEWORK)
    if not inputs or inputs != manifest['input_hashes']:
        raise ValueError('Source inputs differ from the provenance manifest')
    if not outputs or outputs != manifest['framework_files']:
        raise ValueError('Bundled framework differs from the provenance manifest')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--expected-commit', required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    result = {'check': 'aezeed-provenance', 'status': 'failed',
              'runtime_scope': 'file verification; optional cross-compilation only',
              'historical_binary_equivalence': False}
    try:
        result['source_commit'] = require_source_state(source, args.expected_commit)
        manifest = verify_manifest(source)
        result.update(input_files=len(manifest['input_hashes']), framework_files=len(manifest['framework_files']),
                      manifest_sha256=hashlib.sha256((source/'Packages/OathAezeed/BuildProvenance.json').read_bytes()).hexdigest())
        if args.rebuild:
            env = {k: v for k, v in os.environ.items() if k in ['HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'LANG', 'LC_ALL']}
            xcode = subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip()
            result['xcode'] = xcode
            expected_xcode = manifest['xcode_version'].replace(' (', '\nBuild version ').removesuffix(')')
            if xcode != 'Xcode ' + expected_xcode:
                raise ValueError('Reference archive comparison requires the recorded Xcode toolchain')
            builds = []
            for index in range(2):
                with tempfile.TemporaryDirectory(prefix='oath-aezeed-reproduce-') as temp:
                    root = Path(temp)
                    shutil.copytree(source/BRIDGE, root/BRIDGE, ignore=shutil.ignore_patterns('._*'))
                    env['GOCACHE'] = str(root/'go-cache')
                    target = root/'OathAezeedCore.xcframework'
                    log = output/f'build-{index + 1}.log'
                    with log.open('w') as stream:
                        completed = subprocess.run(['bash', str(root/BRIDGE/'build.sh'), str(target)],
                                                   env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
                    log.write_text(log.read_text().replace(str(root), '<ISOLATED_BUILD>'))
                    if completed.returncode:
                        raise ValueError('Build failed; see ' + log.name)
                    builds.append(hashes(target))
            result['builds'] = builds
            if builds[0] != builds[1] or builds[0] != manifest['framework_files']:
                raise ValueError('Rebuilt framework files do not match each other and the checked-in framework')
            result['two_builds_match_reference'] = True
        else:
            result['two_builds_match_reference'] = None
        verify_manifest(source)
        require_source_state(source, args.expected_commit)
        result['status'] = 'passed'
    except (ValueError, OSError, subprocess.SubprocessError, KeyError) as error:
        result['error'] = str(error)
    result['duration_seconds'] = round(time.monotonic() - started, 2)
    result['logs'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('build-*.log')}
    if result.get('two_builds_match_reference'):
        result['log'] = 'build-1.log'
        result['log_sha256'] = result['logs']['build-1.log']
    (output/'aezeed-provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
