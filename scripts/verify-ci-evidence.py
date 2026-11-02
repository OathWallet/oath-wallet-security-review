#!/usr/bin/env python3
"""Verify the durable CI evidence download against the source-controlled manifest."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(manifest, archive):
    evidence = json.loads(manifest.read_bytes())
    if digest(archive.read_bytes()) != evidence['published_bundle_sha256']:
        raise ValueError('Published archive digest mismatch')
    receipts = {a['id']: a for a in evidence['archive_receipts']}
    with ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive member')
        for row in evidence['records']:
            receipt = receipts[row['artifact_id']]
            if receipt['digest'] != 'sha256:'+row['original_archive_sha256']:
                raise ValueError('Wrong source archive receipt')
            if not all(row[k].startswith(receipt['name']+'/') for k in ('report','log')):
                raise ValueError('Report or log belongs to a different artifact')
            body = bundle.read(row['report'])
            if digest(body) != row['report_sha256'] or digest(bundle.read(row['log'])) != row['log_sha256']:
                raise ValueError('Changed evidence: '+row['report'])
            report = json.loads(body)
            if any(report[k] != row[k] for k in ('source_commit','check','status','log_sha256')):
                raise ValueError('Report metadata mismatch')
    return len(evidence['records'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('archive',type=Path)
    args = parser.parse_args()
    print('Verified', verify(args.manifest,args.archive), 'result/log pairs')
