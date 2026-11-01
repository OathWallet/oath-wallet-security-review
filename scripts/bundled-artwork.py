#!/usr/bin/env python3
"""Verify file/reference integrity separately from visual identity or issuer provenance."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
CATALOG='OathApp/Assets.xcassets/'
RECEIVE='OathApp/Resources/ReceiveAssets.json'

def unique(items):
    out={}
    for k,v in items:
        if k in out: raise ValueError('Duplicate JSON key: '+k)
        out[k]=v
    return out

def parse(source,filename):
    return json.loads((source/filename).read_text(),object_pairs_hook=unique)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-commit')
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    pin=require_source_state(source,a.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    names=sorted(filter(None,subprocess.check_output(['git','-C',source,'ls-files','-z','--',CATALOG]).decode().split('\0')))
    known=set(names);rows={};owners={};sets=set()
    for name in names:
        path=source/name
        if path.is_symlink() or not path.is_file(): raise ValueError('Unexpected asset type: '+name)
        rows[name]={'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.name!='Contents.json': continue
        doc=parse(source,name)
        if set(doc)-{'images','info','properties'} or doc['info'].get('version')!=1: raise ValueError('Unknown schema: '+name)
        for image in doc.get('images',[]):
            asset=image['filename']
            if PurePosixPath(asset).name!=asset or asset in {'.','..'}: raise ValueError('Invalid asset path: '+name)
            child=str(Path(name).parent/asset)
            if child not in known: raise ValueError('Missing target: '+child)
            owners.setdefault(child,set()).add(name)
        if name.startswith(CATALOG+'ReceiveAssets/') and path.parent.suffix=='.imageset': sets.add(path.parent.stem)
    properties=parse(source,RECEIVE)['networks'];ids=set();references=set()
    for chain,examples in properties.items():
        for example in examples:
            identity=example['id'];art=example['artwork']
            if identity in ids or not identity.startswith(chain+':') or not identity[len(chain)+1:] or art not in sets:
                raise ValueError('Duplicate, mismatched or dangling token identity: '+identity)
            ids.add(identity);references.add(art)
    if references!=sets: raise ValueError('Unreferenced ReceiveAssets image set')
    rasters=[name for name in names if name.endswith(('.png','.jpg'))]
    probe=ROOT/'fixtures/artwork/InspectBundledRaster.swift'
    output=subprocess.check_output(['swift',str(probe),str(source)],input=json.dumps(rasters).encode())
    decoded=json.loads(output)
    if [v['path'] for v in decoded]!=rasters: raise ValueError('Incomplete image decode')
    for v in decoded:rows[v['path']].update(v)
    for name,row in rows.items():
        if name in owners:row['declared_by']=sorted(owners[name])
        elif not name.endswith('Contents.json'):row['declared_by']=[]
    evidence={'source_commit':pin,'files':list(rows.values()),'receive_catalog_sha256':hashlib.sha256((source/RECEIVE).read_bytes()).hexdigest(),
              'receive_rows':len(ids),'receive_networks':len(properties),'receive_imagesets':len(sets),'declared_assets':len(owners),
              'rasters_decoded':len(decoded),'manifests':sum(n.endswith('Contents.json') for n in names),
              'files_without_manifest_reference':[n for n in names if not n.endswith('Contents.json') and n not in owners]}
    require_source_state(source,pin)
    (out/'asset-coverage.json').write_text(json.dumps(evidence,indent=2)+'\n')
    log=out/'bundled-artwork.log'
    log.write_text(f"Checked {len(rows)} tracked catalog files, {len(owners)} distinct declared assets, {len(decoded)} raster decodes, and {len(ids)} unique source IDs across {len(properties)} network groups.\n")
    (out/'bundled-artwork.json').write_text(json.dumps({'check':'bundled-artwork','status':'passed','source_commit':pin,'log':log.name,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()},indent=2)+'\n')
    print(log.read_text(),end='')

if __name__=='__main__': main()
