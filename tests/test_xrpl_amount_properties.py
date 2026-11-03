import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('xrpl_properties',ROOT/'scripts/xrpl-amount-properties.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class XrplPropertyFixtureTests(unittest.TestCase):
    def test_seed_repeats_complete_fixture(self):
        self.assertEqual(r.vectors(),r.vectors())
        self.assertEqual(len(r.vectors()),4900)
    def test_before_failures_are_ratio_cases_with_four_protocol_examples(self):
        rows=r.vectors()
        self.assertEqual(len(r.BASE_FAILURES),57)
        self.assertEqual(len(set(r.BASE_FAILURES)),57)
        self.assertTrue(all(rows[i]['op']=='ratio' for i in r.BASE_FAILURES))
        self.assertTrue(all(rows[i]['value']==str(10**186) for i in r.BASE_FAILURES[-4:]))
    def test_extreme_valid_and_invalid_protocol_values(self):
        rows=r.vectors()
        self.assertIn(dict(op='parse',value='1000000000000000e-96',expected=str(10**15)),rows)
        self.assertIn(dict(op='parse',value='9999999999999999e80',expected=str((10**16-1)*10**176)),rows)
        self.assertIn(dict(op='parse',value='1e96',expected='ERROR'),rows)
    def test_rounding_overflow_remains_rejected(self):
        last=r.vectors()[-1]
        self.assertEqual(last['op'],'ratio');self.assertEqual(last['expected'],'ERROR')
        value=int(last['value'])*last['numerator']
        ceiling=(value+last['denominator']-1)//last['denominator']
        self.assertEqual(ceiling,10**193)

if __name__=='__main__':unittest.main()
