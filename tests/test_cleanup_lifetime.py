import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('cleanup_lifetime', Path(__file__).resolve().parents[1] / 'scripts/cleanup-lifetime.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CleanupLifetimeEvidenceTests(unittest.TestCase):
    def transcript(self, case, before=False):
        name = f'-[SDKTests.SessionCleanupLifetimeTests {case}]'
        text = f"Test Case '{name}' started.\n"
        if before and case in m.TRAPS:
            return text + 'Fatal error: Attempted to read an unowned reference but object 0x123abc was already destroyed\nexited with unexpected signal code 6\n'
        if before and case in m.ASSERTIONS:
            for message in m.ASSERTIONS[case]: text += f'fixture.swift:1: error: {name} : {message}\n'
        outcome = 'failed' if before and case in m.ASSERTIONS else 'passed'
        return text + f"Test Case '{name}' {outcome} (0.01 seconds).\n"

    def testExactBeforeAndAfterOutcomes(self):
        for case in m.CASES:
            expected = 'expected-unowned-reference-trap' if case in m.TRAPS else 'expected-lifetime-failure' if case in m.ASSERTIONS else 'passed'
            self.assertEqual(m.classify(self.transcript(case, True), int(case in m.ASSERTIONS or case in m.TRAPS), True, case), expected)
            self.assertEqual(m.classify(self.transcript(case), 0, False, case), 'passed')

    def testBaselineRequiresSpecificAssertionsAndCounts(self):
        for case in m.ASSERTIONS:
            text = self.transcript(case, True)
            for bad in [text.replace(m.ASSERTIONS[case][0], 'XCTAssertTrue failed - unrelated', 1),
                        '\n'.join(line for line in text.splitlines() if ': error:' not in line),
                        text + 'fixture.swift:1: error: unrelated\n', text + text]:
                self.assertEqual(m.classify(bad, 1, True, case), 'failed')
            self.assertEqual(m.classify(text, 0, True, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')

    def testRejectsMissingSkippedFailedOrCrashedCases(self):
        for case in m.CASES:
            text = self.transcript(case)
            for bad in ['', text.replace('passed', 'skipped'), text.replace('passed', 'failed'),
                        text.replace(case, 'unrelated'), text + 'Fatal error: unrelated\n', text + text]:
                self.assertEqual(m.classify(bad, 0, False, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')

    def testTrapsRequireExactCaseAndUnownedReferenceFailure(self):
        for case in m.TRAPS:
            text = self.transcript(case, True)
            for bad in [text.replace('unowned reference', 'unrelated pointer'),
                        text.replace('signal code 6', 'signal code 4'),
                        text.replace(case, 'unrelated'), text + text,
                        text + 'fixture.swift:1: error: unrelated\n']:
                self.assertEqual(m.classify(bad, 1, True, case), 'failed')
            self.assertEqual(m.classify(text, 0, True, case), 'failed')
            self.assertEqual(m.classify(text, 1, False, case), 'failed')
