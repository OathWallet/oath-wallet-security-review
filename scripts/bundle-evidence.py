#!/usr/bin/env python3
"""Bundle completed local/CI evidence with normalized paths and checksums."""
import argparse, gzip, hashlib, json, re, tarfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('input',type=Path,nargs='+')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
manifest=[]
for base in a.input:
    for path in sorted(base.rglob('*')):
        if not path.is_file() or path.name.startswith('._') or (path.suffix not in ['.log','.json','.jsonl','.txt','.xml'] and path.name not in ['Package.resolved','TWHRP.h']): continue
        relative=Path(base.name)/path.relative_to(base)
        raw=path.read_bytes()
        text=raw.decode('utf-8',errors='replace')
        text=text.replace('/Volumes/MacOSDisk/oath-wallet-security-review','<AUDIT>')
        text=text.replace('/tmp/oath-security-fixes-20261031','<SOURCE>')
        text=re.sub(r'/Users/[^/\s]+','<HOME>',text)
        text=re.sub(r'/home/runner/work/[^/\s]+/[^/\s]+','<CI_WORKSPACE>',text)
        text=re.sub(r'/var/folders/[^/\s]+/[^/\s]+','<TEMP>',text)
        text=text.replace('\x00','<NUL>')
        data=text.encode()
        target=a.output/relative
        if path.suffix=='.log':
            target=target.with_suffix('.log.gz');data=gzip.compress(data,mtime=0)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        manifest.append({'path':str(target.relative_to(a.output)),
                         'original_sha256':hashlib.sha256(raw).hexdigest(),
                         'published_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=a.output.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as tar: tar.add(a.output,arcname=a.output.name)
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix(archive.suffix+'.sha256').write_text(f'{digest}  {archive.name}\n')
print(f'{len(manifest)} evidence files; {archive}; SHA-256 {digest}')
