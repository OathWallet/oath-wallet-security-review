#!/usr/bin/env python3
"""Trace immutable registry source from rustc dep-info files of the independent device build."""
import argparse,collections,hashlib,json,shlex,tarfile,tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(file):
    with file.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def depfile(row):
    f=Path(row['filenames'][0])
    if row['target']['kind']==['custom-build']:
        name=row['target']['name'].replace('-','_')
        d,=f.parent.glob(name+'-*.d');return d
    if f.parent.name=='deps':return f.with_name(f.stem.removeprefix('lib')+'.d')
    return f.with_suffix('.d')
def main():
    p=argparse.ArgumentParser()
    for arg in ('messages','packages','bridge','cargo_home','inventory','trace'):p.add_argument(arg,type=Path)
    a=p.parse_args();bridge=a.bridge.resolve();target=bridge/'target'
    lock_file=bridge/'Cargo.lock'
    if sha(lock_file)!='a7b22b8c0669d16ad11a3ea7af0c78f22185a91bd9c20ba59ecfd23468d4d9b9':raise ValueError('Unexpected bridge Cargo lock')
    lock=tomllib.loads(lock_file.read_text());registered={r['name']+'-'+r['version']:r for r in lock['package'] if 'checksum' in r}
    packages=json.loads(a.packages.read_bytes())
    if packages['bridge_commit']!='1c5f4863c6a53cc9d063d34c4e13c91fea5c58de' or packages['lock_sha256']!=sha(lock_file):raise ValueError('Wrong build package inventory')
    crates={r['name']+'-'+r['version']:r for r in packages['packages']}
    ledgers=json.loads((ROOT/'scope/upstream-bitcoin-signers.json').read_bytes())
    existing={c['name']+'-'+c['version']:c for c in ledgers['crates']};known={r['path']:r for r in ledgers['files']}
    ffi={r['path']:r for r in json.loads((ROOT/'scope/upstream-bdk-ffi.json').read_bytes())['files']}
    archives={};selected={};generated={};cmdrows=0;finished=False
    registry,=(a.cargo_home/'registry/src').glob('index.crates.io-*');registry=registry.resolve()
    for line in a.messages.read_text().splitlines():
        row=json.loads(line)
        if row['reason']=='build-finished':finished=row['success'];continue
        if row['reason']!='compiler-artifact':continue
        cmdrows+=1;out=Path(row['filenames'][0]).resolve().relative_to(target).as_posix()
        role='ios-target' if out.startswith('aarch64-apple-ios/') else 'build-host'
        d=depfile(row);inputs=shlex.split(d.read_text().splitlines()[0].partition(': ')[2])
        if not inputs:raise ValueError('Missing compiler input list for '+d.name)
        for raw in inputs:
            file=Path(raw)
            if not file.is_absolute():file=bridge/file
            file=file.resolve(strict=True)
            if file.is_relative_to(target):
                # Hashed separately. Generated names or contents can reflect the toolchain.
                rel=file.relative_to(target).as_posix();generated[rel]=sha(file);continue
            disposition='outstanding'
            if file.is_relative_to(bridge):
                name='bdk-ffi/'+file.relative_to(bridge).as_posix();digest=ffi[name]['sha256'];owner='bridge';disposition=ffi[name]['status']
            elif file.is_relative_to(registry):
                crate,*tail=file.relative_to(registry).parts;rel='/'.join(tail);name=crate+'/'+rel;owner='registry'
                if crate not in archives:
                    entry=registered[crate];archive,=(a.cargo_home/'registry/cache').glob('*/'+crate+'.crate')
                    if sha(archive)!=entry['checksum'] or crates[crate]['registry_archive_sha256']!=entry['checksum']:raise ValueError('Registry checksum mismatch')
                    with tarfile.open(archive,'r:gz') as contents:
                        digests={}
                        for member in contents:
                            if member.isfile():
                                if member.name in digests:raise ValueError('Duplicate registry member')
                                with contents.extractfile(member) as stream:digests[member.name]=hashlib.file_digest(stream,'sha256').hexdigest()
                    archives[crate]=digests
                digest=archives[crate][name]
                if crate in existing:
                    prior=known[existing[crate]['name']+'/'+rel];disposition=prior['status']
                    if prior['sha256']!=digest:raise ValueError('Prior crate ledger differs')
                    owner='existing-crate'
            else:raise ValueError('Unclassified compiler input '+str(file))
            if name not in selected:
                if sha(file)!=digest:raise ValueError('Compiled source differs from authenticated input '+name)
                selected[name]=dict(path=name,sha256=digest,bytes=file.stat().st_size,roles=set(),owner=owner,status=disposition)
            selected[name]['roles'].add(role)
    if not finished or cmdrows<100:raise ValueError('Incomplete device build')
    for r in selected.values():r['roles']=sorted(r['roles'])
    entries=[selected[name] for name in sorted(selected)];matching=[r for r in entries if r['owner']=='registry']
    a.inventory.write_text(json.dumps(dict(bridge_commit=packages['bridge_commit'],lock_sha256=packages['lock_sha256'],files=matching,
        scope='Additional registry files selected by rustc dep-info in the independent BDK iOS build. Previously inventoried crates and bridge files are recorded in the separate trace without double-counting. Separate host and device roles; no inference of symbol reachability or review credit.'),indent=2)+'\n')
    a.trace.write_text(json.dumps(dict(bridge_commit=packages['bridge_commit'],compiler_artifacts=cmdrows,all_source=entries,generated_inputs=generated,
        scope='Traces the primary rustc depfile of each recorded Cargo compiler artifact. Build-script subprocess inputs such as C, assembly, headers and external tools need separate trace. Generated inputs are hashed but not presumed independently reproducible.'),indent=2)+'\n')
    print(cmdrows,'compiler artifacts;',len(selected),'verified source files;',len(matching),'additional ledger entries;',len(generated),'generated inputs')
if __name__=='__main__':main()
