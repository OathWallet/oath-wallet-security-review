import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1]/'scripts/xrpl-connect-simulation.py'
spec = importlib.util.spec_from_file_location('xrpl_simulation', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ReplayContract(unittest.TestCase):
    def cases(self, before):
        return [dict(selector='Suite/'+name,
                     status='failed' if before and name in m.FAILING else 'passed',
                     exit_code=1 if before and name in m.FAILING else 0) for name in sorted(m.METHODS)]

    def test_exact_before_and_after(self):
        m.verify(self.cases(True), True)
        m.verify(self.cases(False), False)

    def test_missing_duplicate_and_skip_fail(self):
        cases=self.cases(False)
        for invalid in [[], cases[:-1], cases+[cases[0]], [cases[0]]*6,
                        [dict(c, status='skipped') for c in cases]]:
            with self.assertRaises(ValueError): m.verify(invalid, False)

    def test_wrong_failure_or_exit_fail(self):
        with self.assertRaises(ValueError): m.verify(self.cases(False), True)
        with self.assertRaises(ValueError): m.verify(self.cases(True), False)
        with self.assertRaises(ValueError): m.verify([dict(c,exit_code=1) for c in self.cases(False)], False)
