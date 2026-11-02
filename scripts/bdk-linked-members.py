#!/usr/bin/env python3
"""Replay the actual framework linker invocation in isolation to obtain its selected static members."""
import argparse,hashlib,importlib.util,json,os,re,subprocess,tempfile
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for k in ('derived','inputs','frameworks','output'):p.add_argument(k,type=Path)
    a=p.parse_args();d=a.derived.resolve();i=json.loads(a.inputs.read_bytes());f=json.loads(a.frameworks.read_bytes())
    if i['source_commit']!=f['source_commit'] or i['build_log_sha256']!=f['build_log_sha256'] or i['status']!=f['status'] or i['status']!='passed':raise ValueError('Build identity mismatch')
    m=(d/'Build/Intermediates.noindex/XCBuildData'/(i['build_description']+'.xcbuilddata')/'manifest.json').read_bytes()
    if sha(m)!=i['manifest_sha256']:raise ValueError('Manifest differs from traced build')
    command,=[x for k,x in json.loads(m)['commands'].items() if 'Ld ' in k and 'OathBitcoin.framework/OathBitcoin normal' in k]
    args=list(command['args']);outputs=[Path(x) for x in command['outputs'] if not x.startswith('<')]
    if Path(args[0]).resolve()!=Path(subprocess.check_output(['xcrun','--find','swiftc'],text=True).strip()).resolve() or len(outputs)!=3:
        raise ValueError('Unexpected framework linker configuration')
    assert '-emit-library' in args and '-dead_strip' in args and '-lbdkffi' in args and all(x.resolve().is_relative_to(d/'Build') for x in outputs)
    spec=importlib.util.spec_from_file_location('framework',Path(__file__).with_name('release-frameworks.py'));framework=importlib.util.module_from_spec(spec);spec.loader.exec_module(framework)
    with tempfile.TemporaryDirectory(prefix='oath-link-map-') as t:
        tmp=Path(t)
        for x in outputs:
            assert args.count(str(x))==1
            args[args.index(str(x))]=str(tmp/x.name)
        result=tmp/'link.map'
        subprocess.run(args+['-Xlinker','-map','-Xlinker',str(result)],check=True,cwd=command['working-directory'],env={'PATH':command['env']['PATH'],'TMPDIR':str(tmp)})
        replay=framework.inspect(tmp/'OathBitcoin');actual=f['embedded']['OathBitcoin']
        if replay['uuid']!=actual['uuid'] or replay['executable_sections']!=actual['executable_sections']:raise ValueError('Relinked instruction sections differ from embedded image')
        raw=result.read_bytes();objects=raw.split(b'# Sections:')[0];live=raw.split(b'# Symbols:')[1].split(b'# Dead Stripped Symbols:')[0]
        members={int(idx):name.decode() for idx,name in re.findall(rb'^\[\s*(\d+)\].*?libbdkffi\.a\(([^)]+)\)$',objects,re.M)}
        # The copied XCFramework input can have a different path from the
        # packaged slice. Hash the archive actually named by the linker.
        archive_paths={Path(p.decode()).resolve() for p in re.findall(rb'^\[\s*\d+\]\s+(.+?/libbdkffi\.a)\([^)]*\)$',objects,re.M)}
        archive,=archive_paths
        if not archive.is_relative_to(d) or not archive.is_file():
            raise ValueError('Link map referenced an unexpected BDK archive')
        with archive.open('rb') as stream:archive_digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if archive_digest!='b5106bc00a27ee1b4fc828c8be21c56224557ab4f163d6c11fb0d71f3a6bf8ec':
            raise ValueError('Actually linked BDK library differs from the verified distribution')
        target,=[idx for idx,n in members.items() if n.startswith('uniffi_testing-')]
        sym=rb'__ZN14uniffi_testing24get_cargo_build_messages17he9666a7cefeebc81E'
        addr,length=re.findall(rb'^0x([0-9A-F]+)\s+0x([0-9A-F]+)\s+\[\s*'+str(target).encode()+rb'\] '+sym+rb'$',live,re.M)[0]
        r=dict(check='bdk-linked-members',status='passed',source_commit=i['source_commit'],manifest_sha256=sha(m),replay_uuid=replay['uuid'],same_uuid=True,
            matching_executable_sections=actual['executable_sections'],whole_file_identical=replay['sha256']==actual['sha256'],replay_sha256=replay['sha256'],original_embedded_sha256=actual['sha256'],
            linked_archive_sha256=archive_digest,linked_archive_bytes=archive.stat().st_size,selected_bdk_members=sorted(members.values()),member_count=len(members),cargo_function=dict(member=members[target],address=int(addr,16),bytes=int(length,16)),
            scope='Replay changed only declared linker output paths and requested a link map. All instruction-bearing sections and the UUID matched the embedded framework. Listed members were selected at link; live-symbol presence does not prove invocation.')
    a.output.mkdir(parents=True,exist_ok=True);log=a.output/'bdk-linked-members.log';log.write_text(json.dumps(r,indent=2)+'\n')
    r.update(log=log.name,log_sha256=sha(log.read_bytes()));(a.output/'bdk-linked-members.json').write_text(json.dumps(r,indent=2)+'\n');print(r['member_count'],'archive members selected, function is present')
if __name__=='__main__':main()
