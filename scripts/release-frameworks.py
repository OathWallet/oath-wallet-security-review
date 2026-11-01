#!/usr/bin/env python3
"""Compare executable sections of embedded Wallet Core frameworks with resolved iOS slices."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import subprocess
from source_state import require_source_state

def inspect(path):
    data=path.read_bytes()
    magic,cpu,_,kind,ncmds,size,_,_=struct.unpack_from('<IiiIIIII',data)
    if (magic,cpu)!=(0xfeedfacf,0x0100000c) or kind not in (2,6) or size>len(data)-32:
        raise ValueError('Expected a thin 64-bit arm64 executable or dylib')
    at=32;uuid=None;code={}
    for _ in range(ncmds):
        cmd,n=struct.unpack_from('<II',data,at)
        if n<8 or at+n>32+size:raise ValueError('Malformed Mach-O load command')
        if cmd==0x1b:
            if n!=24 or uuid:raise ValueError('Invalid UUID command')
            uuid=data[at+8:at+24].hex()
        if cmd==0x19:
            nsects=struct.unpack_from('<I',data,at+64)[0]
            if n!=72+nsects*80:raise ValueError('Invalid section list')
            for j in range(nsects):
                pos=at+72+j*80
                sect,seg,_,length,off=struct.unpack_from('<16s16sQQI',data,pos)
                flags=struct.unpack_from('<I',data,pos+64)[0]
                if flags & (0x80000000|0x400): # S_ATTR_PURE_INSTRUCTIONS or SOME_INSTRUCTIONS
                    name=seg.rstrip(b'\0').decode()+'.'+sect.rstrip(b'\0').decode()
                    if name in code or off+length>len(data):raise ValueError('Invalid executable section')
                    code[name]={'bytes':length,'sha256':hashlib.sha256(data[off:off+length]).hexdigest()}
        at+=n
    if at!=32+size or not uuid or '__TEXT.__text' not in code:raise ValueError('Missing or incomplete executable identity')
    return dict(sha256=hashlib.sha256(data).hexdigest(),uuid=uuid,executable_sections=code)

def main():
    p=argparse.ArgumentParser()
    for name in ('source','derived','build_result','output'):p.add_argument(name,type=Path)
    a=p.parse_args();build=json.loads(a.build_result.read_bytes());pin=require_source_state(a.source,build['source_commit'])
    if build['status']!='passed' or hashlib.sha256(a.build_result.with_name('build.log').read_bytes()).hexdigest()!=build['log_sha256']:
        raise ValueError('Successful hashed build log required')
    app=a.derived/'Build/Products/Release-iphoneos/Oath Wallet.app'
    links={};embedded={};core={}
    info=plistlib.loads((app/'Info.plist').read_bytes())
    for bundle in [app,*sorted((app/'Frameworks').glob('*.framework'))]:
        name=plistlib.loads((bundle/'Info.plist').read_bytes())['CFBundleExecutable']
        exe=bundle/name
        deps=subprocess.check_output(['xcrun','otool','-L',exe],text=True).splitlines()[1:]
        links[name]=[line.strip().split(' (compatibility version',1)[0] for line in deps]
        embedded[name]=inspect(exe)
    for name in ('WalletCore','WalletCoreSwiftProtobuf'):
        root=a.derived/'SourcePackages/artifacts/walletcore'/name/(name+'.xcframework')
        matches=[x for x in plistlib.loads((root/'Info.plist').read_bytes())['AvailableLibraries']
                 if x['SupportedPlatform']=='ios' and not x.get('SupportedPlatformVariant') and 'arm64' in x['SupportedArchitectures']]
        if len(matches)!=1:raise ValueError('Unexpected arm64 device slice')
        member=matches[0];src=root/member['LibraryIdentifier']/member['LibraryPath']/name
        resolved=inspect(src);actual=embedded[name]
        if resolved['uuid']!=actual['uuid'] or resolved['executable_sections']!=actual['executable_sections']:
            raise ValueError('Resolved and embedded executable code differs: '+name)
        core[name]=dict(resolved=resolved,whole_file_identical=actual['sha256']==resolved['sha256'],slice=member['LibraryIdentifier'])
    result=dict(source_commit=pin,check='release-frameworks',status='passed',build_log_sha256=build['log_sha256'],
        product=info['CFBundleIdentifier'],embedded=embedded,dependencies=links,comparison=core,
        scope='Exact embedded files, Mach-O UUIDs, instruction-bearing sections and dynamic library references for this generic unsigned iOS build. Only the two dynamic Wallet Core products are compared against resolved XCFramework device slices. This is not a rebuild of Wallet Core or a comparison with the App Store.')
    out=a.output;out.mkdir(parents=True,exist_ok=True);log=out/'release-frameworks.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (out/'release-frameworks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Compared two resolved frameworks;',len(embedded),'embedded executable images inventoried')
if __name__=='__main__':main()
