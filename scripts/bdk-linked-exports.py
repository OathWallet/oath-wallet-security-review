#!/usr/bin/env python3
"""Bind the published BDK UniFFI name inventory to the generic iOS app's actual dyld export tries."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
def marked_names(lines):
    names=set()
    for line in lines:
        if re.search(r'\b_(?:uniffi_bdkffi_|ffi_bdkffi_)',line):
            m=re.fullmatch(r'\s*0x[0-9A-Fa-f]+\s+(_(?:uniffi_bdkffi_|ffi_bdkffi_)\w+)\s*',line)
            if not m:raise ValueError('Unexpected marked dyld export format')
            names.add(m[1])
    return names
def main():
    parser=argparse.ArgumentParser()
    for n in ('app','framework_result','archive_comparison','output'):parser.add_argument(n,type=Path)
    args=parser.parse_args()
    fr=json.loads(args.framework_result.read_bytes());cmp=json.loads(args.archive_comparison.read_bytes())
    if fr['check']!='release-frameworks' or fr['status']!='passed' or cmp['published']['sha256']!='b5106bc00a27ee1b4fc828c8be21c56224557ab4f163d6c11fb0d71f3a6bf8ec':raise ValueError('Wrong evidence identity')
    expected=set(cmp['published']['uniffi_exports']);images={};allnames=set()
    for name,meta in fr['embedded'].items():
        path=args.app/name if (args.app/name).is_file() else args.app/'Frameworks'/(name+'.framework')/name
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=meta['sha256']:raise ValueError('Product hash mismatch: '+name)
        with subprocess.Popen(['xcrun','dyld_info','-exports',path],stdout=subprocess.PIPE,text=True) as proc:
            names=marked_names(proc.stdout)
            if proc.wait():raise ValueError('dyld inspection failed')
        images[name]=dict(image_sha256=digest,bdk_exports=sorted(names));allnames|=names
    result=dict(source_commit=fr['source_commit'],check='bdk-linked-exports',status='passed' if expected==allnames and len(expected)==906 else 'failed',
        images=images,missing=sorted(expected-allnames),extra=sorted(allnames-expected),
        scope='Case-sensitive names in each embedded Mach-O dynamic export trie compared with public UniFFI names in the pinned archive. Export presence does not establish call reachability, signature correctness or byte-identical implementations.')
    args.output.mkdir(parents=True,exist_ok=True)
    log=args.output/'bdk-linked-exports.log';log.write_text(json.dumps(result,indent=2)+'\n')
    result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());(args.output/'bdk-linked-exports.json').write_text(json.dumps(result,indent=2)+'\n')
    print('BDK exports by image:',{k:len(v['bdk_exports']) for k,v in images.items()});return int(result['status']!='passed')
if __name__=='__main__':raise SystemExit(main())
