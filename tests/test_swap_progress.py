import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('swap_progress', Path(__file__).resolve().parents[1] / 'scripts/swap-progress.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class SwapProgressEvidenceTests(unittest.TestCase):
    def transcript(self, result='passed', failures=''):
        name = f'-[OathAnkrTests.ThorchainSwapDestinationTests {m.CASES[0]}]'
        return f"Test Case '{name}' started.\n{failures}\nTest Case '{name}' {result} (0.02 seconds).\n"

    def testOnlyOneRealMatchingTestCanPass(self):
        text = self.transcript()
        self.assertEqual(m.outcome(text, 0, m.CASES[0]), 'passed')
        for bad in ['', text + text, text.replace(m.CASES[0], m.CASES[1]), self.transcript('skipped'), self.transcript(failures='file:1: error: unrelated')]:
            self.assertEqual(m.outcome(bad, 0, m.CASES[0]), 'failed')
        self.assertEqual(m.outcome(text, 1, m.CASES[0]), 'failed')

    def testBaselineRequiresFourExactDestinationMismatches(self):
        line = 'file.swift:32: error: test : XCTAssertEqual failed: (nil) is not equal to (Optional("CDCD")) - Polygon checksum variants must identify the same payout destination'
        text = self.transcript('failed', '\n'.join([line] * 4))
        self.assertEqual(m.outcome(text, 1, m.CASES[0]), 'destination-mismatch-reproduced')
        for bad in [self.transcript('failed', line), text.replace('nil', 'unrelated'), text.replace('Polygon checksum', 'Different test'), text + '\nfile:2: error: unrelated', text.replace('XCTAssertEqual failed', 'unexpected throw')]:
            self.assertEqual(m.outcome(bad, 1, m.CASES[0]), 'failed')
        self.assertEqual(m.outcome(text, 0, m.CASES[0]), 'failed')
