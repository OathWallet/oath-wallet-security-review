import importlib.util
import unittest
from pathlib import Path
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('completion',root/'scripts/completion.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EvidenceTests(unittest.TestCase):
    def test_green_tests_cannot_clear_outstanding_source(self):
        inventory = {'source_commit':'a','files':[{'path':'vault.swift','category':'application','status':'outstanding'}]}
        self.assertEqual(module.gaps({'reviewed_commit':'a'},inventory,[]),['vault.swift'])

    def test_revision_mismatch_invalidates_completion(self):
        self.assertIn('source mismatch',module.gaps({'reviewed_commit':'b'},{'source_commit':'a','files':[]},[]))

    def test_unresolved_finding_remains_visible(self):
        self.assertEqual(module.gaps({'reviewed_commit':'a'},{'source_commit':'a','files':[]},[{'id':'OW-1','status':'open'}]),['OW-1'])
