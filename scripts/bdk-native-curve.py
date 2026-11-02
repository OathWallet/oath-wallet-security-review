#!/usr/bin/env python3
"""Test the pinned Rust bindings and linked C implementation against OpenSSL and modular addition."""
import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import tomllib
import tarfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for a in ('original','scratch','output'):
        p.add_argument(a,type=Path)
    args=p.parse_args();original=args.original.resolve();scratch=args.scratch.resolve();scratch.mkdir()
    scripts=Path(__file__).resolve().parent
    fixture=scripts.parent/'fixtures/bitcoin-native/curve.rs'
    helpers=runpy.run_path(str(scripts/'utxo-recovery-vectors.py'))
    n=helpers['N'];point=lru_cache(maxsize=None)(helpers['point']);sha=lambda b:hashlib.sha256(b).hexdigest()
    lock=original/'bdk-ffi/Cargo.lock'
    assert sha(lock.read_bytes())=='a7b22b8c0669d16ad11a3ea7af0c78f22185a91bd9c20ba59ecfd23468d4d9b9'
    cargo=original/'cargo'
    env=dict(HOME=os.environ['HOME'],CARGO_HOME=str(cargo),RUSTUP_HOME=str(original/'toolchains'),RUSTUP_TOOLCHAIN='1.90.0',
             PATH=str(cargo/'bin')+':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin')
    compiler=subprocess.check_output([cargo/'bin/rustc','-vV'],env=env,text=True)
    assert 'commit-hash: 1159e78c4747b02ef996e55082b704c09b970588' in compiler
    (scratch/'src').mkdir();(scratch/'src/main.rs').write_bytes(fixture.read_bytes());(scratch/'src/der.rs').write_bytes(fixture.with_name('der.rs').read_bytes())
    (scratch/'Cargo.toml').write_text('[package]\nname="audit-bdk-curve"\nversion="0.0.0"\nedition="2021"\n[dependencies]\nsecp256k1={version="=0.29.1",default-features=false,features=["std","hashes","rand-std","recovery","serde"]}\n')
    (scratch/'Cargo.lock').write_bytes(lock.read_bytes())
    messages=scratch/'compilation.jsonl'
    with messages.open('w') as log:
        subprocess.run([cargo/'bin/cargo','build','--release','--offline','--message-format=json'],cwd=scratch,env=env,stdout=log,check=True)
    prior={(r['name'],r['version']):r['checksum'] for r in tomllib.loads(lock.read_text())['package'] if 'checksum' in r}
    now=tomllib.loads((scratch/'Cargo.lock').read_text())['package']
    records=[json.loads(line) for line in messages.read_text().splitlines()]
    assert records[-1]=={'reason':'build-finished','success':True}
    compiled_ids={r['package_id'].split('#')[-1] for r in records if r['reason']=='compiler-artifact'}
    verified={};dormant=[];source_files=0
    for entry in now:
        if entry['name']=='audit-bdk-curve':continue
        version=entry['version'];name=entry['name'];package=name+'-'+version
        assert entry['checksum']==prior[(name,version)]
        if name+'@'+version not in compiled_ids:
            dormant.append(package)
            continue
        archive,=(cargo/'registry/cache').glob('*/'+package+'.crate')
        assert sha(archive.read_bytes())==entry['checksum']
        cratedir,=(cargo/'registry/src').glob('*/'+package)
        with tarfile.open(archive,'r:gz') as tar:
            for item in tar:
                if not item.isfile():continue
                relative=Path(item.name).relative_to(package)
                if relative.is_absolute() or '..' in relative.parts:raise ValueError('Invalid source archive path')
                with tar.extractfile(item) as stream:
                    assert hashlib.file_digest(stream,'sha256').hexdigest()==sha((cratedir/relative).read_bytes())
                source_files+=1
        verified[package]=entry['checksum']
    packages=json.loads((original/'packages.json').read_bytes())['packages']
    for name in ['secp256k1','secp256k1-sys']:
        expected,=[r for r in packages if r['name']==name]
        compiled,=[r for r in records if r['reason']=='compiler-artifact' and r['target']['kind']==['lib'] and r['target']['name']==name.replace('-','_')]
        assert sorted(compiled['features'])==expected['features']
    pairs=[(0,0),(n,0),(n+1,1),(2**256-1,1),(1,0),(1,n),(1,n-1),(n-1,1),(n-1,2)]
    domain=b'oath-bdk-curve-public-fixture-v1'
    for i in range(128):
        integer=lambda tag:int.from_bytes(hashlib.sha256(domain+tag+i.to_bytes(2,'big')).digest(),'big')%(n-1)+1
        k=integer(b'key');t=integer(b'tweak') if i%4 else n-k
        pairs.append((k,t))
    rows=[]
    for k,t in pairs:
        valid=0<k<n;child=(k+t)%n;ok=valid and t<n and child!=0
        rows.append(' '.join([f'{k:064x}',f'{t:064x}',point(k).hex() if valid else '-','valid' if t<n else 'invalid',f'{child:064x}' if ok else '-',point(child).hex() if ok else '-']))
    data=('\n'.join(rows)+'\n').encode()
    binary=scratch/'target/release/audit-bdk-curve'
    completed=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',binary],input=data,capture_output=True,timeout=20,check=True)
    assert completed.stdout.decode().strip()=='Verified all 137 native scalar and public point cases'
    ref=runpy.run_path(str(scripts/'secp-wrapper-vectors.py'))['vector']()
    test=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',binary,'der',ref['der'],ref['digest'],ref['public']],check=True,capture_output=True,text=True,timeout=20)
    cuts=len(bytes.fromhex(ref['der']))
    assert test.stdout.strip()==f'Verified strict and historical DER behavior, {cuts} truncations, 2048 bounded parser inputs'
    result=dict(der_fixture_sha256=sha(fixture.with_name('der.rs').read_bytes()),der_truncations=cuts,der_fuzz_cases=2048,der_fuzz_seed='6f61746864657231',status='passed',cases=len(rows),fixture_sha256=sha(fixture.read_bytes()),input_sha256=sha(data),
                seed_label=domain.decode(),lock_sha256=sha(lock.read_bytes()),host_binary_sha256=sha(binary.read_bytes()),host_compiler=compiler.strip().splitlines(),
                verified_packages=verified,verified_registry_source_files=source_files,uncompiled_lock_entries=sorted(dormant),scope='Host execution of production Rust secp256k1 0.29.1 and secp256k1-sys 0.10.1. The two crate feature sets matched the recorded device graph. Tests public/secret tweak validity and point equality, not timing or physical device execution.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(completed.stdout.decode().strip());print(test.stdout.strip())

if __name__=='__main__':main()
