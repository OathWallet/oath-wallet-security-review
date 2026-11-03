"""Validate exact NEAR vector outcomes, including the deliberately failing baseline."""
import argparse
import hashlib
import json
from pathlib import Path

BASELINE = '0614556b993f85808b13e3a69984ce36050a8dfe'
REPAIR = '5d91d1e4dfd36c56031c7a8fb1ee305446dc54de'
METHODS = [
    'testIndependentPlanBytesHashesAndSignatures',
    'testIndependentActionsAndProductionSignatures',
    'testChangedPlansAndTamperedSignaturesAreRejected',
    'testTruncatedAndTrailingActionBytesAreRejected',
    'testNonzeroOriginDataSliceMatchesBytes',
]


def validate(report, baseline=False):
    if report['source_commit'] != (BASELINE if baseline else REPAIR):
        raise ValueError('Unexpected application commit')
    if [r['method'] for r in report['methods']] != METHODS:
        raise ValueError('Incomplete, duplicated or unexpected method identities')
    for i, row in enumerate(report['methods']):
        expected = ('failed', -5) if baseline and i == 4 else ('passed', 0)
        if (row['status'], row['exit_code']) != expected:
            raise ValueError('Unexpected method outcome')
    if (report['transaction_vectors'], report['action_vectors']) != (72, 10):
        raise ValueError('Unexpected vector coverage')
    if report['independent_signature_verification'] is not (not baseline):
        raise ValueError('Unexpected independent verification status')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evidence', type=Path)
    p.add_argument('--baseline', action='store_true')
    a = p.parse_args()
    report = json.loads((a.evidence / 'result.json').read_text())
    validate(report, a.baseline)
    for row in report['methods']:
        data = (a.evidence / row['log']).read_bytes()
        if hashlib.sha256(data).hexdigest() != row['log_sha256']:
            raise ValueError('Method log digest mismatch')
        identity = '-[OathAnkrTests.NearAuditSigningTests ' + row['method'] + ']'
        if data.decode().count("Test Case '" + identity + "' started.") != 1:
            raise ValueError('Log does not identify the expected method')
    print('Expected baseline trap verified' if a.baseline else 'Repaired vector results verified')


if __name__ == '__main__':
    main()
