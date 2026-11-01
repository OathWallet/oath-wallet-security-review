import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('session_expiry', Path(__file__).resolve().parents[1] / 'scripts/session-expiry.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class SessionExpiryEvidenceTests(unittest.TestCase):
    def transcript(self, case, before):
        name = f'-[SDKTests.SessionExpiryTests {case}]'
        text = f"Test Case '{name}' started.\n"
        if before and case in m.TRAPS:
            return text + 'error: Process xctest exited with unexpected signal code 5\nSwift: Fatal error: '+m.TRAPS[case]+'\n'
        if before and case in m.ASSERTIONS:
            for message in m.ASSERTIONS[case]:
                text += f'fixture.swift:1: error: {name} : XCTAssertThrowsError failed - {message}\n'
        outcome = 'failed' if before and case in m.ASSERTIONS else 'passed'
        return text + f"Test Case '{name}' {outcome} (0.01 seconds).\n"

    def testBeforeRequiresNamedExpectedFailureOrPassingControl(self):
        for case in m.CASES:
            text = self.transcript(case, True)
            code = 0 if case in m.CONTROLS else 1
            expected = 'passed' if case in m.CONTROLS else 'expected-conversion-trap' if case in m.TRAPS else 'expected-expiry-assertions'
            self.assertEqual(m.classify(text, code, True, case), expected)
            for bad in ['', text + text, text.replace(case, 'unrelated'), text + 'fixture:1: error: unrelated\n']:
                self.assertEqual(m.classify(bad, code, True, case), 'failed')

    def testCrashesMustBeExactAndNotCompilationFailures(self):
        for case in m.TRAPS:
            text = self.transcript(case, True)
            for bad in [text.replace('Double value cannot be converted', 'Unrelated crash'),
                        text.replace('exited with unexpected signal code 5', 'build failed'),
                        text.replace('started.', 'skipped.'), 'compiler failed']:
                self.assertEqual(m.classify(bad, 1, True, case), 'failed')
            self.assertEqual(m.classify(text, 0, True, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')

    def testAfterRequiresSinglePassingCase(self):
        for case in m.CASES:
            text = self.transcript(case, False)
            self.assertEqual(m.classify(text, 0, False, case), 'passed')
            for bad in [text.replace('passed', 'skipped'), text.replace('passed', 'failed'), text + text,
                        text + 'Fatal error: unrelated\n', text + 'fixture:1: error: unrelated\n']:
                self.assertEqual(m.classify(bad, 0, False, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')

    def testAssertionMessageMustMatch(self):
        for case in m.ASSERTIONS:
            text = self.transcript(case, True)
            self.assertEqual(m.classify(text.replace(m.ASSERTIONS[case][0], 'Unexpected failure'), 1, True, case), 'failed')
