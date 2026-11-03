import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('disclosure', ROOT / 'scripts/private-key-disclosure.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class DisclosureReplayTests(unittest.TestCase):
    def output(self, stage):
        failed = 4 if stage == 'before' else 0
        return '\n'.join(('FAIL' if stage == 'before' and n in replay.FAILURES else 'PASS') + ': ' + n for n in replay.NAMES) + f'\nPrivate-key disclosure checks: {11-failed} passed, {failed} failed; synthetic reader, production model; no UIKit or OS authentication.\n'

    def test_exact_before_and_after(self):
        for stage, code in [('before', 1), ('after', 0)]:
            self.assertEqual(replay.validate(stage, code, self.output(stage))['failed'], 4 if code else 0)

    def test_missing_duplicate_and_wrong_cases_fail(self):
        text = self.output('after')
        for altered in [text.replace('PASS: native back removes displayed value\n', ''),
                        text + 'PASS: native back removes displayed value\n',
                        text.replace('native back removes displayed value', 'wrong case')]:
            with self.assertRaises(ValueError): replay.validate('after', 0, altered)

    def test_missing_or_duplicate_completion_fails(self):
        text = self.output('after')
        for altered in ['\n'.join(text.splitlines()[:-1]), text + text.splitlines()[-1] + '\n']:
            with self.assertRaises(ValueError): replay.validate('after', 0, altered)

    def test_unexpected_exit_and_signal_fail(self):
        for code in (0, -5, 2):
            with self.assertRaises(ValueError): replay.validate('before', code, self.output('before'))
        with self.assertRaises(ValueError): replay.validate('after', 1, self.output('after'))

    def test_swapped_results_are_not_accepted(self):
        with self.assertRaises(ValueError): replay.validate('after', 0, self.output('before'))
        with self.assertRaises(ValueError): replay.validate('unknown', 0, self.output('after'))

    def test_paths_are_sanitized(self):
        self.assertEqual(replay.sanitized(b'/Users/synthetic/a.swift:12:'), b'<local-file>:12:')


if __name__ == '__main__': unittest.main()
