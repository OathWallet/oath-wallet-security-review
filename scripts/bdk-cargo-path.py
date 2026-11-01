#!/usr/bin/env python3
"""Identify the last differing instruction digest on the hosted SDK 18.5 reconstruction."""
import argparse,hashlib,importlib.util,json,re,struct,subprocess,tempfile
from pathlib import Path

def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def file_offset(obj,kind,address):
    at=32; matches=[]
    for _ in range(struct.unpack_from('<I',obj,16)[0]):
        cmd,n=struct.unpack_from('<II',obj,at)
        if cmd==0x19:
            for j in range(struct.unpack_from('<I',obj,at+64)[0]):
                sect,_,start,size,off=struct.unpack_from('<16s16sQQI',obj,at+72+80*j)
                if sect.rstrip(b'\0').decode()==kind and start<=address<start+size:matches.append(off+address-start)
        at+=n
    offset,=matches;return offset

PUBLISHED='/Users/runner/.rustup/toolchains/1.90.0-aarch64-apple-darwin/bin/cargo'
HOSTED='/Users/runner/work/oath-wallet-security-review/oath-wallet-security-review/independent/toolchains/toolchains/1.90.0-aarch64-apple-darwin/bin/cargo'
TARGET='uniffi_testing-d5b6ff1829c838e7.uniffi_testing.2472df9cc30629ec-cgu.0.rcgu.o'
SYMBOL='__ZN14uniffi_testing24get_cargo_build_messages17he9666a7cefeebc81E'
def main():
    p=argparse.ArgumentParser()
    for k in ('archive','comparison','output'):p.add_argument(k,type=Path)
    a=p.parse_args();r=json.loads(a.comparison.read_bytes());ap=module('compare-bdk-archives')
    assert r['published']['sha256']==hashlib.sha256(a.archive.read_bytes()).hexdigest()=='b5106bc00a27ee1b4fc828c8be21c56224557ab4f163d6c11fb0d71f3a6bf8ec'
    records=[next(x for x in r[k]['members'] if x['name']==TARGET) for k in ('published','rebuilt')]
    obj=bytearray(subprocess.check_output(['xcrun','ar','-p',a.archive,TARGET]))
    assert hashlib.sha256(obj).hexdigest()==records[0]['sha256'] and ap.instruction_digest(obj)==records[0]['instruction_digest']
    with tempfile.TemporaryDirectory() as t:
        image=Path(t)/'member.o';image.write_bytes(obj)
        symbols=subprocess.check_output(['xcrun','llvm-objdump','--macho','--syms',image],text=True)
        entry,=re.findall(r'^([0-9a-f]+) .* __TEXT,__text '+SYMBOL+'$',symbols,re.M)
        start=int(entry,16)
        dis=subprocess.check_output(['xcrun','llvm-objdump','-dr','--start-address='+hex(start),'--stop-address='+hex(start+48),image],text=True)
        mov,=re.findall(r'^\s*([0-9a-f]+): 528008c1\s+mov\s+w1, #0x46',dis,re.M)
        labels=re.findall(r'ARM64_RELOC_PAGE(?:OFF12|21)\s+(l_anon\.\w+\.\d+)',dis)
        assert len(labels)==2 and labels[0]==labels[1] and 'ARM64_RELOC_BRANCH26\t__ZN3std3sys7process4unix6common7Command3new' in dis
        coord,=re.findall(r'^([0-9a-f]+) .* __TEXT,__const '+re.escape(labels[0])+'$',symbols,re.M)
        pos=file_offset(obj,'__const',int(coord,16));assert obj[pos:pos+len(PUBLISHED)]==PUBLISHED.encode()
        at=file_offset(obj,'__text',int(mov,16));assert struct.unpack_from('<I',obj,at)[0]==0x52800001+(len(PUBLISHED)<<5)
        struct.pack_into('<I',obj,at,0x52800001+(len(HOSTED)<<5));predicted=ap.instruction_digest(obj)
        assert predicted==records[1]['instruction_digest'] and predicted!=records[0]['instruction_digest']
    result=dict(archive_sha256=r['published']['sha256'],member=TARGET,function=SYMBOL,instruction_offset_in_function=int(mov,16)-start,
                publisher_path_components=PUBLISHED.split('/')[1:],publisher_length=len(PUBLISHED),hosted_path_components=HOSTED.split('/')[1:],hosted_length=len(HOSTED),
                original_digest=records[0]['instruction_digest'],predicted_digest=predicted,hosted_digest=records[1]['instruction_digest'],
                scope='In-memory change of one AArch64 immediate reproduces the remaining hosted instruction-section digest. The original load resolves to the embedded Cargo path and the call relocation resolves to Command::new. Archives, data, relocations and distributed executable equivalence are distinct.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print('Reproduced remaining instruction digest with verified Cargo path lengths',len(PUBLISHED),len(HOSTED))
if __name__=='__main__':main()
