import importlib.util
from pathlib import Path
import sys
import unittest

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('svg_graph',scripts/'svg-reference-graph.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class SVGGraphEvidenceTests(unittest.TestCase):
    def test_crash_requires_signal_and_only_target_start(self):
        name=f'-[{runner.SUITE} {runner.CRASH}]';start=f"Test Case '{name}' started."
        self.assertEqual(runner.outcome(start,-11,runner.CRASH,True),'expected-signal-11')
        for text,code in [(start,1),(start,-6),(start,124),('',-11),(start+'\n'+start,-11),(start+'\nx: error: other',-11)]:
            self.assertEqual(runner.outcome(text,code,runner.CRASH,True),'failed')
        self.assertEqual(runner.outcome(start,-11,runner.CRASH,False),'failed')
    def test_depth_assertion_must_be_specific(self):
        name=f'-[{runner.SUITE} {runner.OVER}]'
        text=f"Test Case '{name}' started.\nfile: error: {name} : XCTAssertThrowsError failed: did not throw an error - Over-budget SVG must be rejected before rendering\nTest Case '{name}' failed (0.1 seconds)."
        self.assertEqual(runner.outcome(text,1,runner.OVER,True),'expected-depth-assertion')
        self.assertEqual(runner.outcome(text.replace('must be','was'),1,runner.OVER,True),'failed')
        self.assertEqual(runner.outcome(text,1,runner.OVER,False),'failed')
    def test_each_after_case_must_pass(self):
        for case in runner.CASES:
            name=f'-[{runner.SUITE} {case}]'
            text=f"Test Case '{name}' started.\nTest Case '{name}' passed (0.1 seconds)."
            self.assertEqual(runner.outcome(text,0,case,False),'passed')
            self.assertEqual(runner.outcome(text.replace('passed','skipped'),0,case,False),'failed')
