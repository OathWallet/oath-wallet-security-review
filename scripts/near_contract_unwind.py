#!/usr/bin/env python3
"""Paired native SDK mock ABI replay; never changes the shipped contract or app."""
import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import tomllib
import near_contract_unit as base

SDK = {'near-sdk':'4.0.0-pre.4','near-sys':'0.1.0'}
WRONG_KEY = 'tests::test_delete_request_panic_wrong_key'
WRONG_FIXTURE = 'tests::test_panics_add_key_different_account'
MUTANT_FAILURES = {
    'audit_contract::characterizes_confirmation_retained_after_quorum_authorized_member_removal',
    'audit_rejections::foreign_key_cannot_create_request',
    'audit_rejections::foreign_key_cannot_delete_even_after_cooldown',
    'audit_rejections::removed_member_cannot_add_a_new_confirmation',
}


def patch_mock(sdk, sys):
    a = 'extern "C" fn panic_utf8'
    b = '    pub fn panic_utf8(len: u64, ptr: u64) -> !;'
    if sdk.count(a) != 1 or sys.count(b) != 1:
        raise ValueError('Unexpected SDK panic boundary')
    return (sdk.replace(a,'extern "C-unwind" fn panic_utf8'),
            sys.replace(b,'    #[cfg(target_arch = "wasm32")]\n'+b)+
            '\n#[cfg(not(target_arch = "wasm32"))]\nextern "C-unwind" {\n'+b+'\n}\n')


def normalize_lock(original, adapted):
    adapted = json.loads(json.dumps(adapted))
    originals = {(p['name'],p['version']):p for p in original['package']}
    for name, version in SDK.items():
        matches = [p for p in adapted['package'] if p['name']==name and p['version']==version]
        if len(matches)!=1 or 'source' in matches[0] or 'checksum' in matches[0]:
            raise ValueError('Expected exactly the two local SDK copies')
        for key in ('source','checksum'): matches[0][key] = originals[(name,version)][key]
    return base.verify_lock(original,adapted)


