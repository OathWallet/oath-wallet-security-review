#!/usr/bin/env python3
"""Inventory the recorded Rust input to the BDK publisher and its Cargo lock."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

REVISION = '1c5f4863c6a53cc9d063d34c4e13c91fea5c58de'
REVIEWED = {
    'bdk-swift/build-xcframework.sh', 'bdk-ffi/Cargo.toml',
    'bdk-ffi/rust-toolchain.toml', 'bdk-ffi/src/lib.rs', 'bdk-ffi/src/signer.rs',
    'bdk-ffi/src/macros.rs', 'bdk-ffi/uniffi.toml', 'bdk-ffi/uniffi-bindgen.rs',
}

def build(checkout):
    def git(*args):
        return subprocess.check_output(['git', '-C', checkout, *args])
    if git('rev-parse','HEAD').decode().strip() != REVISION:
        raise ValueError('Unexpected bdk-ffi checkout')
    files = []
    for entry in git('ls-tree','-rz',REVISION).split(b'\0'):
        if not entry:
            continue
        header, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = header.decode().split()
        name = raw_path.decode()
        if kind != 'blob':
            raise ValueError('Unaccounted source type ' + name)
        blob=git('cat-file','blob',oid)
        row=dict(path=name, bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest(), mode=mode, status='outstanding')
        if name in REVIEWED:
            row.update(status='reviewed', evidence=['review/RESOLVED-PACKAGES.md'])
        if name in {'bdk-ffi/src/wallet.rs','bdk-ffi/src/bitcoin.rs'}:
            row.update(status='partially-reviewed', evidence=['review/BITCOIN-SIGNER-AND-CORE.md'])
        if name=='bdk-ffi/src/keys.rs':
            row.update(status='partially-reviewed',evidence=['review/EXTENDED-KEY-IMPORT.md'])
        files.append(row)
    if {r['path'] for r in files if r['status']=='reviewed'} != REVIEWED:
        raise ValueError('Reviewed file missing')
    lock=tomllib.loads(git('show',REVISION+':bdk-ffi/Cargo.lock').decode())
    crates=[{key:item[key] for key in ('name','version','source','checksum') if key in item} for item in lock['package']]
    return dict(repository='https://github.com/bitcoindevkit/bdk-ffi',commit=REVISION,files=files,
                locked_packages=crates,scope='Source selected in publisher build log. Locked packages include tools and test inputs. Rust dependency implementation coverage and independent build equivalence remain outstanding.')

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('checkout',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(build(a.checkout),indent=2)+'\n')
