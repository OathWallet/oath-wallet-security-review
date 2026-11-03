import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('token_order', ROOT / 'scripts/token-search-order.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class TokenOrderReplayTests(unittest.TestCase):
    def log(self, name, state, errors=0):
        case = f'-[TokenLookupTests.TokenLookupTests {name}]'
        return f"Test Case '{case}' started.\n" + ': error: assertion\n' * errors + f"Test Case '{case}' {state} (0.1 seconds).\n"

    def test_success_requires_actual_case_and_no_assertion(self):
        for name in replay.CASES:
            self.assertEqual(replay.verify(name, False, 0, self.log(name, 'passed')), 0)
            for text in ['', self.log(name+'Other', 'passed'), self.log(name, 'failed', 1)]:
                with self.assertRaises(ValueError):
                    replay.verify(name, False, 0, text)

    def test_mutant_requires_exact_assertion_count_and_failure(self):
        for name, count in replay.CASES.items():
            self.assertEqual(replay.verify(name, True, 1, self.log(name, 'failed', count)), count)
            for code, text in [(0, self.log(name, 'passed')), (-5, self.log(name, 'failed', count)),
                               (1, self.log(name, 'failed', count-1)), (1, self.log(name, 'failed', count+1)),
                               (1, self.log(name, 'passed', count))]:
                with self.assertRaises(ValueError):
                    replay.verify(name, True, code, text)

    def test_mutation_is_limited_to_refresh_guards(self):
        guard = '                guard !Task.isCancelled, generation == request else { return }\n'
        start = '            if await catalog.refreshIfNeeded() {\n'
        end = '            return\n        }'
        text = guard + start + guard + '                keepThis()\n' + guard + end + guard
        self.assertEqual(replay.mutate(text), guard + start + '                keepThis()\n' + end + guard)
        with self.assertRaises(ValueError):
            replay.mutate(start + guard + end)

    def test_logs_sanitize_machine_paths(self):
        for path in ['/private/var/folders/a/source.swift', '/var/folders/a/source.swift', '/Users/fixture/file.swift', '/home/runner/file.swift']:
            text = replay.sanitized((path + ':37: error: assertion').encode()).decode()
            self.assertNotIn(path, text)
            self.assertIn(':37: error: assertion', text)


if __name__ == '__main__':
    unittest.main()
