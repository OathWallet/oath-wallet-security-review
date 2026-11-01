#!/usr/bin/env python3
"""Explain SDK markers and object overlap in two immutable arm64 device archives."""
from collections import Counter,defaultdict
from pathlib import Path
import argparse,hashlib,json,re,struct

def version(v):return '.'.join(map(str,(v>>16,(v>>8)&255,v&255)))
def metadata(blob):
    if len(blob)<32 or blob[:4]!=b'\xcf\xfa\xed\xfe':return ()
    _,cpu,_,kind,count,size,_,_=struct.unpack_from('<IiiIIIII',blob)
    if cpu!=0x0100000c or kind!=1 or size>len(blob)-32:raise ValueError('Invalid arm64 object')
    cursor=32;versions=[]
    for _ in range(count):
        cmd,length=struct.unpack_from('<II',blob,cursor)
        if length<8 or cursor+length>32+size:raise ValueError('Malformed command')
        if cmd==0x32:
            platform,minimum,sdk,tools=struct.unpack_from('<IIII',blob,cursor+8)
            if length!=24+tools*8:raise ValueError('Malformed build version')
            versions.append((platform,version(minimum),version(sdk)))
        cursor+=length
    if cursor!=32+size:raise ValueError('Invalid commands length')
    return tuple(versions)

def rows(path):
    data=path.read_bytes();at=8
    if not data.startswith(b'!<arch>\n'):raise ValueError('Expected archive')
    out={}
    while at<len(data):
        head=data[at:at+60]
        if len(head)!=60 or head[58:]!=b'`\n':raise ValueError('Invalid archive header')
        n=int(head[48:58]);at+=60
        if n<0 or at+n>len(data):raise ValueError('Bad member size')
        name=head[:16].rstrip().decode();blob=data[at:at+n];at+=n+n%2
        if name.startswith('#1/'):
            end=int(name[3:])
            if not 0<end<=len(blob):raise ValueError('Bad member name')
            name=blob[:end].rstrip(b'\0').decode();blob=blob[end:]
        if name.startswith('__.SYMDEF'):continue
        if name in out:raise ValueError('Duplicate member')
        out[name]=dict(sha256=hashlib.sha256(blob).hexdigest(),versions=metadata(blob))
    if at!=len(data) or not out:raise ValueError('Incomplete archive')
    return out

def compare(a,b,exact):
    ref=json.loads(exact.read_bytes());archives=[]
    for path,kind in ((a,'published'),(b,'rebuilt')):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=ref[kind]['sha256']:raise ValueError('Wrong archive')
        obj=rows(path);old={m['name']:m for m in ref[kind]['members']}
        if set(old)!=set(obj) or any(old[n]['sha256']!=r['sha256'] for n,r in obj.items()):raise ValueError('Member mismatch')
        for n,r in obj.items():r['code']=old[n]['instruction_digest']
        archives.append(obj)
    p,r=archives
    common=p.keys()&r.keys()
    def count(rows):return [dict(platform=v[0],minimum=v[1],sdk=v[2],count=n) for v,n in sorted(Counter(v for row in rows.values() for v in row['versions']).items())]
    meta_only=[]
    for n in sorted(common):
        if p[n]['versions']!=r[n]['versions'] and p[n]['code'] and p[n]['code']==r[n]['code']:meta_only.append(n)
    return dict(published_sha256=ref['published']['sha256'],rebuilt_sha256=ref['rebuilt']['sha256'],published_build_versions=count(p),rebuilt_build_versions=count(r),same_named_members=len(common),
        changed_hash_same_name=sum(p[n]['sha256']!=r[n]['sha256'] for n in common),
        different_build_version_same_instruction_digest=meta_only,
        scope='Architecture, SDK and minimum OS are read from each Mach-O LC_BUILD_VERSION. Matching raw instruction bytes omit relocations and data. Different recorded SDKs establish a toolchain difference but do not alone explain changes in machine code.')
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for key in ('published','rebuilt','comparison','output'):ap.add_argument(key,type=Path)
    a=ap.parse_args();a.output.write_text(json.dumps(compare(a.published,a.rebuilt,a.comparison),indent=2)+'\n')
