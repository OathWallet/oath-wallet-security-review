import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('tron_properties', ROOT/'scripts/tron-properties.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class TronHarnessTests(unittest.TestCase):
    def test_deterministic_integer_oracle(self):
        values = runner.amount_vectors()
        self.assertEqual(values, runner.amount_vectors())
        self.assertEqual(len(values), 1006)
        for value in values:
            self.assertEqual(int(value['decimal']), int(value['hex'],16))
            self.assertEqual(len(value['hex']), 64)
            self.assertLess(int(value['decimal']), 1 << 256)

    def test_accepts_real_xctest_formats(self):
        for template in ["Test Case '-[TronAudit.TronAuditProductionTests {}]' passed (1.0 seconds).",
                         "Test Case 'TronAuditProductionTests.{}' passed (1.0 seconds)."]:
            text = '\n'.join(template.format(name) for name in sorted(runner.EXPECTED))
            self.assertTrue(runner.successful(text, 0))
            self.assertFalse(runner.successful(text, 1))
            self.assertFalse(runner.successful(text + '\n' + text, 0))
            self.assertFalse(runner.successful('\n'.join(text.splitlines()[1:]), 0))

    def test_no_build_or_skip_only_pass(self):
        self.assertFalse(runner.successful('Build complete!', 0))
        self.assertFalse(runner.successful('', 0))
        self.assertFalse(runner.successful("Test Case 'TronAuditProductionTests.testPlanBoundsAndExpiry' skipped (1.0 seconds).", 0))
