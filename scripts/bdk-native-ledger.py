#!/usr/bin/env python3
"""Build the crate-source ledger for native inputs without duplicating previously attributed Rust sources."""
import argparse
from collections import Counter
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='secp256k1-sys-0.10.1/depend/secp256k1/'
MANUAL={BASE+'contrib/lax_der_parsing.c':'reviewed',BASE+'src/secp256k1.c':'partially-reviewed',
        BASE+'src/scalar_impl.h':'partially-reviewed',BASE+'src/eckey_impl.h':'partially-reviewed'}

def ledger(traced, rust):
    if traced['lock_sha256']!=rust['lock_sha256']:
        raise ValueError('The Rust and native inventory locks differ')
    prior={x['path']:x['sha256'] for x in rust['files']}
    paths={x['path'] for x in traced['files']}
    if len(paths)!=len(traced['files']):
        raise ValueError('Duplicate compiler input')
    for row in traced['objects']:
        if row['source'] not in row['inputs'] or not set(row['inputs'])<=paths:
            raise ValueError('Compiler object references missing inputs')
    registry={f['path']:f for f in traced['files'] if f['role']=='registry'}
    translations=Counter(r['source'] for r in traced['objects'])
    inputs=Counter(path for r in traced['objects'] for path in r['inputs'])
    if not MANUAL.keys()<=registry.keys():raise ValueError('Expected reviewed native inputs absent')
    rows=[]
    for key,file in sorted(registry.items()):
        if key in prior:
            if prior[key]!=file['sha256']:raise ValueError('Prior input hash differs')
            continue
        if not inputs[key]:raise ValueError('File has no traced compiler action')
        row=dict(path=key,sha256=file['sha256'],bytes=file['bytes'],translation_units=translations[key],included_by_objects=inputs[key],status=MANUAL.get(key,'outstanding'))
        if key in MANUAL:row['evidence']=['review/BDK-NATIVE-INPUTS.md']
        rows.append(row)
    return dict(lock_sha256=traced['lock_sha256'],registry_archives=traced['registry_archives'],files=rows,
                scope='Registry-owned native compiler inputs in the independent SDK 27 build, indexed by package version. The compiler and SDK header inventories are recorded separately in the evidence. Compiler provenance and explicit manual dispositions are distinct.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    d=ledger(json.loads(a.trace.read_bytes()),json.loads((ROOT/'scope/upstream-bdk-rust-selected.json').read_bytes()))
    a.output.write_text(json.dumps(d,indent=2)+'\n');print(len(d['files']),'native registry inputs')
