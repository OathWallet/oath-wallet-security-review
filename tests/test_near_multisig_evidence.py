import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import near_contract_provenance as provenance
spec = importlib.util.spec_from_file_location('near_multisig_boundaries', ROOT/'scripts/near-multisig-boundaries.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class NearMultisigEvidence(unittest.TestCase):
    def setUp(self):
        self.expected = ['OathAnkrTests.NearMultisigTests/test'+str(i) for i in range(10)]
        self.rows = [{'selector': n, 'status': 'passed', 'exit_code': 0} for n in self.expected]

    def test_exact_success_receipt(self):
        driver.validate_results(self.rows, self.expected)

    def test_missing_duplicate_unexpected_failed_and_skipped_rejected(self):
        for rows in [self.rows[:-1], self.rows[:-1]+[self.rows[0]],
                     self.rows[:-1]+[dict(self.rows[-1], selector='Other/test')],
                     self.rows[:-1]+[dict(self.rows[-1], status='skipped')],
                     self.rows[:-1]+[dict(self.rows[-1], exit_code=1)]]:
            with self.assertRaises(ValueError): driver.validate_results(rows, self.expected)

    def test_copy_and_expected_digest_must_both_match(self):
        value=b'public synthetic fixture'
        expected=hashlib.sha256(value).hexdigest()
        self.assertEqual(provenance.matching_copy(value,value,expected),expected)
        for args in [(value,b'changed',expected),(value,value,'0'*64)]:
            with self.assertRaises(ValueError): provenance.matching_copy(*args)

    def test_published_evidence_hashes_and_limits(self):
        root=ROOT/'evidence/5.0.2-build104/near-multisig'
        manifest=json.loads((root/'manifest.json').read_text())
        for entry in manifest['files']:
            self.assertEqual(hashlib.sha256((root/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
        result=json.loads((root/'host/result.json').read_text())
        self.assertEqual((result['selected'],result['passed'],result['failed'],result['skipped']),(10,10,0,0))
        self.assertEqual(result['source_commit'],driver.COMMIT)
        self.assertEqual(result['script_sha256'],hashlib.sha256((ROOT/'scripts/near-multisig-boundaries.py').read_bytes()).hexdigest())
        copies=json.loads((root/'provenance.json').read_text())
        self.assertFalse(copies['source_to_binary_rebuild_verified'])
        self.assertEqual(len(copies['copies']),4)
        self.assertEqual(copies['upstream_commit'],provenance.UPSTREAM_COMMIT)
