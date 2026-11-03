"""Prevent replay scope or source-identity drift; no claim of Swift runtime here."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('signing_matrix',ROOT/'scripts/xrpl-signing-vectors.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class XRPReplayContractTests(unittest.TestCase):
    def test_only_exact_expected_methods(self):
        self.assertEqual(len(r.METHODS),4)
        self.assertEqual(len(set(r.METHODS)),4)
        fixture=(ROOT/'fixtures/xrpl-signing/XrplAuditSigningTests.swift').read_text()
        for method in r.METHODS:self.assertEqual(fixture.count('func '+method+'('),1)
    def test_replay_uses_pinned_clean_public_source_and_no_live_flags(self):
        self.assertEqual(r.COMMIT,'6783750661c43d3511d8973a2de77106fdf2001d')
        source=(ROOT/'scripts/xrpl-signing-vectors.py').read_text()
        self.assertEqual(source.count('require_source_state(source,COMMIT)'),2)
        self.assertIn('--ignore-scripts',source)
        self.assertEqual(source.count('(deny network*)'),2)
        self.assertNotIn('OATH_XRPL_TESTNET_FIXTURE',source)
        self.assertIn("if changed:raise ValueError",source)
if __name__=='__main__':unittest.main()
