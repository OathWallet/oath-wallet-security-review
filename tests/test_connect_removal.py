import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1]/'scripts/connect-removal.py'
spec = importlib.util.spec_from_file_location('connect_removal', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ReplayContract(unittest.TestCase):
    def cases(self, phase):
        names = {m.COMPAT} if phase == 'compatibility' else m.FAILURES | m.CONTROLS | ({m.COMPAT} if phase == 'after' else set())
        return [dict(selector='WalletConnectRemovalGuardTests/'+name,
                     status='failed' if phase == 'compatibility' or (phase == 'before' and name in m.FAILURES) else 'passed',
                     exit_code=1 if phase == 'compatibility' or (phase == 'before' and name in m.FAILURES) else 0) for name in sorted(names)]

    def test_exact_three_phases(self):
        for phase in m.PINS: m.verify(self.cases(phase), phase)

    def test_missing_duplicate_skip_and_wrong_exit_rejected(self):
        for phase in m.PINS:
            cases = self.cases(phase)
            for invalid in [[], cases[:-1], cases+[cases[0]], [dict(c, status='skipped') for c in cases], [dict(c, exit_code=1-c['exit_code']) for c in cases]]:
                with self.assertRaises(ValueError): m.verify(invalid, phase)

    def test_wrong_phase_or_unexpected_failure_rejected(self):
        for phase in m.PINS:
            cases = self.cases(phase)
            bad = [dict(c, status='failed' if c['status']=='passed' else 'passed', exit_code=1-c['exit_code']) for c in cases]
            with self.assertRaises(ValueError): m.verify(bad, phase)
        with self.assertRaises(ValueError): m.verify(self.cases('after'), 'before')
