import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from go_advisory_triage import classify

class GoAdvisoryTriageTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {'source_commit': 'fixture', 'module_graph': {'module': 'v1'}, 'targets': [
            {'target': t, 'packages': [{'import_path': 'module/used'}]} for t in ['mac', 'ios', 'sim']]}
        self.advisory = {'id': 'GO-TEST', 'affected': [{'package': {'name': 'module'},
            'ecosystem_specific': {'imports': [{'path': 'module/unused'}]}}]}
    def scan(self, *advisories):
        return {'results': [{'packages': [{'package': {'name': 'module', 'version': '1'},
                                          'vulnerabilities': list(advisories)}]}]}
    def test_uncompiled_has_explicit_package_evidence(self):
        result = classify(self.scan(self.advisory), self.inventory)
        self.assertEqual(result['unresolved'], 0)
        self.assertFalse(result['binary_clearance'])
        self.assertEqual(result['advisories'][0]['status'], 'not-compiled')
    def test_single_target_reachability_blocks(self):
        self.inventory['targets'][1]['packages'].append({'import_path': 'module/unused'})
        result = classify(self.scan(self.advisory), self.inventory)
        self.assertEqual(result['unresolved'], 1)
        self.assertEqual(result['advisories'][0]['selected_intersections']['ios'], ['module/unused'])
    def test_missing_metadata_is_not_clearance(self):
        self.advisory['affected'][0].pop('ecosystem_specific')
        self.assertEqual(classify(self.scan(self.advisory), self.inventory)['unresolved'], 1)
    def test_explicit_go_alias_resolves_package_metadata(self):
        alias = {'id': 'GHSA-TEST', 'aliases': ['GO-TEST'], 'affected': [{'package': {'name': 'module'}}]}
        result = classify(self.scan(self.advisory, alias), self.inventory)
        self.assertEqual(result['unresolved'], 0)
        self.assertEqual(result['advisories'][1]['metadata_evidence_ids'], ['GO-TEST'])
    def test_unrelated_module_alias_cannot_clear(self):
        alias = {'id': 'GHSA-TEST', 'aliases': ['GO-TEST'], 'affected': []}
        self.advisory['affected'][0]['package']['name'] = 'different-module'
        self.assertEqual(classify(self.scan(self.advisory, alias), self.inventory)['unresolved'], 2)
    def test_missing_or_empty_target_rejected(self):
        empty = copy.deepcopy(self.inventory); empty['targets'][0]['packages'] = []
        for candidate in [empty, {'targets': self.inventory['targets'][:2]}]:
            with self.assertRaises(ValueError): classify(self.scan(self.advisory), candidate)
    def test_different_version_cannot_clear_advisory(self):
        self.inventory['module_graph']['module'] = 'v2'
        with self.assertRaises(ValueError): classify(self.scan(self.advisory), self.inventory)
    def test_empty_scan_is_not_a_claim_of_triaged_advisories(self):
        with self.assertRaises(ValueError): classify({}, self.inventory)
