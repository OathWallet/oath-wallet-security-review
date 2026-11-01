import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('refresh_cancellation',ROOT/'scripts/refresh-cancellation.py')
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CancellationEvidenceTests(unittest.TestCase):
    def test_only_exact_nonempty_case_counts(self):
        name='-[OathDatabaseTests.AnkrSynchronizerTests testCancellationClosesQueuedAdmissionBeforeIndividualWorkersUnwind]'
        passed=f"Test Case '{name}' started.\nTest Case '{name}' passed (0.1 seconds).\n"
        self.assertEqual(runner.outcome(passed,0),'passed')
        for text,code in [(passed,1),(passed+passed,0),('',0),(passed.replace(name,'unrelated'),0)]:
            self.assertEqual(runner.outcome(text,code),'failed')

    def test_crash_skip_or_unrelated_assertion_is_not_reproduction(self):
        name='-[OathDatabaseTests.AnkrSynchronizerTests testCancellationClosesQueuedAdmissionBeforeIndividualWorkersUnwind]'
        failure=f"Test Case '{name}' started.\nXCTAssertEqual failed: No old queued request may enter the transport during cancellation\nTest Case '{name}' failed (0.1 seconds).\n"
        self.assertEqual(runner.outcome(failure,1),'race-reproduced')
        self.assertEqual(runner.outcome(failure,-9),'failed')
        self.assertEqual(runner.outcome(failure.replace('No old queued request may enter the transport during cancellation','unrelated failure'),1),'failed')
        self.assertEqual(runner.outcome(failure.replace("failed (","skipped ("),0),'failed')
