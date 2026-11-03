import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('backup_replay',ROOT/'scripts/backup-presentation.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class BackupPresentationReplayTests(unittest.TestCase):
    def output(self,stage):
        failed=3 if stage=='before' else 0
        return '\n'.join(('FAIL' if stage=='before' and n in r.FAILURES else 'PASS')+': '+n for n in r.NAMES)+f'\nBackup presentation checks: {15-failed} passed, {failed} failed\n'
    def test_exact_results(self):
        self.assertEqual(r.validate('before',1,self.output('before'))['failed'],3)
        self.assertEqual(r.validate('after',0,self.output('after'))['passed'],15)
    def test_missing_duplicate_or_renamed_case(self):
        s=self.output('after')
        for t in ['\n'.join(s.splitlines()[1:]),s+s.splitlines()[0]+'\n',s.replace(r.NAMES[0],'wrong')]:
            with self.assertRaises(ValueError):r.validate('after',0,t)
    def test_summary_and_exit_required(self):
        s=self.output('before')
        for t in ['\n'.join(s.splitlines()[:-1]),s+s.splitlines()[-1]+'\n']:
            with self.assertRaises(ValueError):r.validate('before',1,t)
        for code in [0,-5,2]:
            with self.assertRaises(ValueError):r.validate('before',code,s)
    def test_current_failures_remain_controls(self):
        with self.assertRaises(ValueError):r.validate('after',0,self.output('after').replace('PASS: current failure remains visible','FAIL: current failure remains visible'))
if __name__=='__main__':unittest.main()
