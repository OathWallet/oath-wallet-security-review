import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run import SCANNER_MODES, scanner_case_count

class ScannerResultsTests(unittest.TestCase):
    def test_only_offline_modes_are_exposed(self):
        self.assertEqual(SCANNER_MODES, {'scanner': [], 'wallet-links': ['--links'], 'scanner-lifecycle': ['--performance']})

    def test_actual_summary(self):
        self.assertEqual(scanner_case_count('scanner', 'Passed 13635 scanner checks; 715 real CoreImage/Vision QR round trips; 42 chains; remaining scope\n'), 13635)
        self.assertEqual(scanner_case_count('wallet-links', 'Wallet link checks passed: 100\n'), 100)
        self.assertEqual(scanner_case_count('scanner-lifecycle', 'Scanner concurrency/lifecycle: 2018 checks passed\n'), 2018)

    def test_compile_empty_or_duplicate_summary_is_not_a_test_pass(self):
        for text in ['', 'Build complete!', 'Wallet link checks passed: 0', 'Wallet link checks passed: 1\nWallet link checks passed: 1']:
            self.assertIsNone(scanner_case_count('wallet-links', text))
        self.assertIsNone(scanner_case_count('scanner', 'Passed 10 scanner checks; 0 real CoreImage/Vision QR round trips; 42 chains;'))
