import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PrivacyCoverEvidenceTests(unittest.TestCase):
    def test_archived_capture_and_fixture_hashes(self):
        root = ROOT / 'evidence/5.0.1-build103/privacy-cover'
        receipt = json.loads((root / 'result.json').read_text())
        for name, expected in receipt['files'].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected)
        for name, expected in receipt['fixtures'].items():
            with self.subTest(fixture=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_positive_control_and_limited_ocr_claim(self):
        root = ROOT / 'evidence/5.0.1-build103/privacy-cover'
        ocr = json.loads((root / 'ocr.json').read_text())
        self.assertEqual(len(ocr['uncovered']), 10)
        self.assertTrue(any('fixture' in item['text'] for item in ocr['uncovered']))
        self.assertEqual(ocr['covered-light'], [])
        self.assertEqual(ocr['covered-dark'], [])
        # No claim that the status bar or every pixel is hidden.
        self.assertEqual(len(ocr['compositor-dark']), 2)

    def test_runtime_is_explicitly_opt_in(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/privacy-cover-probe.py'),
             '/nonexistent-source', '/nonexistent-output'],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('requires explicit --run-simulator', result.stderr)
        self.assertNotIn('Wrong source revision', result.stderr)


if __name__ == '__main__':
    unittest.main()
