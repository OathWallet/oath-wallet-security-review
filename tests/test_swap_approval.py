import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('swap_approval', Path(__file__).resolve().parents[1] / 'scripts/swap-approval.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class SwapApprovalEvidenceTests(unittest.TestCase):
    def transcript(self, result='passed', failures=''):
        name = f'-[OathAnkrTests.WalletConnectApprovalOperationsTests {m.CASES[0]}]'
        return f"Test Case '{name}' started.\n{failures}\nTest Case '{name}' {result} (0.02 seconds).\n"

    def testOnlyOneRealMatchingTestCanPass(self):
        text = self.transcript()
        self.assertEqual(m.outcome(text, 0, m.CASES[0]), 'passed')
        for bad in ['', text + text, text.replace(m.CASES[0], m.CASES[1]), self.transcript('skipped'), self.transcript(failures='file:1: error: unrelated')]:
            self.assertEqual(m.outcome(bad, 0, m.CASES[0]), 'failed')
        self.assertEqual(m.outcome(text, 1, m.CASES[0]), 'failed')

    def testBaselineRequiresSixSpecificOmissions(self):
        line = 'fixture.swift:32: error: test : XCTAssertNotEqual failed: identical - Approval must retain additional operations: swap-transfer-2'
        text = self.transcript('failed', '\n'.join([line] * 6))
        self.assertEqual(m.outcome(text, 1, m.CASES[0]), 'omitted-operations-reproduced')
        for bad in [self.transcript('failed', line), text.replace('Approval must retain', 'Different test'), text + '\nfile:2: error: unrelated', text.replace('XCTAssertNotEqual failed', 'unexpected throw')]:
            self.assertEqual(m.outcome(bad, 1, m.CASES[0]), 'failed')
        self.assertEqual(m.outcome(text, 0, m.CASES[0]), 'failed')

    def testSemanticMutationBaselineRequiresFourFailures(self):
        method = m.CASES[1]
        line = 'fixture.swift:44: error: test : XCTAssertNotEqual failed: identical - Approval must retain transfer semantics: swap-other-amount'
        text = self.transcript('failed', '\n'.join([line] * 4)).replace(m.CASES[0], method)
        self.assertEqual(m.outcome(text, 1, method), 'omitted-operations-reproduced')
        self.assertEqual(m.outcome(text, 1, m.CASES[0]), 'failed')
