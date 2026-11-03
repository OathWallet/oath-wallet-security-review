#!/usr/bin/env python3
"""Verify the pinned NEAR artifact and source copies; never infer a reproducible build."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib
from source_state import require_source_state

APP_COMMIT = '5d91d1e4dfd36c56031c7a8fb1ee305446dc54de'
UPSTREAM_COMMIT = '1b0436c96379c63aee7d2429c6d5d24019031ab8'
WASM_SHA256 = 'f3f9ee3e5e29d020dc73f581ff1490c03dff875ed01327dfebbe666724930a76'
COPIES = {
    'multisig2/res/multisig2.wasm': 'Packages/OathAnkr/Sources/OathAnkr/Resources/NearMultisig2.wasm',
    'multisig2/src/lib.rs': 'Packages/OathAnkr/ThirdParty/NearMultisig2/lib.rs',
    'LICENSE-MIT': 'Packages/OathAnkr/ThirdParty/NearMultisig2/LICENSE-MIT',
    'LICENSE-APACHE': 'Packages/OathAnkr/ThirdParty/NearMultisig2/LICENSE-APACHE',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def matching_copy(original, bundled, expected=None):
    if original != bundled or (expected is not None and digest(original) != expected):
        raise ValueError('Pinned upstream copy mismatch')
    return digest(original)


def inspect(app, upstream):
    require_source_state(app, APP_COMMIT)
    require_source_state(upstream, UPSTREAM_COMMIT)
    copies = []
    for source, target in COPIES.items():
        copies.append({'upstream_path': source, 'application_path': target,
                       'sha256': matching_copy((upstream/source).read_bytes(), (app/target).read_bytes(),
                           WASM_SHA256 if source.endswith('.wasm') else None)})
    paths = subprocess.check_output(['git', '-C', str(upstream), 'ls-files', '-z', 'multisig2', 'LICENSE-MIT', 'LICENSE-APACHE']).decode().split('\0')
    files = [{'path': p, 'sha256': digest((upstream/p).read_bytes()), 'bytes': (upstream/p).stat().st_size,
              'status': 'outstanding'} for p in sorted(filter(None, paths))]
    packages = tomllib.loads((upstream/'multisig2/Cargo.lock').read_text())['package']
    return {'repository': 'https://github.com/near/core-contracts.git', 'upstream_commit': UPSTREAM_COMMIT,
            'application_commit': APP_COMMIT, 'copies': copies, 'files': files,
            'lock_packages': [{'name': p['name'], 'version': p['version'], 'source': p.get('source'),
                               'checksum': p.get('checksum'), 'dependencies': p.get('dependencies', []),
                               'implementation_review': 'outstanding'} for p in packages],
            'source_to_binary_rebuild_verified': False,
            'scope': 'Byte identity with the pinned upstream artifact, source and license copies. Lock entries include test dependencies; they are not a proven production reachability inventory.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('application', type=Path); p.add_argument('upstream', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args()
    result = inspect(a.application.resolve(), a.upstream.resolve())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(f"Verified {len(result['copies'])} exact upstream copies; rebuild remains unverified")
