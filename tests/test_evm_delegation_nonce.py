import importlib.util
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('nonce_runner', ROOT/'scripts/evm-delegation-nonce.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class NonceEvidenceTests(unittest.TestCase):
    def log(self, name, state=None):
        prefix = f"Test Case '-[OathAnkrTests.EVMDelegationNonceBoundaryTests {name}]'"
        return prefix+' started.\n'+(prefix+f' {state} (0.01 seconds).\n' if state else '')

    def test_pass_requires_exact_case_completion(self):
        name=runner.CASES[2]; log=self.log(name,'passed')
        self.assertEqual(runner.outcome(log,0,name),'passed')
        for text,code in [('',0),(log+log,0),(log,1),(self.log(name,'skipped'),0)]:
            self.assertEqual(runner.outcome(text,code,name),'failed')

    def test_trap_is_only_provisional_until_stack_is_verified(self):
        name=runner.CASES[0]
        self.assertEqual(runner.outcome(self.log(name),-5,name),'trap-needs-stack-verification')
        for code in [-9,1,0]:
            self.assertEqual(runner.outcome(self.log(name),code,name),'failed')
        markers=['stop reason = Swift runtime failure: arithmetic overflow','EVMSendCrypto.fields(',
                 'EVMSendCrypto.swift:31:',name,'plan.nonce+1']
        self.assertTrue(runner.proves_overflow('\n'.join(markers)))
        for marker in markers:
            self.assertFalse(runner.proves_overflow('\n'.join(x for x in markers if x!=marker)))

    def test_invalid_acceptance_requires_expected_assertion(self):
        name=runner.CASES[1]; log=self.log(name,'failed')
        self.assertEqual(runner.outcome(log,1,name),'failed')
        log+='XCTAssertThrowsError failed: did not throw an error\n'
        self.assertEqual(runner.outcome(log,1,name),'invalid-nonce-accepted')
        self.assertEqual(runner.outcome(log,0,name),'failed')
