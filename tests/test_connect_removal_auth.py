import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'scripts/connect-removal-auth.py'
s=importlib.util.spec_from_file_location('removal_auth',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Results(unittest.TestCase):
    def text(self,mutant=False):
        return '\n'.join(s+': '+n for s,n in m.expected_cases(mutant))+f'\nRemoval authentication checks: {36 if mutant else 38} passed, {2 if mutant else 0} failed\n'
    def test_exact_success_and_negative_control(self):
        m.validate(0,self.text());m.validate(1,self.text(True),True)
    def test_missing_duplicate_wrong_case_and_wrong_exit_rejected(self):
        text=self.text()
        for bad in ['',text.replace('PASS: message / soft removal initial signature\n',''),text+text,text.replace('PASS:','FAIL:',1)]:
            with self.assertRaises(ValueError):m.validate(0,bad)
        with self.assertRaises(ValueError):m.validate(1,text)
    def test_mutation_needs_exact_failures(self):
        with self.assertRaises(ValueError):m.validate(0,self.text(),True)
        with self.assertRaises(ValueError):m.validate(1,self.text(True).replace('FAIL:','PASS:',1),True)
