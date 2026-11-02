#!/usr/bin/env python3
"""Check whether Rust toolchain source path spelling explains the published C string differences."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('archive','comparison','differences','output'):
        parser.add_argument(key,type=Path)
    a=parser.parse_args()
    trace=json.loads(a.comparison.read_bytes());delta=json.loads(a.differences.read_bytes())
    data=a.archive.read_bytes();sha=lambda d:hashlib.sha256(d).hexdigest()
    if sha(data)!=trace['published']['sha256'] or sha(data)!='b5106bc00a27ee1b4fc828c8be21c56224557ab4f163d6c11fb0d71f3a6bf8ec':
        raise ValueError('Unexpected publisher archive')
    if delta['archives']!={k:trace[k]['sha256'] for k in ('published','rebuilt')}:
        raise ValueError('Compared archive identities differ')
    old=b'/Users/runner/.rustup/toolchains/1.90.0-aarch64-apple-darwin/lib/rustlib/src/rust/'
    new=b'/rustc/1159e78c4747b02ef996e55082b704c09b970588/'
    objects=dict(runpy.run_path(str(Path(__file__).with_name('compare-bdk-archives.py')))['payloads'](data))
    rows=[]
    for d in delta['members']:
        obj=objects[d['member']];at=32;sections=[]
        for _ in range(struct.unpack_from('<I',obj,16)[0]):
            cmd,length=struct.unpack_from('<2I',obj,at)
            if cmd==25:
                n=struct.unpack_from('<I',obj,at+64)[0]
                if length!=72+80*n:raise ValueError('Invalid Mach-O section list')
                for j in range(n):
                    sec,seg,_,size,offset=struct.unpack_from('<16s16sQQI',obj,at+72+j*80)
                    if (seg.rstrip(b'\0'),sec.rstrip(b'\0'))==(b'__TEXT',b'__cstring'):
                        sections.append(obj[offset:offset+size])
            at+=length
        payload,=sections;rewritten=payload.replace(old,new)
        if [sha(payload),sha(rewritten)]!=d['differences']['__TEXT,__cstring/data'] or [len(payload),len(rewritten)]!=d['differences']['__TEXT,__cstring/size']:
            raise ValueError('Predicted C string section differs: '+d['member'])
        rows.append(dict(member=d['member'],source_path_count=payload.count(old),predicted_digest=sha(rewritten)))
    if len(rows)!=67 or any(not row['source_path_count'] for row in rows):
        raise ValueError('Expected all 67 different members in the pinned publisher-layout experiment')
    result=dict(published_archive=sha(data),rebuilt_archive=trace['rebuilt']['sha256'],members=rows,
                rustc_source_revision='1159e78c4747b02ef996e55082b704c09b970588',
                scope='Replacing only the Rust standard-library source path prefix in each original C string section reproduces the corresponding hosted digest. Constant data, bitcode, symbols and the whole library are separate.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(len(rows),'complete C string sections reproduced')
if __name__=='__main__':main()
