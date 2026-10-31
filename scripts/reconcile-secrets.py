#!/usr/bin/env python3
"""Retain raw scanner results; reconcile only existing exact, hash-bound exceptions."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('report',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();allowed=set()
for item in json.loads((a.source/'Tools/PublicFixtureReview.json').read_text())['files']:
    if not item['reason'].strip(): raise SystemExit('Missing exception reason')
    if hashlib.sha256((a.source/item['path']).read_bytes()).hexdigest()!=item['sha256']:
        raise SystemExit('Stale exception hash: '+item['path'])
    allowed.update(item['fingerprints'])
raw=json.loads(a.report.read_text());accepted=[];unknown=[]
for item in raw:
    path=item['File']
    prefix=str(a.source).rstrip('/')+'/'
    if path.startswith(prefix): path=path[len(prefix):]
    fingerprint=f"{path}:{item['RuleID']}:{item['StartLine']}"
    record={'file':path,'line':item['StartLine'],'rule':item['RuleID'],'fingerprint':fingerprint}
    (accepted if fingerprint in allowed else unknown).append(record)
result={'raw_count':len(raw),'existing_hash_bound_exception_count':len(accepted),
        'unreconciled_count':len(unknown),'unreconciled':unknown,
        'exception_authority':'Application Tools/PublicFixtureReview.json; not an independent secret review',
        'report_sha256':hashlib.sha256(a.report.read_bytes()).hexdigest()}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
raise SystemExit(1 if unknown else 0)
