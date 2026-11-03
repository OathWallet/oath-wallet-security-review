import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).resolve().parents[1]/'scripts/connect-removal-race.py'
spec=importlib.util.spec_from_file_location('removal_race',P)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Contract(unittest.TestCase):
    def output(self,before=False,recovery=False):
        cases=module.expected_cases(before,recovery)
        text='\n'.join(f'{state}: {name}' for state,name in cases)+'\n'
        text+=('Passed 30 wallet removal recovery checks. Synthetic memory credentials and real encrypted vault/database; no device or network.' if recovery else
               f'Removal journal race checks: {19 if before else 23} passed, {4 if before else 0} failed')+'\n'
        return text
    def test_exact_before_after_and_recovery(self):
        for before,recovery in [(True,False),(False,False),(False,True)]:
            cases=module.validate(1 if before else 0,self.output(before,recovery),before,recovery)
            self.assertEqual(len(cases),30 if recovery else 23)
    def test_missing_duplicate_changed_cases_and_summary_fail(self):
        text=self.output()
        for bad in [text.replace('PASS: journal first / production vault signature verifies\n',''),
                    text+text, text.replace('restart preserves recoverability','unrelated check',1),
                    text.replace('23 passed','22 passed')]:
            with self.assertRaises(ValueError):module.validate(0,bad)
    def test_wrong_exit_or_unexpected_pass_cannot_certify_before(self):
        with self.assertRaises(ValueError):module.validate(0,self.output(True),True)
        with self.assertRaises(ValueError):module.validate(1,self.output(),True)
        with self.assertRaises(ValueError):module.validate(1,self.output())