def classify(name, code, log, messages):
    passed = code==0 and 'test result: ok. 1 passed; 0 failed; 0 ignored;' in log
    if name==WRONG_FIXTURE:
        return 'invalid_fixture_pass' if passed and 'called `Result::unwrap()` on an `Err` value' in log else 'failed'
    if name in messages:
        if messages[name] not in log: return 'failed'
        if code==-6 and 'non-unwinding panic' in log: return 'blocked_sdk_abort'
        if passed: return 'invalid_fixture_pass' if name==WRONG_KEY else 'passed'
        return 'failed'
    return 'passed' if passed else 'failed'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('upstream','scratch','output','cargo_home'): p.add_argument(name,type=Path)
    p.add_argument('--mode',choices=('original','unwind','mutant'),required=True)
    a=p.parse_args(); upstream,scratch,out,cache=[getattr(a,n).resolve() for n in ('upstream','scratch','output','cargo_home')]
    base.require_source_state(upstream,base.UPSTREAM_COMMIT)
    if scratch.exists() or out.exists(): raise ValueError('Use fresh directories')
    (scratch/'src').mkdir(parents=True);out.mkdir(parents=True)
    started=time.monotonic()
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','LANG','LC_ALL'}}
    env.update(CARGO_HOME=str(cache),CARGO_TARGET_DIR=str(scratch/'build'))
    versions={n:subprocess.check_output([n,'--version'],env=env,text=True).strip() for n in ('rustc','cargo')}
    if any('1.96.1' not in v.split() for v in versions.values()): raise ValueError('Requires Rust/Cargo 1.96.1')
    source=(upstream/'multisig2/src/lib.rs').read_bytes();assert base.sha(source)==base.SOURCE_SHA
    original_source=source
    if a.mode=='mutant':
        needle=b'if self.members.contains(&member) {';assert source.count(needle)==1
        source=source.replace(needle,b'if true {')
        (out/'mutation.patch').write_text(''.join(difflib.unified_diff(original_source.decode().splitlines(True),source.decode().splitlines(True),fromfile='original/lib.rs',tofile='synthetic-mutant/lib.rs')))
    overlays=[(base.ROOT/'fixtures/near-contract-unit'/name).read_bytes() for name in ('audit.rs','rejections.rs')]
    (scratch/'src/lib.rs').write_bytes(source+b'\n'+b'\n'.join(overlays))
    manifest=(upstream/'multisig2/Cargo.toml').read_text().split('[dev-dependencies]')[0]
    original_lock=tomllib.loads((upstream/'multisig2/Cargo.lock').read_text())
    sdk_files=[]; archives=[]
    for name, version in SDK.items():
        package=next(p for p in original_lock['package'] if (p['name'],p['version'])==(name,version))
        matches=list((cache/'registry/cache').glob('*/'+name+'-'+version+'.crate'))
        if len(matches)!=1 or base.sha(matches[0].read_bytes())!=package['checksum']: raise ValueError('Wrong SDK archive')
        archives.append({'name':name,'version':version,'sha256':package['checksum']})
        with tarfile.open(matches[0]) as tar:
            for member in tar.getmembers():
                path=Path(member.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0]!=name+'-'+version: raise ValueError('Unsafe archive member')
                if member.isdir(): continue
                if not member.isfile(): raise ValueError('Unexpected non-regular member')
                rel=Path(name).joinpath(*path.parts[1:]);data=tar.extractfile(member).read()
                target=scratch/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                sdk_files.append({'path':str(rel),'original_sha256':base.sha(data)})
    targets=[scratch/'near-sdk/src/environment/mock/mocked_blockchain.rs',scratch/'near-sys/src/lib.rs']
    if a.mode!='original':
        originals=[p.read_text() for p in targets]
        for path,before,after in zip(targets,originals,patch_mock(*originals)):
            path.write_text(after)
            (out/(path.parent.name+'-unwind.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/'+str(path.relative_to(scratch)),tofile='audit-only/'+str(path.relative_to(scratch)))))
    for row in sdk_files: row['executed_sha256']=base.sha((scratch/row['path']).read_bytes())
    changed=[r['path'] for r in sdk_files if r['original_sha256']!=r['executed_sha256']]
    expected=[] if a.mode=='original' else [str(t.relative_to(scratch)) for t in targets]
    if sorted(changed)!=sorted(expected): raise ValueError('Unexpected SDK source changes')
    manifest+='\n[patch.crates-io]\nnear-sdk = { path = "near-sdk" }\nnear-sys = { path = "near-sys" }\n'
    (scratch/'Cargo.toml').write_text(manifest);(scratch/'Cargo.lock').write_bytes((upstream/'multisig2/Cargo.lock').read_bytes())
    with (out/'build.jsonl').open('w') as stdout,(out/'build.log').open('w') as stderr:
        built=subprocess.run(['cargo','test','--offline','--lib','--no-run','--message-format=json','--manifest-path',str(scratch/'Cargo.toml')],env=env,stdout=stdout,stderr=stderr,timeout=600)
    if built.returncode: raise RuntimeError('Build failed; logs retained')
    lock=normalize_lock(original_lock,tomllib.loads((scratch/'Cargo.lock').read_text()))
    binaries=[r['executable'] for line in (out/'build.jsonl').read_text().splitlines() if (r:=json.loads(line)).get('reason')=='compiler-artifact' and r.get('executable') and r['profile']['test']]
    if len(binaries)!=1: raise ValueError('Ambiguous test executable')
    command=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binaries[0]]
    discovery=subprocess.check_output(command+['--list'],env=env,text=True,timeout=30);(out/'discovery.log').write_text(discovery)
    names=[l.removesuffix(': test') for l in discovery.splitlines() if l.endswith(': test')]
    additional=re.findall(r'#\[test\]\s+#\[should_panic\(expected = "([^"]+)"\)\]\s+fn (\w+)',overlays[1].decode())
    messages={'tests::'+k:v for k,v in base.ABORTS.items()}
    messages.update({'audit_rejections::'+n:m for m,n in additional})
    expected={'tests::'+n for n in base.UPSTREAM_TESTS}|{'audit_contract::'+n for n in re.findall(r'#\[test\]\s+fn (\w+)',overlays[0].decode())}|{'audit_rejections::'+n for _,n in additional}
    if set(names)!=expected or len(names)!=20: raise ValueError('Incomplete selection')
    rows=[]
    for name in names:
        result=subprocess.run(command+[name,'--exact','--nocapture'],env=env,capture_output=True,text=True,timeout=30)
        log=result.stdout+result.stderr;file=name.replace('::','-')+'.log';(out/file).write_text(log)
        rows.append({'name':name,'exit_code':result.returncode,'status':classify(name,result.returncode,log,messages),'log':file,'sha256':base.sha(log.encode())})
    counts={s:sum(r['status']==s for r in rows) for s in {r['status'] for r in rows}}
    for path in ['src/lib.rs','Cargo.toml','Cargo.lock']+[str(t.relative_to(scratch)) for t in targets]:
        f=out/'inputs'/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((scratch/path).read_bytes())
    report={'mode':a.mode,'upstream_commit':base.UPSTREAM_COMMIT,'original_source_sha256':base.sha(original_source),'executed_contract_source_sha256':base.sha(source),
            'overlay_sha256':[base.sha(b) for b in overlays],'driver_sha256':base.sha(Path(__file__).read_bytes()),'base_driver_sha256':base.sha(Path(base.__file__).read_bytes()),
            'toolchain':versions,'sdk_archives':archives,'sdk_files':sdk_files,'lock':lock,'cases':rows,'counts':counts,'runtime_network':'denied by sandbox-exec',
            'duration_seconds':round(time.monotonic()-started,3),'wasm_execution_verified':False,'source_to_binary_rebuild_verified':False,'production_app_changed':False,
            'files':[{'path':str(f.relative_to(out)),'sha256':base.sha(f.read_bytes())} for f in sorted(out.rglob('*')) if f.is_file()]}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    base.require_source_state(upstream,base.UPSTREAM_COMMIT)
    expected_counts={'original':{'passed':9,'blocked_sdk_abort':10,'invalid_fixture_pass':1},'unwind':{'passed':18,'invalid_fixture_pass':2},'mutant':{'passed':14,'invalid_fixture_pass':2,'failed':4}}[a.mode]
    if counts!=expected_counts: raise RuntimeError('Unexpected results: '+str(counts))
    if a.mode=='mutant' and {r['name'] for r in rows if r['status']=='failed'}!=MUTANT_FAILURES: raise RuntimeError('Wrong mutation failures')
    print(json.dumps(counts,sort_keys=True))


if __name__=='__main__': main()
