import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run import sdk_case_counts

class SDKResultTests(unittest.TestCase):
    def test_only_actual_case_results_count(self):
        text = """Test Case '-[A testOne]' started.
Test Case '-[A testOne]' passed (0.001 seconds).
Test Case '-[A testTwo]' skipped (0.001 seconds).
Test Case '-[A testThree]' failed (0.001 seconds).
Executed 3 tests, with 1 test skipped and 1 failure.
Test run with 0 tests passed after 0.001 seconds.
"""
        self.assertEqual(sdk_case_counts(text), dict(passed=1, skipped=1, failed=1))

    def test_empty_swift_runner_and_summary_do_not_prove_cases(self):
        self.assertEqual(sdk_case_counts("Test run with 0 tests passed.\nExecuted 20 tests."), dict(passed=0, skipped=0, failed=0))

    def test_known_interleaved_swift_warning_preserves_case_result(self):
        warning = "warning: '--build-system native' has been deprecated and will be removed in a future release; please report an issue at https://github.com/swiftlang/swift-package-manager/issues if you are unable to adopt the default build system.\n"
        text = "Test Case '-[A testType2Wir" + warning + "eFormat]' passed (0.001 seconds).\n"
        self.assertEqual(sdk_case_counts(text), dict(passed=1, skipped=0, failed=0))

    def test_unknown_interruption_is_not_silently_erased(self):
        text = "Test Case '-[A testUnexpected\nother error\nResult]' passed (0.001 seconds).\n"
        self.assertEqual(sdk_case_counts(text), dict(passed=0, skipped=0, failed=0))
