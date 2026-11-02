#!/usr/bin/env python3
"""Attribute native archive objects to Clang's actual translation units and headers."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import shlex
import subprocess
import tarfile
import tomllib

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_hash(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('bridge','cargo_home','scratch','reference','output'):
        p.add_argument(k,type=Path)
    p.add_argument('--linked-members',type=Path,help='Verified app link-map evidence for the distributed archive')
    a=p.parse_args();bridge=a.bridge.resolve();work=a.scratch.resolve();target=work/'target'
    cargo=a.cargo_home.resolve();registry,=(cargo/'registry/src').glob('index.crates.io-*')
    lock=bridge/'Cargo.lock'
    if file_hash(lock)!='a7b22b8c0669d16ad11a3ea7af0c78f22185a91bd9c20ba59ecfd23468d4d9b9':
        raise ValueError('Unexpected Cargo inputs')
    pins={f"{i['name']}-{i['version']}":i['checksum'] for i in tomllib.loads(lock.read_text())['package'] if 'checksum' in i}
    compiler=Path(subprocess.check_output(['xcrun','--find','clang'],text=True).strip())
    sdk=Path(subprocess.check_output(['xcrun','--sdk','iphoneos','--show-sdk-path'],text=True).strip()).resolve()
    resource=Path(subprocess.check_output([compiler,'-print-resource-dir'],text=True).strip()).resolve()
    deps={};hashed={};files={}
    def classify(path):
        if path in hashed:return hashed[path]
        if path.is_relative_to(registry):
            item=path.relative_to(registry);crate=item.parts[0];key=item.as_posix()
            if crate not in deps:
                archive,=(cargo/'registry/cache').glob('*/'+crate+'.crate')
                if file_hash(archive)!=pins[crate]:raise ValueError('Cargo checksum differs for '+crate)
                with tarfile.open(archive,'r:gz') as t:
                    dep={}
                    for member in t:
                        if not member.isfile():continue
                        if member.name in dep:raise ValueError('Duplicate registry file')
                        with t.extractfile(member) as f:dep[member.name]=hashlib.file_digest(f,'sha256').hexdigest()
                    deps[crate]=dep
            expected=deps[crate][key];role='registry'
        elif path.is_relative_to(target):
            key='<build>/'+path.relative_to(target).as_posix();role='generated';expected=None
        elif path.is_relative_to(sdk):
            key='<iphoneos-sdk>/'+path.relative_to(sdk).as_posix();role='system-sdk';expected=None
        elif path.is_relative_to(resource):
            key='<clang-resource>/'+path.relative_to(resource).as_posix();role='compiler-resource';expected=None
        else:
            raise ValueError('Unclassified source path: '+str(path))
        digest=file_hash(path)
        if expected is not None and expected!=digest:raise ValueError('Compiled input differs from archive: '+key)
        files[key]=dict(path=key,sha256=digest,role=role,bytes=path.stat().st_size)
        hashed[path]=key;return key
    tool=runpy.run_path(str(Path(__file__).with_name('compare-bdk-archives.py')))
    def objects(path):
        pairs=list(tool['payloads'](path.read_bytes()))
        result={n:sha(obj) for n,obj in pairs}
        if len(pairs)!=len(result):raise ValueError('Repeated object name: '+path.name)
        return result
    archives=[];finished=False
    for s in (work/'messages.jsonl').read_text().splitlines():
        r=json.loads(s)
        if r['reason']=='build-finished':finished=r['success']
        if r['reason']!='build-script-executed':continue
        out=Path(r['out_dir']).resolve()
        if not out.is_relative_to(target/'aarch64-apple-ios'):continue
        for lib in r['linked_libs']:
            if not lib.startswith('static='):raise ValueError('Unexpected native link request: '+lib)
            archives.append((out/('lib'+lib[7:]+'.a'),r['package_id'].split('#')[-1]))
    if not finished or len(archives)!=5:raise ValueError('Incomplete BDK native link requests')
    def read_actions():
        rows={}
        for action in sorted((work/'trace').glob('*/action.json')):
            r=json.loads(action.read_bytes());obj=Path(r['object']).resolve()
            if not obj.is_relative_to(target):raise ValueError('Foreign object')
            headers=action.parent/'headers.d'
            if file_hash(headers)!=r['dependency_file_sha256']:raise ValueError('Changed include trace')
            # Ignore compiler flag probes. Results are attributed only when the
            # object's bytes survive into one of the final five native archives.
            key=(obj,r['object_sha256']);rows.setdefault(key,[]).append((r,headers))
        return rows
    actions=read_actions();used=set();records=[];libs=[]
    library='aarch64-apple-ios/release-smaller/libbdkffi.a'
    final=objects(target/library);published=objects(a.reference)
    selected=set()
    if a.linked_members:
        if file_hash(a.reference)!='b5106bc00a27ee1b4fc828c8be21c56224557ab4f163d6c11fb0d71f3a6bf8ec':
            raise ValueError('The link map belongs to the distributed archive')
        link=json.loads(a.linked_members.read_bytes())
        if link.get('check')!='bdk-linked-members' or not link.get('same_uuid') or link['status']!='passed':
            raise ValueError('Unverified link map')
        selected=set(link['selected_bdk_members'])
    for archive,crate in sorted(archives):
        objs=objects(archive);libs.append(dict(archive=archive.name,crate=crate,members=len(objs),sha256=file_hash(archive)))
        for name,digest in sorted(objs.items()):
            key=(archive.parent/name,digest)
            if key not in actions:raise ValueError('No compiler action with matching object bytes: '+name)
            if key in used:raise ValueError('Object reused between archives')
            used.add(key);translated=set()
            for action,headers in actions[key]:
                cwd=Path(action['cwd']);unit,=[(cwd/v).resolve() for v in action['argv'] if Path(v).suffix.lower() in {'.s','.c','.cc','.cpp','.cxx'} and (cwd/v).is_file()]
                rule=headers.read_text().replace('\\\n',' ');target_path,body=rule.split(': ',1)
                targets=shlex.split(target_path)
                if len(targets)!=1 or (cwd/targets[0]).resolve()!=key[0]:raise ValueError('Unexpected dependency target')
                paths={(cwd/v).resolve() for v in shlex.split(body)}
                if unit not in paths:raise ValueError('Missing unit in compiler-generated header list')
                translated.add((classify(unit),tuple(sorted(classify(f) for f in paths))))
            if len(translated)!=1:raise ValueError('Ambiguous compiler/source mapping: '+name)
            unit,inputs=translated.pop();included=final.get(name)==digest;equal=published.get(name)==digest
            records.append(dict(crate=crate,object=name,sha256=digest,source=unit,inputs=inputs,in_rebuilt_bridge=included,
                                same_name_and_bytes_in_reference=equal,selected_in_reference_app=equal and name in selected if a.linked_members else None))
    result=dict(reference_sha256=file_hash(a.reference),rebuilt_archive_sha256=file_hash(target/library),lock_sha256=file_hash(lock),
        compiler_version=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0],sdk=sdk.name,
        registry_archives={k:pins[k] for k in sorted(deps)},libraries=libs,files=[files[k] for k in sorted(files)],objects=records,
        object_action_pairs=len(actions),non_archive_action_pairs=len(actions)-len(used),source_role_counts=dict(Counter(v['role'] for v in files.values())),
        source_scope='Clang dependency files from target compile invocations. Each object is matched by full bytes inside a Cargo-requested native archive. System headers, compiler resources and generated inputs remain distinct. Listed inputs are not a claim of manual review or runtime execution.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(len(records),'native members;',len(files),'inputs;',sum(r['in_rebuilt_bridge'] for r in records),'in rebuilt bridge;',
          sum(r['same_name_and_bytes_in_reference'] for r in records),'with matching reference name and bytes')

if __name__=='__main__':main()
