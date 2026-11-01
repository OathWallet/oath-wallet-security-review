import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('evm_boundary', ROOT/'scripts/evm-response-boundary.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EVMResponseEvidenceTests(unittest.TestCase):
    def log(self, before=False):
        lines = []
        for case in sorted(runner.CASES):
            name = f'-[OathAnkrTests.EVMSendResponseBoundaryTests {case}]'
            lines.append(f"Test Case '{name}' started.")
            if before and case == 'testOversizedStandaloneChainReplyPreventsBroadcast':
                lines.extend(['Oversized standalone chain reply must be rejected before broadcast',
                              'Oversized standalone chain reply must not admit a broadcast'])
                state = 'failed'
            else:
                state = 'passed'
            lines.append(f"Test Case '{name}' {state} (0.01 seconds).")
        return '\n'.join(lines)+'\n'

    def test_requires_all_three_exact_cases(self):
        log = self.log()
        self.assertEqual(runner.outcome(log, 0), 'passed')
        for text, code in [('', 0), (log+log, 0), (log, 1), (log.replace('passed', 'skipped'), 0)]:
            self.assertEqual(runner.outcome(text, code), 'failed')

    def test_reproduction_requires_specific_failure_and_passing_controls(self):
        log = self.log(before=True)
        self.assertEqual(runner.outcome(log, 1), 'boundary-reproduced')
        for text, code in [(log, -9), (log, 0), (log.replace('passed', 'failed'), 1),
                           (log.replace('Oversized standalone chain reply must not admit a broadcast', 'other'), 1)]:
            self.assertEqual(runner.outcome(text, code), 'failed')
