#!/usr/bin/env python3
"""Prove the independent verifier rejects changed, missing and reordered signatures."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('evidence',type=Path);a=p.parse_args();root=a.evidence.resolve()
    original=json.loads((root/'application-signatures.json').read_text());cases=[]
    missing=copy.deepcopy(original);missing.pop();cases.append(('missing-bundle',missing,'Incomplete bundle results'))
    order=copy.deepcopy(original);order[0],order[1]=order[1],order[0];cases.append(('bundle-order',order,'Missing or reordered bundle'))
    part=copy.deepcopy(original);part[0]['parts'].pop();cases.append(('missing-part',part,'Missing or reordered bundle'))
    for name,index,expected in [('changed-raw',0,'Changed transaction bytes'),('changed-signature',-1,'Invalid production signature')]:
        value=copy.deepcopy(original);raw=bytearray(base64.b64decode(value[0]['parts'][0]));raw[index]^=1;value[0]['parts'][0]=base64.b64encode(raw).decode();cases.append((name,value,expected))
    verifier=ROOT/'fixtures/near-multisig-signing/verify.mjs';results=[]
    with tempfile.TemporaryDirectory(prefix='oath-near-negative-') as temporary:
        for name,value,expected in cases:
            fixture=Path(temporary)/(name+'.json');fixture.write_text(json.dumps(value))
            r=subprocess.run(['node',str(verifier),str(root/'vectors.json'),str(fixture)],capture_output=True,timeout=30)
            data=r.stdout+r.stderr;log=root/(name+'.log');log.write_bytes(data)
            if r.returncode!=1 or ('Error: '+expected) not in data.decode():raise ValueError('Unexpected negative-control outcome: '+name)
            results.append({'name':name,'expected_error':expected,'exit_code':r.returncode,'log':log.name,'log_sha256':hashlib.sha256(data).hexdigest()})
    (root/'verifier-controls.json').write_text(json.dumps({'controls':results,'verifier_sha256':hashlib.sha256(verifier.read_bytes()).hexdigest()},indent=2)+'\n')
    print('Five altered-output controls rejected with their expected errors')
if __name__=='__main__':main()
