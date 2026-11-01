import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('namespace_boundary', Path(__file__).resolve().parents[1] / 'scripts/namespace-boundary.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class NamespaceBoundaryEvidenceTests(unittest.TestCase):
    def transcript(self, case, before):
        name = f'-[SDKTests.NamespaceBoundaryTests {case}]'
        text = f"Test Case '{name}' started.\n"
        if before and case in m.TRAPS:
            return text + f'error: Process xctest exited with unexpected signal code 5\nSchemas/{m.TRAPS[case]}:118: Fatal error: Unexpectedly found nil while unwrapping an Optional value\n'
        if before and case in m.ASSERTIONS:
            for message in m.ASSERTIONS[case]: text += f'fixture.swift:1: error: {name} : XCTAssertFalse failed - {message}\n'
        if before and case in m.ERRORS: text += f'<EXPR>:0: error: {name} : {m.ERRORS[case]}\n'
        status = 'failed' if before and case not in m.CONTROLS else 'passed'
        return text + f"Test Case '{name}' {status} (0.01 seconds).\n"

    def testAllBaselineCasesHaveExactExpectedOutcomes(self):
        for case in m.CASES:
            text = self.transcript(case, True); code = 0 if case in m.CONTROLS else 1
            expected = 'passed' if case in m.CONTROLS else 'expected-optional-trap' if case in m.TRAPS else 'expected-namespace-failure'
            self.assertEqual(m.classify(text, code, True, case), expected)
            for bad in ['', text+text, text.replace(case,'unrelated'), text+'file:1: error: unrelated\n']:
                self.assertEqual(m.classify(bad, code, True, case), 'failed')

    def testCrashMustIdentifyTheProductionFileAndTrap(self):
        for case in m.TRAPS:
            text = self.transcript(case, True)
            for bad in [text.replace(m.TRAPS[case], 'Other.swift'), text.replace('Unexpectedly found nil', 'Different crash'),
                        text.replace('exited with unexpected signal code 5','build failed'), text.replace('started.','skipped.')]:
                self.assertEqual(m.classify(bad, 1, True, case), 'failed')
            self.assertEqual(m.classify(text, 0, True, case), 'failed')

    def testUnexpectedErrorMustMatchExactly(self):
        for case in m.ERRORS:
            text = self.transcript(case, True)
            self.assertEqual(m.classify(text.replace(m.ERRORS[case], 'failed: caught error: unrelated'), 1, True, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')

    def testAssertionMessagesAndCountsMustMatch(self):
        for case in m.ASSERTIONS:
            text = self.transcript(case, True)
            self.assertEqual(m.classify(text.replace(m.ASSERTIONS[case][0], 'wrong assertion', 1), 1, True, case), 'failed')
            self.assertEqual(m.classify(text, 0, True, case), 'failed')

    def testAfterMustPassEachCaseOnce(self):
        for case in m.CASES:
            text = self.transcript(case, False)
            self.assertEqual(m.classify(text, 0, False, case), 'passed')
            for bad in [text+text, text.replace('passed','skipped'), text.replace('passed','failed'), text+'Fatal error: unrelated\n']:
                self.assertEqual(m.classify(bad, 0, False, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')
