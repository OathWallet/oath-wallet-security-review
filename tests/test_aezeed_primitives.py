import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
spec = importlib.util.spec_from_file_location('primitives', Path(__file__).resolve().parents[1]/'scripts/aezeed-primitives.py')
primitives = importlib.util.module_from_spec(spec)
spec.loader.exec_module(primitives)


class PrimitiveResultTests(unittest.TestCase):
    def events(self):
        return [{'Action': 'pass', 'Test': case} for case in sorted(primitives.EXPECTED)] + [{'Action': 'pass'}]

    def check(self, events, code=0):
        return primitives.successful('\n'.join(json.dumps(row) for row in events), code)

    def test_exact_results(self):
        self.assertTrue(self.check(self.events()))

    def test_empty_missing_duplicate_skip_failure_rejected(self):
        rows = self.events()
        for events in [[], rows[1:], rows+rows[:1], rows+[{'Action':'skip'}], rows+[{'Action':'fail'}], rows[:-1]]:
            self.assertFalse(self.check(events))
        self.assertFalse(self.check(rows, 1))
        self.assertFalse(primitives.successful('not JSON', 0))
