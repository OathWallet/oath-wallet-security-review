import importlib.util
from pathlib import Path
import sys
import unittest

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('parent_budget',scripts/'bitcoin-parent-budget.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class ParentFetchEvidenceTests(unittest.TestCase):
    def test_only_successful_interception_can_demonstrate_retention(self):
        name=f'-[{runner.SUITE} {runner.OVER}]'
        t=f"Test Case '{name}' started.\na.swift:1: error: {name} : failed - Six hash-verified parents exceeded the packet budget\nTest Case '{name}' failed (0.02 seconds)."
        self.assertEqual(runner.outcome(t,1,runner.OVER,True),'expected-retention-failure')
        for wrong in [t+'\na.swift:2: error: unexpected bytes',t.replace('Six','Two'),t.replace('started','skipped')]:
            self.assertEqual(runner.outcome(wrong,1,runner.OVER,True),'failed')
        self.assertEqual(runner.outcome(t,1,runner.OVER,False),'failed')
