#!/usr/bin/env python3
"""Compare each historical aezeed archive against the earliest public bridge reconstruction."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import struct
import subprocess
import tarfile
import tempfile
import os

ROOT=Path(__file__).resolve().parents[1]
BASE='c7cdbde5e9f136b595500e92fbc904b107dcd8ee'
BRIDGE='ae5a35cec58f51bcfd6de3cd55950b47fa055a51'

def metadata(payload):
    assert payload.startswith(b'\xff Go buildinf:\x08\x02')
    pos=32;values=[]
    for _ in range(2):
        value=shift=0
        while True:
            b=payload[pos];pos+=1;value|=(b&127)<<shift
            if b<128:break
            shift+=7
            if shift>63:raise ValueError('Bad Go build-info length')
        if value>len(payload)-pos:raise ValueError('Truncated build info')
        values.append(payload[pos:pos+value]);pos+=value
    return values

def sections(obj):
    items={};pos=32
    for _ in range(struct.unpack_from('<I',obj,16)[0]):
        cmd,n=struct.unpack_from('<2I',obj,pos)
        if cmd==25:
            count=struct.unpack_from('<I',obj,pos+64)[0]
            assert n==72+80*count
            for j in range(count):
                s,g,addr,size,off=struct.unpack_from('<16s16sQQI',obj,pos+72+80*j)
                if off:
                    assert off+size<=len(obj)
                    items[(g.rstrip(b'\0').decode(),s.rstrip(b'\0').decode())]=(addr,obj[off:off+size])
        pos+=n
    return items

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    src=a.source.resolve();git=lambda *args:subprocess.check_output(['git','-C',src,*args]);sha=lambda b:hashlib.sha256(b).hexdigest()
    archive=runpy.run_path(str(ROOT/'scripts/compare-bdk-archives.py'))['payloads']
    describe=runpy.run_path(str(ROOT/'scripts/bdk-archive-differences.py'))['describe']
    evidence={}
    with tempfile.TemporaryDirectory(prefix='oath-historical-bridge-') as tmp:
        w=Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(git('archive',BRIDGE,'Tools/AezeedBridge'))) as t:t.extractall(w,filter='data')
        out=w/'Packages/OathAezeed';out.mkdir(parents=True)
        toolchain=subprocess.check_output(['go','version'],text=True).strip();assert 'go1.26.5' in toolchain
        env=dict(os.environ,GOTOOLCHAIN='local',GOWORK='off',GOFLAGS='-mod=readonly')
        subprocess.run(['go','mod','verify'],cwd=w/'Tools/AezeedBridge',env=env,check=True)
        subprocess.run(['bash','build.sh'],cwd=w/'Tools/AezeedBridge',env=env,check=True)
        for platform in ('ios-arm64','ios-arm64-simulator','macos-arm64'):
            path='Packages/OathAezeed/OathAezeedCore.xcframework/'+platform+'/libOathAezeedCore.a'
            raw=git('show',BASE+':'+path);fresh=(w/path).read_bytes()
            left=dict(archive(raw));right=dict(archive(fresh));assert left.keys()==right.keys()
            native=[n for n in left if n!='go.o'];assert all(re.fullmatch(r'\d+\.o',n) and left[n]==right[n] for n in native)
            pair=(left['go.o'],right['go.o']);details=[describe(o) for o in pair];sects=[sections(o) for o in pair]
            assert details[0].keys()==details[1].keys()
            different={k:[field for field in v if v[field]!=details[1][k][field]] if isinstance(v,dict) else ['raw bytes']
                       for k,v in details[0].items() if v!=details[1][k]}
            assert not any('relocations' in diff for diff in different.values())
            t0,t1=[s['__TEXT','__text'][1] for s in sects]
            pat=rb'^\xff Go build ID: "([a-zA-Z0-9_/-]+)"\n \xff'
            m0,m1=[re.match(pat,t) for t in (t0,t1)];assert m0 and m1 and m0.span(1)==m1.span(1)
            i,j=m0.span(1);assert t0[:i]==t1[:i] and t0[j:]==t1[j:]
            head=[metadata(s['__DATA','__go_buildinfo'][1]) for s in sects]
            assert head[0][0]==head[1][0]==b'go1.26.5'
            old,new=(k[1] for k in head)
            fields=b''.join(re.findall(rb'build\tvcs(?:\.[a-z]+)?=[^\n]+\n',old))
            assert b'build\tvcs.modified=true\n' in fields and old.count(fields)==1 and old.replace(fields,b'')==new
            ro0,ro1=[s['__TEXT','__rodata'][1] for s in sects]
            assert ro0.count(old)==1 and ro1.count(new)==1
            a0,b0=ro0.split(old);a1,b1=ro1.split(new);assert a0==a1 and b0.lstrip(bytes(1))==b1.lstrip(bytes(1))
            d0,d1=[s['__DATA','__data'][1] for s in sects]
            obj=w/'historical-go.o';obj.write_bytes(pair[0]);symbols=subprocess.check_output(['go','tool','nm','-size','-sort','address',obj],text=True)
            address,=re.findall(r'^\s*([0-9a-f]+)\s+16 D runtime\.modinfo$',symbols,re.M)
            at=int(address,16)-sects[0]['__DATA','__data'][0]+8
            assert struct.unpack_from('<Q',d0,at)[0]==len(old) and struct.unpack_from('<Q',d1,at)[0]==len(new)
            assert d0[:at]+d0[at+8:]==d1[:at]+d1[at+8:]
            evidence[platform]=dict(historical_sha256=sha(raw),rebuilt_sha256=sha(fresh),whole_match=raw==fresh,
                identical_c_objects={n:sha(left[n]) for n in native},all_go_section_relocations_equal=True,
                go_text_bytes=len(t0),build_id_offset=i,build_id_length=j-i,go_text_outside_build_id_identical=True,
                identical_build_info_after_removing_vcs_fields=True,original_reports_modified_checkout=True,
                readonly_data_outside_module_info_and_padding_identical=True,nonmatching_go_components=different,
                writable_data_outside_modinfo_length_identical=True,reference_module_info_length=len(old),rebuilt_module_info_length=len(new))
    result=dict(baseline=BASE,earliest_public_source=BRIDGE,compiler=toolchain,xcode=subprocess.check_output(["xcodebuild","-version"],text=True).splitlines(),slices=evidence,
                scope='Real historical Git blobs versus clean rebuild. Object code bytes outside the embedded Go build-ID string, plus the listed raw sections, were compared. Differing debug info, symbols, load commands and original archive hashes remain visible. Embedded VCS metadata reports a modified checkout and does not identify its uncommitted inputs.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('Verified all three historical slice comparisons')
if __name__=='__main__':main()
