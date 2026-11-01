import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('batch_races',ROOT/'scripts/permission-batch-races.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class PermissionRaceEvidenceTests(unittest.TestCase):
    def test_pass_requires_full_exact_summary(self):
        log='BATCH_RACES checks=84 failures=0 scenarios=21 chains=3\n'
        self.assertEqual(runner.outcome(log,0),'passed')
        for text,code in [('',0),(log+log,0),(log,1),(log.replace('84','83'),0),('FAIL: unrelated\n'+log,0)]:
            self.assertEqual(runner.outcome(text,code),'failed')

    def test_before_requires_exact_nine_revocation_failures(self):
        log='\n'.join('FAIL: '+x for x in sorted(runner.EXPECTED_FAILURES))+'\nBATCH_RACES checks=84 failures=9 scenarios=21 chains=3\n'
        self.assertEqual(runner.outcome(log,1),'revocation-reproduced')
        for text,code in [(log,0),(log,-5),(log.replace('tron/end:','tron/lock:'),1),(log.replace('chains=3','chains=2'),1),(log+'FAIL: unrelated\n',1)]:
            self.assertEqual(runner.outcome(text,code),'failed')
