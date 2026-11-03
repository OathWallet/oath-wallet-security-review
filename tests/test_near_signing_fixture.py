import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import near_signing_evidence as evidence


class NearSigningEvidenceTests(unittest.TestCase):
    def report(self, baseline=False):
        rows = [{'method': m, 'status': 'passed', 'exit_code': 0} for m in evidence.METHODS]
        if baseline:
            rows[-1].update(status='failed', exit_code=-5)
        return dict(source_commit=evidence.BASELINE if baseline else evidence.REPAIR,
                    methods=rows, transaction_vectors=72, action_vectors=10,
                    independent_signature_verification=not baseline)

    def test_before_and_after_are_distinguished(self):
        for baseline in (False, True):
            report = self.report(baseline)
            evidence.validate(report, baseline)
            with self.assertRaises(ValueError):
                evidence.validate(report, not baseline)

    def test_incomplete_duplicate_skipped_and_wrong_trap_fail(self):
        for baseline in (False, True):
            original = self.report(baseline)
            mutations = []
            for key, value in [('status', 'skipped'), ('exit_code', 1), ('method', 'different')]:
                r = copy.deepcopy(original)
                r['methods'][-1][key] = value
                mutations.append(r)
            r = copy.deepcopy(original); r['methods'].pop(); mutations.append(r)
            r = copy.deepcopy(original); r['methods'][-1] = r['methods'][0]; mutations.append(r)
            r = copy.deepcopy(original); r['transaction_vectors'] = 71; mutations.append(r)
            r = copy.deepcopy(original); r['independent_signature_verification'] = baseline; mutations.append(r)
            for r in mutations:
                with self.assertRaises(ValueError):
                    evidence.validate(r, baseline)

    def test_exact_swift_method_selection(self):
        fixture = (ROOT / 'fixtures/near-signing/NearAuditSigningTests.swift').read_text()
        for method in evidence.METHODS:
            self.assertEqual(fixture.count('func ' + method + '('), 1)

    def test_adjacent_regression_receipts_reject_missing_methods(self):
        spec = importlib.util.spec_from_file_location('near_reader', ROOT / 'scripts/near-reader-regressions.py')
        driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
        expected = ['Suite/test' + str(i) for i in range(26)]
        rows = [dict(selector=n, status='passed', exit_code=0) for n in expected]
        driver.validate_results(rows, expected)
        with self.assertRaises(ValueError):
            driver.validate_results(rows[:-1], expected)
