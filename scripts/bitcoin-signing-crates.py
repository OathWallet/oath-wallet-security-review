#!/usr/bin/env python3
"""Inventory the exact registry sources named by the published BDK Cargo lock."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
CRATES=('bdk_wallet','miniscript')
PARTIAL={
 'bdk_wallet/src/wallet/signer.rs','bdk_wallet/src/wallet/mod.rs',
 'miniscript/src/psbt/finalizer.rs','miniscript/src/psbt/mod.rs','miniscript/src/interpreter/mod.rs',
}

def inventory(cache):
    lock=json.loads((ROOT/'scope/upstream-bdk-ffi.json').read_bytes())['locked_packages']
    rows=[];crates=[]
    for name in CRATES:
        record,=[p for p in lock if p['name']==name]
        version=record['version']; expected=record['checksum']; full=f'{name}-{version}';filename=full+'.crate'
        source=f'https://static.crates.io/crates/{name}/{filename}';path=cache/filename
        if not path.exists():subprocess.run(['curl','--fail','--silent','--show-error','--location','--retry','3',source,'-o',path],check=True,timeout=120)
        with path.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=expected: raise ValueError('Rust archive checksum mismatch')
        names=set()
        with tarfile.open(path,'r:gz') as tar:
            for item in tar:
                if item.isdir():continue
                parts=PurePosixPath(item.name).parts
                if not item.isfile() or len(parts)<2 or parts[0]!=full or '..' in parts:raise ValueError('Unexpected registry entry')
                relative='/'.join([name,*parts[1:]])
                if relative in names:raise ValueError('Duplicate file')
                names.add(relative)
                with tar.extractfile(item) as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
                row=dict(path=relative,sha256=digest,bytes=item.size,status='outstanding')
                if relative in PARTIAL: row.update(status='partially-reviewed',evidence=['review/BITCOIN-SIGNER-AND-CORE.md'])
                rows.append(row)
        crates.append(dict(name=name,version=version,url=source,archive_sha256=expected,entries=len(names)))
    assert {r['path'] for r in rows if r['status']=='partially-reviewed'}==PARTIAL
    return dict(cargo_lock_source='https://github.com/bitcoindevkit/bdk-ffi/blob/1c5f4863c6a53cc9d063d34c4e13c91fea5c58de/bdk-ffi/Cargo.lock',
                crates=crates,files=sorted(rows,key=lambda r:r['path']),scope='All files in these two pinned registry tarballs. Includes non-runtime files. File review applies only to scopes documented in the report. No independent binary-equivalence claim.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();a.cache.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(inventory(a.cache),indent=2)+'\n')
