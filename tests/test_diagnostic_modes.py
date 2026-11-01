import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('diagnostic_modes', ROOT/'scripts/diagnostic-modes.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DiagnosticModesTests(unittest.TestCase):
    def test_no_inherited_live_flags_or_credentials(self):
        inherited = {'PATH':'/usr/bin', 'HOME':'/fixture', 'OATH_ARC_LIVE':'1', 'OATH_ANKR_CONFIG':'/secret', 'GH_TOKEN':'secret', 'DYLD_INSERT_LIBRARIES':'bad'}
        for _, _, flag in runner.CASES + runner.TRACE_CASES:
            self.assertEqual(runner.environment(inherited, flag), {'PATH':'/usr/bin','HOME':'/fixture',flag:'1'})
        self.assertEqual(runner.environment(inherited), {'PATH':'/usr/bin','HOME':'/fixture'})
        with self.assertRaises(ValueError):
            runner.environment(inherited, 'OATH_ARC_LIVE')

    def test_selection_must_be_exact_and_nonempty(self):
        cls, method, _ = runner.CASES[0]
        for name in [f'-[OathAnkrTests.{cls} {method}]', f'{cls}.{method}']:
            for status in ['passed','skipped']:
                text = f"Test Case '{name}' started.\nTest Case '{name}' {status} (0.1 seconds).\n"
                self.assertEqual(runner.outcome(text,0,cls,method), status)
                self.assertEqual(runner.outcome(text,1,cls,method), 'failed')
                self.assertEqual(runner.outcome(text+text,0,cls,method), 'failed')
                self.assertEqual(runner.outcome(text,0,cls,'wrong'), 'failed')
                self.assertEqual(runner.outcome(text.splitlines()[1],0,cls,method), 'failed')
        for text in ['', 'Build complete!', 'Test Suite passed.']:
            self.assertEqual(runner.outcome(text,0,cls,method), 'failed')

    def test_reviewed_allowlist_is_bounded_and_unique(self):
        self.assertEqual(len(runner.CASES), 7)
        self.assertEqual(len({(c,m) for c,m,_ in runner.CASES}), 7)
        self.assertEqual(len({f for _,_,f in runner.CASES}), 7)
        self.assertIn('(deny network*)', runner.SANDBOX)

    def test_trace_module_selection(self):
        cls, method, _ = runner.TRACE_CASES[0]
        name = f'-[OathDiagnosticsTests.{cls} {method}]'
        text = f"Test Case '{name}' started.\nTest Case '{name}' passed (0.1 seconds).\n"
        self.assertEqual(runner.outcome(text,0,cls,method,'OathDiagnostics'), 'passed')
        self.assertEqual(runner.outcome(text,0,cls,method,'OathAnkr'), 'failed')
