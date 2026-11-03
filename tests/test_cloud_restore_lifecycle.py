import importlib.util
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('restore_lifecycle', ROOT/'scripts/cloud-restore-lifecycle.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)

class RestoreLifecycleTests(unittest.TestCase):
    def output(self, mutant=False):
        return '\n'.join(('FAIL' if mutant and n in r.MUTANT_FAILURES else 'PASS')+': '+n for n in r.NAMES)+f'\nCloud restore lifecycle checks: {19 if mutant else 22} passed, {3 if mutant else 0} failed\n'
    def test_exact_controls(self):
        self.assertEqual(len(r.validate(0,self.output())),22)
        self.assertEqual(len(r.validate(1,self.output(True),True)),22)
    def test_missing_duplicate_or_renamed_case_rejected(self):
        text = self.output()
        for value in ['\n'.join(text.splitlines()[1:]), text+text.splitlines()[0]+'\n', text.replace(r.NAMES[0],'unknown')]:
            with self.assertRaises(ValueError): r.validate(0,value)
    def test_exit_and_summary_required(self):
        for code in [-5,1,2]:
            with self.assertRaises(ValueError): r.validate(code,self.output())
        for value in ['\n'.join(self.output().splitlines()[:-1]),self.output()+self.output().splitlines()[-1]+'\n']:
            with self.assertRaises(ValueError): r.validate(0,value)
    def test_mutation_cannot_be_reported_as_production_success(self):
        with self.assertRaises(ValueError): r.validate(1,self.output(True))
        with self.assertRaises(ValueError): r.validate(0,self.output(),True)

if __name__ == '__main__': unittest.main()
