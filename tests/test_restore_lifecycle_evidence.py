"""Verify published source/fixture/log bindings; these are not new runtime tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
E = ROOT/'evidence/5.0.1-build103/restore-lifecycle'
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('restore_evidence',ROOT/'scripts/cloud-restore-lifecycle.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

class RestoreEvidenceTests(unittest.TestCase):
    def test_production_and_mutation_results_are_distinct(self):
        for folder,mutant in [('production',False),('mutation',True)]:
            result=json.loads((E/folder/'result.json').read_text())
            self.assertEqual(result['source_commit'],r.COMMIT)
            self.assertEqual(result['deliberate_mutation'],mutant)
            self.assertEqual(result['fixture_sha256'],sha(ROOT/'fixtures/cloud-restore-lifecycle/Checks.swift'))
            self.assertEqual(result['script_sha256'],sha(ROOT/'scripts/cloud-restore-lifecycle.py'))
            self.assertEqual(result['log_sha256'],sha(E/folder/'checks.log'))
            cases=r.validate(result['exit_code'],(E/folder/'checks.log').read_text(),mutant)
            self.assertEqual(result['cases'],[dict(name=n,status=s.lower()) for s,n in cases])
    def test_coverage_remains_partial_and_hash_bound(self):
        source=json.loads((E/'source.json').read_text())
        ledger={v['path']:v for v in json.loads((ROOT/'scope/history/5.0.1-build103/inventory.json').read_text())['files']}
        self.assertEqual(len(source['files']),4)
        for entry in source['files']:
            self.assertEqual(entry['sha256'],ledger[entry['path']]['sha256'])
            self.assertEqual(entry['read_ranges'],[[1,entry['line_count']]])
            self.assertEqual(ledger[entry['path']]['status'],'partially-reviewed')
    def test_mutation_does_not_change_original_identity(self):
        production=json.loads((E/'production/result.json').read_text())
        mutation=json.loads((E/'mutation/result.json').read_text())
        self.assertEqual(production['source_sha256'],mutation['source_sha256'])
        self.assertNotEqual(production['compiled_model_sha256'],mutation['compiled_model_sha256'])
        source=json.loads((E/'source.json').read_text())
        self.assertEqual(production['source_sha256'],next(v['sha256'] for v in source['files'] if v['path']==r.MODEL))

if __name__=='__main__': unittest.main()
