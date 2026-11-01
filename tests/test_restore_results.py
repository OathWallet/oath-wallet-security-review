import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run

class RestoreResults(unittest.TestCase):
    def test_complete_summary_required(self):
        self.assertEqual(run.restore_case_count('Passed 140 cloud-restore integration checks (local synthetic backups; no live iCloud).\n'), 140)

    def test_empty_build_and_short_runs_fail(self):
        for value in ['', '** BUILD SUCCEEDED **', 'Passed 139 cloud-restore integration checks (local synthetic backups; no live iCloud).', 'Passed 0 cloud-restore integration checks (local synthetic backups; no live iCloud).']:
            self.assertIsNone(run.restore_case_count(value))

    def test_ambiguous_duplicate_results_fail(self):
        line = 'Passed 140 cloud-restore integration checks (local synthetic backups; no live iCloud).\n'
        self.assertIsNone(run.restore_case_count(line * 2))
