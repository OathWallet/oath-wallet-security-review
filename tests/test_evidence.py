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
        self.assertIn('OW-1',module.gaps({'reviewed_commit':'a'},{'source_commit':'a','files':[]},[{'id':'OW-1','status':'open'}]))

    def test_stale_passing_test_does_not_validate_current_commit(self):
        result = module.gaps({'reviewed_commit':'b','required_checks':['build']},
            {'source_commit':'b','files':[]},[],[{'check':'build','source_commit':'a','status':'passed','log_sha256':'hash'}])
        self.assertIn('required validation: build',result)

    def test_partial_review_remains_a_gap(self):
        result = module.gaps({'reviewed_commit':'a'},
            {'source_commit':'a','files':[{'path':'vault.swift','category':'application','status':'partially-reviewed'}]},[])
        self.assertIn('vault.swift',result)

    def test_green_app_does_not_clear_unreviewed_dependency(self):
        result = module.gaps({'reviewed_commit':'a'},
            {'source_commit':'a','files':[{'path':'vault.swift','category':'application','status':'reviewed'}]}, [], [],
            [{'repository':'upstream','files':[{'path':'sign.cpp','status':'outstanding'}]}])
        self.assertIn('upstream: sign.cpp',result)
