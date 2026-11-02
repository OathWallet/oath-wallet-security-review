#!/usr/bin/env python3
"""Hash tracked inputs in the package checkouts selected by the iOS Release build."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

LOCK = 'OathAtmosphere.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved'
REVIEWED = {
    'bdk-swift/.github/workflows/publish-spm.yaml': 'ab4b0c02e522b4016ab527dfd8cda246c40f55c5f1d7cf51478b7774a551a50b',
    'bdk-swift/.gitignore': 'c0a2aa0dd04e05ef59c1ad99d4dd89d8532ee733b5f32548ad15fb20058b6b4a',
    'bdk-swift/LICENSE': '031dbd187e6e01b8b0ab57250038c3810633323e61a0a4d1d0c171760dba38c7',
    'bdk-swift/Package.swift': '6ce1b7cbc43010bc375834de3fe30826ef68c87fd5400788607bf9b8bc587473',
    'bdk-swift/README.md': '862856098e9ef79dce64288c5c0c0b859de4d1935a593ee12bac4479fc8451e9',
    'SwiftImageReadWrite/Package.swift': '7a027a5c133c689324b3ccfad1933fc40d687b27718da55a75cefac8a42c5ffd',
    'swift-qrcode-generator/Package.swift': 'cb912dfe68ad850395e65763848b5069b70730bac79408afd397a94870970d42',
}

PARTIAL_XDR = {
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/responses/xdr/InvokeContractArgsXDR.swift": "11c0db49bc6d0f9d6c967a740369a2e37c43bfb07c9756d881eee4534765fb9d",
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/responses/xdr/InvokeHostFunctionOpXDR.swift": "aad2a95792e8c9e9f781def4296926dc193fa926805d629c7c610feca876cde6",
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/responses/xdr/SCValXDR.swift": "2fa265a6d2d4c2003ce99eab37abd14a6c5128d0fc781f900207c1a1dea1aab2",
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/responses/xdr/TransactionEnvelopeXDR.swift": "77387a2fc6e50ccee9bf61421197e22ea7ecbaa7ead06b7334adff660106af51",
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/responses/xdr/TransactionXDR.swift": "fde8a00c4050eb67551303806bb71efca0cd40fa5a40b28b48f5784c9b51f27c",
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/utils/xdrCodable/XDRCodableExtensions.swift": "778d90a4dba09951ce333eaf6c5a78033675bd60b74a21775e5f16ac3c3012ba",
    "stellar-ios-mac-sdk/stellarsdk/stellarsdk/utils/xdrCodable/XDRDecoder.swift": "6462325ba84f51925c5d7fb084deef748b37b7a6e9d21317b99c035357b3099b"
}


def git(root, *args):
    return subprocess.check_output(['git', '-C', root, *args])


def files(checkout, pin):
    if git(checkout, 'rev-parse', 'HEAD').decode().strip() != pin:
        raise ValueError(f'Revision mismatch in {checkout.name}')
    if git(checkout, 'status', '--porcelain', '--untracked-files=no', '--ignore-submodules=untracked'):
        raise ValueError(f'Modified tracked files in {checkout.name}')
    generated = {}
    if checkout.name == 'stellar-ios-mac-sdk':
        proof_path = Path(__file__).resolve().parents[1]/'evidence/progress55/stellar-generation.json'
        proof = json.loads(proof_path.read_bytes())
        if proof['sdk_commit'] == pin and not proof['mismatches']:
            generated = proof['matching_files']
    rows = []
    with subprocess.Popen(['git', '-C', checkout, 'cat-file', '--batch'],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as reader:
        for entry in git(checkout, 'ls-tree', '-r', '-z', pin).split(b'\0'):
            if not entry:
                continue
            header, path = entry.split(b'\t', 1)
            mode, kind, oid = header.decode().split()
            name = f'{checkout.name}/{path.decode()}'
            row = dict(path=name, mode=mode, kind=kind, git_oid=oid, status='outstanding')
            if kind == 'blob':
                reader.stdin.write(oid.encode() + b'\n')
                reader.stdin.flush()
                obj, objtype, size = reader.stdout.readline().decode().split()
                if obj != oid or objtype != kind:
                    raise ValueError(f'Unexpected Git object at {name}')
                data = reader.stdout.read(int(size))
                if len(data) != int(size) or reader.stdout.read(1) != b'\n':
                    raise ValueError(f'Truncated object at {name}')
                row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            elif kind != 'commit' or mode != '160000':
                raise ValueError(f'Unknown Git entry at {name}')
            if name in REVIEWED and row.get('sha256') == REVIEWED[name]:
                row.update(status='reviewed', evidence=['review/RESOLVED-PACKAGES.md'])
            if name in PARTIAL_XDR and row.get('sha256') == PARTIAL_XDR[name]:
                row.update(status='partially-reviewed', evidence=['review/STELLAR-XDR-BOUNDARIES.md'])
            if path.decode() in generated and generated[path.decode()] == row.get('sha256'):
                row['semantic_review_status'] = row['status']
                row['status'] = 'generated-verified'
                row.setdefault('evidence', []).append('evidence/progress55/stellar-generation.json')
            rows.append(row)
        reader.stdin.close()
        if reader.wait():
            raise ValueError('Git object reader failed')
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('checkouts', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    pins = json.loads((a.source / LOCK).read_bytes())['object']['pins']
    packages, entries = [], []
    for pin in sorted(pins, key=lambda item: item['repositoryURL']):
        url = pin['repositoryURL']
        name = url.rsplit('/', 1)[1].removesuffix('.git')
        checkout = a.checkouts / name
        revision = pin['state']['revision']
        if name == 'SwiftDraw':
            separate = Path(__file__).resolve().parents[1] / 'scope/upstream-swiftdraw.json'
            if json.loads(separate.read_bytes())['commit'] != revision or git(checkout, 'rev-parse', 'HEAD').decode().strip() != revision:
                raise ValueError('SwiftDraw ledger revision mismatch')
            continue
        rows = files(checkout, revision)
        packages.append(dict(checkout=name, repository=url, commit=revision, entries=len(rows)))
        entries.extend(rows)
    if {r['path'] for r in entries if r['status'] == 'reviewed'} != set(REVIEWED):
        raise ValueError('Reviewed source missing')
    if {r['path'] for r in entries if r.get('semantic_review_status',r['status']) == 'partially-reviewed'} != set(PARTIAL_XDR):
        raise ValueError('Partially reviewed XDR source missing or changed')
    output = dict(lockfile=LOCK, lock_sha256=hashlib.sha256((a.source/LOCK).read_bytes()).hexdigest(),
                  scope='All tracked entries at the other Xcode package pins. Gitlinks are unresolved subtrees. Development files are included. No automatic reachability or review disposition.', packages=packages, files=entries)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2) + '\n')


if __name__ == '__main__':
    main()
