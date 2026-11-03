import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('audit_run', ROOT / 'scripts/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PrivateKeyResultsTests(unittest.TestCase):
    summary = ('Passed 305 HD private-key browser/vault host checks. Synthetic seed adapter; '
               'real public descriptors, leaf-key derivation, database and authorization. '
               'No user data, network, simulator or device used.')

    def test_exact_nonzero_summary(self):
        self.assertEqual(runner.private_key_case_count(self.summary + '\n'), 305)

    def test_reduced_assertion_count_rejected(self):
        self.assertIsNone(runner.private_key_case_count(self.summary.replace('305', '304')))
        self.assertIsNone(runner.private_key_case_count(self.summary.replace('305', '1')))

    def test_build_without_execution_does_not_pass(self):
        self.assertIsNone(runner.private_key_case_count('Build complete!\n'))

    def test_duplicate_or_zero_summary_rejected(self):
        self.assertIsNone(runner.private_key_case_count(self.summary + '\n' + self.summary))
        self.assertIsNone(runner.private_key_case_count(self.summary.replace('305', '0')))

    def test_wrong_scope_summary_rejected(self):
        self.assertIsNone(runner.private_key_case_count(self.summary.replace('Synthetic seed adapter; ', '')))


if __name__ == '__main__':
    unittest.main()
