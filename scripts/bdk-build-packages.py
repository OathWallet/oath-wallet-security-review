#!/usr/bin/env python3
"""Inventory packages Cargo actually compiled on the independent iOS reconstruction."""
import argparse,hashlib,json,tomllib
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    for name in ['messages','lock','cargo_home','target_dir','output']:p.add_argument(name,type=Path)
    a=p.parse_args();lock=a.lock.read_bytes()
    if hashlib.sha256(lock).hexdigest()!='a7b22b8c0669d16ad11a3ea7af0c78f22185a91bd9c20ba59ecfd23468d4d9b9':
        raise ValueError('Wrong release lockfile')
    pinned={(v['name'],v['version']):v for v in tomllib.loads(lock.decode())['package']}
    pkgs={};finished=False
    for line in a.messages.read_text().splitlines():
        row=json.loads(line);reason=row.get('reason')
        if reason=='build-finished':finished=row.get('success') is True;continue
        if reason!='compiler-artifact':continue
        manifest=Path(row['manifest_path']);decl=tomllib.loads(manifest.read_text())['package']
        name,version=decl['name'],decl['version'];locked=pinned[(name,version)]
        key=(name,version);new=key not in pkgs
        record=pkgs.setdefault(key,dict(name=name,version=version,compiled_targets=set(),roles=set(),features=set()))
        record['compiled_targets'].add(row['target']['name']+' ('+','.join(row['target']['kind'])+')')
        record['features'].update(row.get('features',[]))
        for file in row['filenames']:
            relative=Path(file).resolve().relative_to(a.target_dir.resolve());record['roles'].add('ios-target' if relative.parts[0]=='aarch64-apple-ios' else 'build-host')
        if new and 'checksum' in locked:
            archive,=list((a.cargo_home/'registry/cache').glob('*/'+name+'-'+version+'.crate'))
            with archive.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
            if digest!=locked['checksum']:raise ValueError('Cargo archive mismatch: '+name)
            record['registry_archive_sha256']=digest
        elif new and (name,version)!=('bdk-ffi','3.1.1'):
            raise ValueError('Unexpected unverified source: '+name+' '+version)
    if not finished or ('bdk-ffi','3.1.1') not in pkgs:raise ValueError('No completed bridge build')
    for r in pkgs.values():
        for k in ['compiled_targets','roles','features']:r[k]=sorted(r[k])
    result=dict(bridge_commit='1c5f4863c6a53cc9d063d34c4e13c91fea5c58de',lock_sha256=hashlib.sha256(lock).hexdigest(),packages=[pkgs[k] for k in sorted(pkgs)],
        scope='Compiler artifact messages from the isolated Rust build, including host tools and build scripts. Registry archives matched Cargo.lock. Compilation does not establish link survival, manual review or equivalence with the distributed binary.')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(len(pkgs),'packages emitted compiler artifacts;',sum('registry_archive_sha256' in x for x in pkgs.values()),'archive hashes verified')
if __name__=='__main__':main()
