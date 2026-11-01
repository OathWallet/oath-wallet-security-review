#!/usr/bin/env python3
"""Inventory the exact upstream files used by the pinned SwiftDraw dependency review."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN='82699f4bdf2f075793cfa0d392eb27c59b41a3fe'
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('checkout',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.checkout
    if subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()!=PIN: raise ValueError('Unexpected SwiftDraw revision')
    entries=subprocess.check_output(['git','-C',root,'ls-tree','-r','-z',PIN]).decode().split('\0')
    decisions={'Package.swift':'reviewed','DOM/Sources/DOM.Use.swift':'reviewed',
               'SwiftDraw/Sources/LayerTree/LayerTree.Builder.swift':'partially-reviewed',
               'SwiftDraw/Sources/LayerTree/LayerTree.Builder.Layer.swift':'partially-reviewed'}
    rows=[]
    for entry in filter(None,entries):
        meta,name=entry.split('\t',1);mode,kind,oid=meta.split()
        if kind!='blob': raise ValueError('Unexpected non-blob entry '+name)
        data=subprocess.check_output(['git','-C',root,'cat-file','blob',oid])
        row=dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),mode=mode,
                 library_target_source=name.startswith(('SwiftDraw/Sources/','DOM/Sources/')),
                 status=decisions.get(name,'outstanding'))
        if name in decisions: row['evidence']=['review/TOKEN-ARTWORK.md']
        rows.append(row)
    if set(decisions)-{r['path'] for r in rows}: raise ValueError('Missing reviewed input')
    a.output.write_text(json.dumps(dict(repository='https://github.com/swhitty/SwiftDraw',commit=PIN,tag='0.29.0',
        scope_note='Tracks all upstream blobs, including development/test inputs. Library-target membership follows Package.swift. No reachability or source-to-binary claim for an outstanding file.',files=rows),indent=2)+'\n')

if __name__=='__main__': main()
