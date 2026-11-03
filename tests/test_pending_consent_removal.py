import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'scripts/pending-consent-removal.py'
s=importlib.util.spec_from_file_location('pending_consent_removal',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Contract(unittest.TestCase):
    def output(self,before=False):
        return '\n'.join(s+': '+n for s,n in m.expected_cases(before))+f'\nPending consent checks: {13 if before else 14} passed, {1 if before else 0} failed\n'
    def test_exact_before_after(self):
        self.assertEqual(len(m.validate(1,self.output(True),True)),14)
        self.assertEqual(len(m.validate(0,self.output())),14)
    def test_missing_duplicate_wrong_summary_and_exit_rejected(self):
        text=self.output()
        for bad in ['',text+text,text.replace('14 passed','13 passed'),text.replace('PASS: lock delayed consent\n','')]:
            with self.assertRaises(ValueError):m.validate(0,bad)
        with self.assertRaises(ValueError):m.validate(1,text)
    def test_only_restored_old_consent_fails_before(self):
        self.assertEqual([n for s,n in m.expected_cases(True) if s=='FAIL'],['remove and restore delayed consent'])
        with self.assertRaises(ValueError):m.validate(0,self.output(),True)
