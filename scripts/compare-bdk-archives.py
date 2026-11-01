#!/usr/bin/env python3
"""Compare exact archive bytes, member content and exported interfaces from two arm64 BDK slices."""
from collections import Counter
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
def sha(data):return hashlib.sha256(data).hexdigest()
def instruction_digest(body):
    # Some Rust archive members consist solely of metadata. Compare instruction-
    # bearing Mach-O sections when present, still retaining every whole object hash.
    if len(body)<32 or struct.unpack_from('<I',body)[0]!=0xfeedfacf:return None
    _,cpu,_,kind,ncmds,size,_,_=struct.unpack_from('<IiiIIIII',body)
    if cpu!=0x0100000c or kind!=1 or 32+size>len(body):raise ValueError('Unexpected object header')
    cursor=32;h=hashlib.sha256();total=0
    for _ in range(ncmds):
        cmd,n=struct.unpack_from('<II',body,cursor)
        if cursor+n>32+size or n<8:raise ValueError('Invalid object command')
        if cmd==0x19:
            count=struct.unpack_from('<I',body,cursor+64)[0]
            if 72+80*count!=n:raise ValueError('Invalid object section list')
            for j in range(count):
                at=cursor+72+80*j
                sect,seg,_,length,off=struct.unpack_from('<16s16sQQI',body,at)
                flags=struct.unpack_from('<I',body,at+64)[0]
                if length and flags&(0x80000000|0x400):
                    if off+length>len(body):raise ValueError('Invalid section size')
                    h.update(seg+sect+struct.pack('<Q',length));h.update(body[off:off+length]);total+=length
        cursor+=n
    if cursor!=32+size:raise ValueError('Incomplete object commands')
    return h.hexdigest() if total else None

def payloads(data):
    if not data.startswith(b'!<arch>\n'):raise ValueError('Not a Unix static archive')
    at=8;count=0
    while at<len(data):
        header=data[at:at+60]
        if len(header)!=60 or header[58:]!=b'`\n':raise ValueError('Invalid member header')
        name=header[:16].rstrip().decode();size=int(header[48:58]);at+=60
        if size<0 or at+size>len(data):raise ValueError('Invalid member size')
        body=data[at:at+size];at+=size+(size%2)
        if name.startswith('#1/'):
            n=int(name[3:])
            if n>len(body) or n<=0:raise ValueError('Invalid long name')
            name=body[:n].rstrip(b'\0').decode();body=body[n:]
        if name not in ('__.SYMDEF','__.SYMDEF SORTED','__.SYMDEF_64','__.SYMDEF_64 SORTED'):
            count+=1
            yield name,body
    if at!=len(data) or not count:raise ValueError('Incomplete archive')

def members(data):
    return [{'name':name,'sha256':sha(body),'bytes':len(body),'instruction_digest':instruction_digest(body)}
            for name,body in payloads(data)]

def inventory(path):
    arch=subprocess.check_output(['xcrun','lipo','-archs',path],text=True).strip()
    if arch!='arm64':raise ValueError('Expected thin arm64 iOS archive')
    data=path.read_bytes();r=members(data)
    syms=set()
    for line in subprocess.check_output(['xcrun','nm','-gUj',path],text=True).splitlines():
        if line and not line.endswith(':'):syms.add(line)
    api={x for x in syms if x.startswith(('_uniffi_bdkffi_', '_ffi_bdkffi_'))}
    if len(api)<100:raise ValueError('Unexpected UniFFI export inventory')
    return {'bytes':len(data),'sha256':sha(data),'members':r,'all_exported_symbols':len(syms),'uniffi_exports':sorted(api)}
def main():
    p=argparse.ArgumentParser();p.add_argument('published',type=Path);p.add_argument('rebuilt',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    old=inventory(a.published);new=inventory(a.rebuilt)
    if old['sha256']!='b5106bc00a27ee1b4fc828c8be21c56224557ab4f163d6c11fb0d71f3a6bf8ec':
        raise ValueError('Unexpected distributed BDK 3.1.1 iOS slice')
    left=Counter(x['sha256'] for x in old['members']);right=Counter(x['sha256'] for x in new['members'])
    common=sum((left & right).values());a1=set(old['uniffi_exports']);a2=set(new['uniffi_exports'])
    def code_counts(which):return Counter(x['instruction_digest'] for x in which['members'] if x['instruction_digest'])
    pcode,rcode=code_counts(old),code_counts(new)
    result=dict(published_objects_with_code=sum(pcode.values()),rebuilt_objects_with_code=sum(rcode.values()),common_instruction_digests=sum((pcode & rcode).values()),bridge_commit='1c5f4863c6a53cc9d063d34c4e13c91fea5c58de',rust_version='1.90.0',deployment_target='15.0',
        profile='release-smaller',target='aarch64-apple-ios',published=old,rebuilt=new,
        whole_archive_identical=old['sha256']==new['sha256'],common_member_hashes_counting_multiplicity=common,
        published_only_ffi=sorted(a1-a2),rebuilt_only_ffi=sorted(a2-a1),scope='The independent device-slice build uses the published source and lock. Matching exported names or some objects is insufficient to prove equivalent machine code; only archive byte equality proves an identical archive.')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Archive bytes identical:',result['whole_archive_identical'],'; identical objects:',common,'of',len(old['members']),'; public/absent/additional FFI names:',len(a1),len(a1-a2),len(a2-a1))
if __name__=='__main__':main()
