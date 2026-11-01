import importlib.util
from pathlib import Path
import sys
import unittest

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('psbt_size',scripts/'bitcoin-psbt-size.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class PSBTSizeEvidenceTests(unittest.TestCase):
    def test_exact_size_failure_requires_a_real_assertion(self):
        case=runner.EXACT;name=f'-[{runner.SUITE} {case}]'
        t=f"Test Case '{name}' started.\nx: error: {name} : XCTAssertThrowsError failed: did not throw an error\nTest Case '{name}' failed (0.02 seconds)."
        self.assertEqual(runner.outcome(t,1,case,True),'expected-size-failure')
        for changed in [t.replace('ThrowsError','Equal'),t+'\nfile: error: unrelated',t.replace('started','skipped')]:
            self.assertEqual(runner.outcome(changed,1,case,True),'failed')
        self.assertEqual(runner.outcome(t,1,case,False),'failed')
    def test_each_case_needs_its_own_pass(self):
        for case in runner.CASES:
            name=f'-[{runner.SUITE} {case}]'
            t=f"Test Case '{name}' started.\nTest Case '{name}' passed (0.02 seconds)."
            self.assertEqual(runner.outcome(t,0,case,False),'passed')
            self.assertEqual(runner.outcome(t,0,case,True),'passed' if case==runner.CASES[-1] else 'failed')
            self.assertEqual(runner.outcome(t.replace('passed','skipped'),0,case,False),'failed')
