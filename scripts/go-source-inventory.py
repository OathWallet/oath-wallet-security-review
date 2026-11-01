#!/usr/bin/env python3
"""Inventory selected aezeed source inputs; does not establish archive identity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from source_state import require_source_state
from aezeed_source import prepared_bridge


def objects(text):
    decoder = json.JSONDecoder()
    while text.strip():
        text = text.lstrip()
        value, length = decoder.raw_decode(text)
        yield value
        text = text[length:]


def collect_graph(source, commit, bridge, preparation):
    require_source_state(source, commit)
    original_bridge = source / 'Tools/AezeedBridge'
    version = subprocess.check_output(['go', 'version'], text=True).strip()
    if not version.startswith('go version go1.26.5 '):
        raise ValueError('Expected Go 1.26.5')
    subprocess.run(['go', 'mod', 'verify'], cwd=original_bridge, check=True)
    modules = list(objects(subprocess.check_output(['go', 'list', '-mod=readonly', '-m', '-json', 'all'], cwd=original_bridge, text=True)))
    module_graph = {m['Path']: m.get('Version', 'main') for m in modules}
    if any(m.get('Replace') for m in modules):
        raise ValueError('Unexpected replaced Go dependency')
    targets = []
    for name, goos, sdk, triple in [
        ('mac', 'darwin', 'macosx', 'arm64-apple-macos15.5'),
        ('ios', 'ios', 'iphoneos', 'arm64-apple-ios17.0'),
        ('sim', 'ios', 'iphonesimulator', 'arm64-apple-ios17.0-simulator'),
    ]:
        clang = subprocess.check_output(['xcrun', '--find', 'clang'], text=True).strip()
        sdk_path = subprocess.check_output(['xcrun', '--sdk', sdk, '--show-sdk-path'], text=True).strip()
        env = {k: v for k, v in os.environ.items() if not k.startswith('OATH_')}
        env.update(GOOS=goos, GOARCH='arm64', CGO_ENABLED='1',
                   CC=f'{clang} -target {triple} -isysroot {sdk_path}',
                   GOFLAGS='-mod=vendor' if preparation else '-mod=readonly', GOWORK='off')
        rows = list(objects(subprocess.check_output(['go', 'list', '-deps', '-json', '.'], cwd=bridge, env=env, text=True)))
        packages = []
        for row in rows:
            if row.get('Error') or row.get('Incomplete'):
                raise ValueError('Incomplete Go dependency graph')
            module = row.get('Module', {})
            if module.get('Replace'):
                raise ValueError('Unexpected replaced Go dependency')
            files = []
            if not row.get('Standard'):
                for field in ['GoFiles', 'CgoFiles', 'CFiles', 'CXXFiles', 'MFiles', 'HFiles', 'SFiles', 'SysoFiles', 'EmbedFiles']:
                    for name_in_package in row.get(field, []):
                        path = Path(row['Dir']) / name_in_package
                        files.append({'path': name_in_package, 'kind': field,
                                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            packages.append({'import_path': row['ImportPath'], 'standard': bool(row.get('Standard')),
                             'module': module.get('Path'), 'version': module.get('Version'),
                             'module_sum': module.get('Sum'), 'files': files})
        targets.append({'target': name, 'goos': goos, 'goarch': 'arm64', 'cgo': True,
                        'clang_triple': triple, 'sdk': sdk, 'packages': packages})
    require_source_state(source, commit)
    return {'source_commit': commit, 'go_version': version, 'targets': targets,
            'source_preparation': preparation,
            'module_graph': module_graph,
            'go_mod_sha256': hashlib.sha256((bridge/'go.mod').read_bytes()).hexdigest(),
            'go_sum_sha256': hashlib.sha256((bridge/'go.sum').read_bytes()).hexdigest(),
            'binary_identity_established': False,
            'limitations': ['Go source selection only, not a linked-binary measurement.',
                            'Standard library sources remain a separate toolchain review boundary.',
                            'No source file is marked reviewed by this inventory.']}


def collect(source, commit):
    require_source_state(source, commit)
    with prepared_bridge(source) as (bridge, preparation):
        return collect_graph(source, commit, bridge, preparation)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('commit')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = collect(args.source.resolve(), args.commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
