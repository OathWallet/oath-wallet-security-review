#!/usr/bin/env python3
"""Trace Swift and C compilation inputs in one successful unsigned arm64 iOS build."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def c_dependencies(path):
    data=path.read_text().replace('\\\n',' ')
    name,sep,value=data.partition(':')
    if not sep or name!='dependencies':raise ValueError('Unknown compiler dependency format')
    return [Path(x) for x in shlex.split(value)]

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--build-result',type=Path,required=True)
    p.add_argument('--derived-data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-packages-dir',type=Path,help='Explicit clonedSourcePackagesDirPath used by xcodebuild')
    a=p.parse_args();source=a.source.resolve();derived=a.derived_data.resolve()
    build=json.loads(a.build_result.read_bytes()); pin=require_source_state(source,build['source_commit'])
    log=a.build_result.with_name('build.log')
    if build['status']!='passed' or digest(log)!=build['log_sha256'] or 'generic/platform=iOS' not in build['command'] or 'CODE_SIGNING_ALLOWED=NO' not in build['command']:
        raise ValueError('Expected successful, hashed unsigned generic iOS build')
    ids=re.findall(r'^Build description signature: ([a-f0-9]{32})$',log.read_text(),re.M)
    if len(ids)!=1:raise ValueError('Expected exactly one build description')
    inter=derived/'Build/Intermediates.noindex';manifest=inter/'XCBuildData'/(ids[0]+'.xcbuilddata')/'manifest.json'
    cmds=json.loads(manifest.read_bytes())['commands']
    package_root = (a.source_packages_dir or derived/'SourcePackages').resolve()
    if a.source_packages_dir:
        if '-clonedSourcePackagesDirPath' not in build['command'] or build['command'][build['command'].index('-clonedSourcePackagesDirPath')+1] != str(package_root):
            raise ValueError('Package root differs from the recorded build invocation')
    pkgs=package_root/'checkouts';toolchain=Path(subprocess.check_output(['xcrun','--find','swiftc'],text=True).strip()).resolve()
    developer=next(x for x in toolchain.parents if x.name=='Developer')
    scope=json.loads((ROOT/'scope/inventory.json').read_bytes());assert scope['source_commit']==pin
    known={'application/'+r['path']:r['sha256'] for r in scope['files']}
    other=json.loads((ROOT/'scope/upstream-xcode-packages.json').read_bytes())
    known.update({'package/'+r['path']:r['sha256'] for r in other['files'] if 'sha256' in r})
    swift=json.loads((ROOT/'scope/upstream-swiftdraw.json').read_bytes())
    known.update({'package/SwiftDraw/'+r['path']:r['sha256'] for r in swift['files']})
    def identify(raw):
        real=Path(raw).resolve(strict=True)
        for root,prefix in [(pkgs,'package'),(inter,'generated'),(source,'application'),(developer,'toolchain'),(package_root/'artifacts','artifact'),(derived/'Build/Products','product')]:
            if real.is_relative_to(root):
                return prefix+'/'+real.relative_to(root).as_posix()
        raise ValueError('Unexpected source origin at '+str(real))
    files={};units=[];binaries=set()
    def add(path,role,target):
        ident=identify(path)
        if ident.startswith('toolchain/'):return
        if ident not in files:
            actual=digest(path)
            if ident.startswith(('package/','application/')) and known.get(ident)!=actual:
                raise ValueError('Compiled file differs from scoped source: '+ident)
            files[ident]=dict(path=ident,sha256=actual,roles=set(),targets=set())
        files[ident]['roles'].add(role);files[ident]['targets'].add(target)
    for command in cmds.values():
        tool=command['tool']
        if tool=='swift-driver-compilation':
            (lst,)=[Path(i) for i in command['inputs'] if i.endswith('.SwiftFileList')]
            target=lst.stem;actual={Path(x).resolve() for x in lst.read_text().splitlines()};declared={Path(x).resolve() for x in command['inputs'] if x.endswith('.swift')}
            if not actual or actual!=declared:raise ValueError('Swift input list mismatch for '+target)
            for swift_file in actual:add(swift_file,'swift',target)
            units.append(dict(target=target,language='swift',inputs=len(actual)))
        elif tool=='ccompile':
            (cfile,)=[Path(x) for x in command['inputs'] if x.endswith(('.c','.cpp','.m','.mm','.cc','.S','.s'))]
            (obj,)=[Path(x) for x in command['outputs'] if x.endswith('.o')]
            if obj.parent.name!='arm64' or 'Release-iphoneos' not in obj.parts:raise ValueError('Unexpected C output target')
            target=obj.parents[2].stem.removesuffix('-t');deps=c_dependencies(obj.with_suffix('.d'))
            add(cfile,'c-family',target)
            for dep in deps:
                if dep.resolve()!=cfile.resolve():add(dep,'clang-dependency',target)
            units.append(dict(target=target,language='c-family',file=identify(cfile)))
        elif tool=='process-xcframework':
            (fw,)=[x for x in command['inputs'] if x.rstrip('/').endswith('.xcframework')]
            binaries.add(identify(fw))
    if 'Oath Wallet' not in {x['target'] for x in units} or not binaries:raise ValueError('Missing app or binary processing')
    for row in files.values():
        for k in ['roles','targets']:row[k]=sorted(row[k])
    result=dict(source_commit=pin,check='release-inputs',status='passed',build_log_sha256=build['log_sha256'],
                build_description=ids[0],manifest_sha256=digest(manifest),compiler_units=sorted(units,key=lambda x:(x['language'],x['target'],x.get('file',''))),
                processed_xcframeworks=sorted(binaries),files=[files[k] for k in sorted(files)],
                scope='Swift and C-family compile command inputs and Clang .d dependencies from this Release arm64 build. Source selection alone does not establish symbol reachability, resource behavior or App Store binary equivalence. Apple toolchain files are excluded.')
    a.output.mkdir(parents=True,exist_ok=True)
    trail=a.output/'release-inputs.log';trail.write_text(json.dumps(result,indent=2)+'\n');result.update(log=trail.name,log_sha256=digest(trail))
    (a.output/'release-inputs.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(files),'distinct non-toolchain compiler inputs',len(units),'compile units')
if __name__=='__main__':main()
