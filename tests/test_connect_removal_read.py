import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'scripts/connect-removal-read.py'
s=importlib.util.spec_from_file_location('removal_read',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Results(unittest.TestCase):
    def text(self,vulnerable=False):
        return '\n'.join(s+': '+n for s,n in m.expected_cases(vulnerable))+f'\nRemoval account-read checks: {54 if vulnerable else 66} passed, {12 if vulnerable else 0} failed\n'
    def test_exact_before_and_after(self):
        self.assertEqual(len(m.validate(0,self.text())),66)
        self.assertEqual(len(m.validate(1,self.text(True),True)),66)
    def test_missing_duplicate_wrong_case_and_wrong_exit_rejected(self):
        text=self.text()
        for bad in ['',text.replace('PASS: message / soft removal initial signature\n',''),text+text,text.replace('PASS:','FAIL:',1)]:
            with self.assertRaises(ValueError):m.validate(0,bad)
        with self.assertRaises(ValueError):m.validate(1,text)
    def test_before_requires_exact_failures(self):
        with self.assertRaises(ValueError):m.validate(0,self.text(),True)
        with self.assertRaises(ValueError):m.validate(1,self.text(True).replace('FAIL:','PASS:',1),True)
    def test_controls_remain_passing_before(self):
        failed=[n for s,n in m.expected_cases(True) if s=='FAIL']
        self.assertEqual(len(failed),12)
        self.assertTrue(all(n.endswith(('delayed result','batch consent lifetime')) for n in failed))
        self.assertFalse(any('fresh restored' in n or 'failed save' in n or 'other wallet' in n or '/ lock' in n for n in failed))
