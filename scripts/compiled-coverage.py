#!/usr/bin/env python3
"""Join direct Release compiler inputs to exact-hash review dispositions without promoting coverage."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CLOSED={'reviewed','non-security-content','generated-verified'}

def join(inputs, app, packages, artwork):
    if inputs.get('check')!='release-inputs' or inputs.get('status')!='passed' or inputs['source_commit']!=app['source_commit']:
        raise ValueError('Need a successful matching compiler trace')
    ledger={}
    for prefix,source in [('application/',app),('package/',packages),('package/SwiftDraw/',artwork)]:
        for row in source['files']:
            path=prefix+row['path']
            if path in ledger:
                raise ValueError('Ambiguous inventory path')
            ledger[path]=row
    results=[]
    seen=set()
    for source in inputs['files']:
        path=source['path']
        if path in seen:raise ValueError('Repeated compiler input')
        seen.add(path)
        disposition=ledger.get(path)
        if disposition is None:
            if not path.startswith('generated/'):
                raise ValueError('Missing ledger entry: '+path)
            status='generated-input-needs-trace'
        else:
            if disposition['sha256']!=source['sha256']:
                raise ValueError('Stale review disposition for '+path)
            status=disposition['status']
        results.append(dict(source,review_status=status,
                            evidence=list(disposition.get('evidence', [])) if disposition else [],
                            additional_review=status not in CLOSED))
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    trace=json.loads(args.trace.read_bytes())
    if hashlib.sha256((args.trace.parent/trace['log']).read_bytes()).hexdigest()!=trace['log_sha256']:
        raise ValueError('Compiler trace log digest mismatch')
    ledgers=[json.loads((ROOT/'scope'/name).read_bytes()) for name in ('inventory.json','upstream-xcode-packages.json','upstream-swiftdraw.json')]
    rows=join(trace,*ledgers)
    counts=Counter(row['review_status'] for row in rows)
    open_targets=Counter(t for row in rows if row['additional_review'] for t in row['targets'])
    output=dict(source_commit=trace['source_commit'],trace_manifest_sha256=hashlib.sha256(args.trace.read_bytes()).hexdigest(),input_count=len(rows),status_counts=dict(counts),
                open_input_counts_by_target=dict(open_targets.most_common()),files=rows,
                scope='Direct source and header inputs of the selected unsigned iOS build. Excludes prebuilt libraries, runtime-loaded assets and build tools. No review status is changed by this join.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print('Compiled input coverage:',dict(counts))

if __name__=='__main__':
    main()
