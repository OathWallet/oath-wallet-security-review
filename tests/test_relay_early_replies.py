import importlib.util
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec = importlib.util.spec_from_file_location('early_replies',scripts/'relay-early-replies.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class EarlyReplyEvidenceTests(unittest.TestCase):
    def transcript(self, before):
        lines = []
        for case in sorted(runner.EARLY | runner.CONTROLS):
            name = f'-[SDKTests.{runner.SUITE} {case}]'
            lines.append(f"Test Case '{name}' started.")
            fails = before and case in runner.EARLY
            if fails: lines.append(f'file.swift:50: error: {name} : {runner.MESSAGE}')
            lines.append(f"Test Case '{name}' {'failed' if fails else 'passed'} (0.5 seconds).")
        return '\n'.join(lines)

    def test_before_and_after_require_their_own_outcomes(self):
        for before in [True,False]:
            text = self.transcript(before)
            self.assertTrue(runner.verify(text,int(before),before))
            self.assertFalse(runner.verify(text,int(not before),before))
            self.assertFalse(runner.verify(text,int(before),not before))

    def test_missing_duplicate_and_unrelated_failures_rejected(self):
        text = self.transcript(True)
        for bad in [text.replace(runner.MESSAGE,'unrelated',1), text+'\n'+text,
                    text.replace(' passed (',' skipped (',1), text+'\nFatal error: trap',
                    '\n'.join(text.splitlines()[1:])]:
            self.assertFalse(runner.verify(bad,1,True))
