import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('near_journal_boundaries', SCRIPTS / 'near-journal-boundaries.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class NearJournalEvidence(unittest.TestCase):
    def setUp(self):
        self.expected = ['OathDatabaseTests.WalletConnectNearJournalTests/test' + str(i) for i in range(8)]
        self.rows = [{'selector': n, 'status': 'passed', 'exit_code': 0} for n in self.expected]

    def test_exact_success_receipt(self):
        driver.validate_results(self.rows, self.expected)

    def test_missing_duplicate_and_unexpected_cases_fail(self):
        for rows in [self.rows[:-1], self.rows[:-1] + [self.rows[0]],
                     self.rows[:-1] + [dict(self.rows[-1], selector='Other/test')]]:
            with self.assertRaises(ValueError):
                driver.validate_results(rows, self.expected)

    def test_skip_failure_and_process_error_fail(self):
        for changes in [{'status': 'skipped'}, {'status': 'failed'}, {'exit_code': 1}]:
            with self.assertRaises(ValueError):
                driver.validate_results(self.rows[:-1] + [dict(self.rows[-1], **changes)], self.expected)

    def test_published_replay_files_and_source_are_bound(self):
        root = SCRIPTS.parent
        evidence = root / 'evidence/5.0.2-build104/near-journal-boundaries'
        manifest = json.loads((evidence / 'manifest.json').read_text())
        for item in manifest['files']:
            data = (evidence / item['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])
        result = json.loads((evidence / manifest['replay']).read_text())
        self.assertEqual(result['source_commit'], driver.COMMIT)
        self.assertEqual(result['script_sha256'], hashlib.sha256((SCRIPTS / 'near-journal-boundaries.py').read_bytes()).hexdigest())
        self.assertEqual((result['selected'], result['passed'], result['skipped'], result['failed']), (8, 8, 0, 0))
        dispositions = json.loads((root / 'review/dispositions.json').read_text())
        binding = json.loads((evidence / 'source-binding.json').read_text())
        self.assertEqual(len(binding['files']), 4)
        for item in binding['files']:
            self.assertEqual(dispositions[item['path']]['sha256'], item['sha256'])
            self.assertEqual(dispositions[item['path']]['status'], 'partially-reviewed')
