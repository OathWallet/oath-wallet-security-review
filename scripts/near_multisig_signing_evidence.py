"""Validate complete multisig vector coverage and exact executed test identities."""
import argparse
import hashlib
import json
from pathlib import Path
COMMIT='5d91d1e4dfd36c56031c7a8fb1ee305446dc54de'
METHODS=['testIndependentBundleBytesAndSignatures','testRestartRoundtripRetainsEveryPartAndPlan','testEverySignatureAndBundleOrderIsBound']


def validate(report):
    if report['source_commit']!=COMMIT: raise ValueError('Unexpected application commit')
    if [r['method'] for r in report['methods']]!=METHODS: raise ValueError('Missing or unexpected methods')
    if any((r['status'],r['exit_code'])!=('passed',0) for r in report['methods']): raise ValueError('Failed or skipped method')
    if (report['multisig_bundles'],report['transaction_parts'])!=(50,188): raise ValueError('Incomplete matrix')
    if report['independent_signature_verification'] is not True: raise ValueError('Signatures unverified')


def inspect(root):
    report=json.loads((root/'result.json').read_text());validate(report)
    for r in report['methods']:
        data=(root/r['log']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=r['log_sha256']:raise ValueError('Changed test log')
        identity="Test Case '-[OathAnkrTests.NearAuditMultisigTests "+r['method']+"]' started."
        if data.decode().count(identity)!=1:raise ValueError('Wrong test identity')
    data=(root/'vectors.json').read_bytes()
    if hashlib.sha256(data).hexdigest()!=report['fixture_sha256']:raise ValueError('Changed fixture')
    fixture=json.loads(data)
    expected={(r,c,b,m) for r,c in [(1,2),(2,3),(3,5),(7,10),(10,10)] for b in ['low','high'] for m in ['deploy','secure','native','token','registration']}
    actual={(v['required'],v['count'],v['boundary'],v['mode']) for v in fixture['bundles']}
    if actual!=expected or len(fixture['bundles'])!=50 or sum(len(v['parts']) for v in fixture['bundles'])!=188:raise ValueError('Wrong fixture matrix')
    if [v['id'] for v in fixture['bundles']]!=list(range(50)):raise ValueError('Duplicated bundle identity')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('evidence',type=Path);a=p.parse_args()
    inspect(a.evidence)
    print('Three methods, 50 bundles and 188 transaction parts verified')
