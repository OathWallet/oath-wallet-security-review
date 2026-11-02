import importlib.util
from pathlib import Path
import signal
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('signature_replay', ROOT / 'scripts/signature-contract-boundaries.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class SignatureReplayTests(unittest.TestCase):
    def text(self, name, state=None, failures=0):
        full = f"-[SDKTests.SignatureBoundaryTests {name}]"
        result = f"Test Case '{full}' started.\n" + ": error: assertion\n" * failures
        if state:
            result += f"Test Case '{full}' {state} (0.1 seconds).\n"
        return result

    def test_each_success_requires_exact_case_completion(self):
        name = 'testValidAddressAndIntegers'
        for stage in ['before', 'after']:
            self.assertEqual(replay.validate_case(name, stage, 0, self.text(name, 'passed')), 'passed')
            for text in ['', self.text(name), self.text(name + 'Other', 'passed')]:
                with self.assertRaises(ValueError):
                    replay.validate_case(name, stage, 0, text)

    def test_expected_crash_is_never_a_success(self):
        for name in replay.CRASHES:
            self.assertEqual(replay.validate_case(name, 'before', -signal.SIGTRAP, self.text(name)), 'trapped')
            for code in [0, 1, -signal.SIGABRT]:
                with self.assertRaises(ValueError):
                    replay.validate_case(name, 'before', code, self.text(name))
            with self.assertRaises(ValueError):
                replay.validate_case(name, 'after', -signal.SIGTRAP, self.text(name))

    def test_original_assertions_need_the_expected_count(self):
        for name, count in replay.FAILURES.items():
            self.assertEqual(replay.validate_case(name, 'before', 1, self.text(name, 'failed', count)), 'failed')
            with self.assertRaises(ValueError):
                replay.validate_case(name, 'before', 1, self.text(name, 'failed', count + 1))
            with self.assertRaises(ValueError):
                replay.validate_case(name, 'after', 1, self.text(name, 'failed', count))

    def test_local_paths_are_removed_from_public_logs(self):
        for path in ['/private/var/folders/xx/a/file.swift', '/var/folders/xx/a/file.swift',
                     '/Users/synthetic/file.swift', '/home/runner/file.swift']:
            data = replay.sanitized((path + ':12: error: assertion').encode()).decode()
            self.assertNotIn(path, data)
            self.assertIn(':12: error: assertion', data)


if __name__ == '__main__':
    unittest.main()
