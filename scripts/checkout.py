#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[1]
config = json.loads((root/'scope/source.json').read_text())
source = root/'.work/source'
if source.exists():
    current = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if current != config['reviewed_commit']:
        raise SystemExit('Existing checkout differs; preserve it and use a fresh workspace.')
else:
    source.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','clone','--no-checkout',config['repository'],str(source)],check=True)
    subprocess.run(['git','-C',str(source),'checkout','--detach',config['reviewed_commit']],check=True)
print('Pinned source ready:',config['reviewed_commit'])
