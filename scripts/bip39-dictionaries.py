#!/usr/bin/env python3
"""Verify the ten ordered word lists in the actual unsigned iOS Release product against Bitcoin BIPs."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unicodedata
from source_state import require_source_state

REV='927b6de9915c9262615a6399de51b200f81e5aa4'
LANGUAGES=('english','japanese','korean','spanish','chinese_simplified','chinese_traditional','french','italian','czech','portuguese')
def sha(data):return hashlib.sha256(data).hexdigest()

def check(source,app,upstream):
    base=source/'OathApp/Resources/BIP39';manifest=base/'bip39_manifest.json'
    actual=json.loads(manifest.read_bytes())
    if actual['commit']!=REV or tuple(r['id'] for r in actual['lists'])!=LANGUAGES or manifest.read_bytes()!=(app/manifest.name).read_bytes():
        raise ValueError('Wrong dictionary manifest in source or product')
    results=[]
    for row in actual['lists']:
        lang=row['id'];path='bip-0039/'+lang+'.txt';name='bip39_'+lang+'.txt'
        if row['source']!='https://raw.githubusercontent.com/bitcoin/bips/'+REV+'/'+path:
            raise ValueError('Unexpected upstream dictionary identity')
        content=subprocess.check_output(['git','-C',upstream,'show',REV+':'+path])
        if content!=(base/name).read_bytes() or content!=(app/name).read_bytes() or sha(content)!=row['sha256']:
            raise ValueError('Ordered dictionary differs: '+lang)
        words=content.decode('utf-8').splitlines()
        if not (len(words)==len(set(words))==row['count']==2048 and all(w and unicodedata.normalize('NFKD',w)==w and not any(c.isspace() for c in w) for w in words)):
            raise ValueError('Invalid dictionary semantics: '+lang)
        results.append(dict(language=lang,upstream_blob=subprocess.check_output(['git','-C',upstream,'rev-parse',REV+':'+path],text=True).strip(),sha256=sha(content),words=len(words)))
    return results,sha(manifest.read_bytes())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','app','framework_result','output'):p.add_argument(name,type=Path)
    a=p.parse_args();framework=json.loads(a.framework_result.read_bytes());pin=require_source_state(a.source,framework['source_commit'])
    binary=plistlib.loads((a.app/'Info.plist').read_bytes())['CFBundleExecutable']
    binary_hash=sha((a.app/binary).read_bytes())
    if framework['status']!='passed' or binary_hash!=framework['embedded'][binary]['sha256']:
        raise ValueError('Release product identity mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['git','init','-q',tmp],check=True)
        subprocess.run(['git','-C',tmp,'fetch','--quiet','--depth=1','https://github.com/bitcoin/bips.git',REV],check=True)
        rows,mhash=check(a.source,a.app,tmp)
    out=dict(check='bip39-dictionaries',source_commit=pin,status='passed',app_binary_sha256=binary_hash,upstream_revision=REV,manifest_sha256=mhash,
             dictionaries=rows,scope='All bytes, order, counts, uniqueness and Unicode NFKD representation in Git and the traced unsigned iOS bundle against the pinned upstream files.')
    a.output.mkdir(parents=True,exist_ok=True);log=a.output/'bip39-dictionaries.log';log.write_text(json.dumps(out,indent=2)+'\n')
    out.update(log=log.name,log_sha256=sha(log.read_bytes()));(a.output/'bip39-dictionaries.json').write_text(json.dumps(out,indent=2)+'\n')
    print(len(rows),'dictionaries and',sum(x['words'] for x in rows),'ordered entries verified')
if __name__=='__main__':main()
