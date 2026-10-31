import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('isolated_tests',Path(__file__).resolve().parents[1]/'scripts/isolated_tests.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class IsolatedTestResultTests(unittest.TestCase):
    start="Test Case '-[Fixture testOne]' started.\n"
    def test_pass(self):
        self.assertEqual(m.classify(self.start+"Test Case '-[Fixture testOne]' passed (0.001 seconds).\n",0),'passed')
    def test_skip_is_not_pass(self):
        self.assertEqual(m.classify(self.start+"Test Case '-[Fixture testOne]' skipped (0.001 seconds).\n",0),'skipped')
    def test_empty_selection_is_failure(self):
        self.assertEqual(m.classify('Executed 0 tests, 0 failures',0),'failed')
    def test_crash_is_failure(self):
        self.assertEqual(m.classify(self.start,-6),'failed')
    def test_multiple_selected_is_failure(self):
        self.assertEqual(m.classify(self.start*2,0),'failed')
