"""Receipt integrity only; the Swift executable is run by the separate replay."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/5.0.1-build103/xrpl-amounts'
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('xrpl_evidence',ROOT/'scripts/xrpl-amount-properties.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class XRPAmountEvidenceTests(unittest.TestCase):
    def test_same_cases_and_exact_before_after_outcomes(self):
        fixture=json.dumps(r.vectors(),separators=(',',':')).encode()
        for folder,commit,failures in [('before-replay',r.BASE,r.BASE_FAILURES),('after-replay',r.COMMIT,[])]:
            result=json.loads((E/folder/'result.json').read_text())
            self.assertEqual(result['source_commit'],commit)
            self.assertEqual(gzip.decompress((E/folder/'vectors.json.gz').read_bytes()),fixture)
            self.assertEqual(result['fixture_sha256'],hashlib.sha256(fixture).hexdigest())
            self.assertEqual(result['script_sha256'],hashlib.sha256((ROOT/'scripts/xrpl-amount-properties.py').read_bytes()).hexdigest())
            output=gzip.decompress((E/folder/'output.json.gz').read_bytes())
            self.assertEqual(result['output_sha256'],hashlib.sha256(output).hexdigest())
            self.assertEqual(len(json.loads(output)),4900)
            self.assertEqual([f['index'] for f in result['failures']],failures)
            self.assertEqual((result['passed'],result['failed']),(4900-len(failures),len(failures)))
    def test_package_skips_and_isolated_retest_remain_visible(self):
        cases=json.loads((E/'package-tests/OathAnkr-cases.json').read_text())
        self.assertEqual((len(cases),sum(c['status']=='passed' for c in cases),sum(c['status']=='skipped' for c in cases)),(32,29,3))
        isolated=json.loads((E/'preparation-diagnostics/OathAnkr-cases.json').read_text())
        self.assertEqual(len(isolated),1);self.assertEqual(isolated[0]['status'],'passed')
        self.assertIn(isolated[0]['selector'],[c['selector'] for c in cases if c['status']=='skipped'])
        for folder in ['package-tests','preparation-diagnostics','validation']:
            name='OathDiagnostics' if folder=='validation' else 'OathAnkr'
            for c in json.loads((E/folder/(name+'-cases.json')).read_text()):
                raw=gzip.decompress((E/folder/(c['log']+'.gz')).read_bytes())
                self.assertEqual(c['log_sha256'],hashlib.sha256(raw).hexdigest())
    def test_validation_is_bound_to_tested_revision(self):
        for check in ['build','public','diagnostics-coverage','OathDiagnostics']:
            receipt=json.loads((E/'validation'/(check+'.json')).read_text())
            self.assertEqual(receipt['source_commit'],r.COMMIT)
            self.assertEqual(receipt['status'],'passed')
            self.assertEqual(receipt['exit_code'],0)
            raw=gzip.decompress((E/'validation'/(check+'.log.gz')).read_bytes())
            self.assertEqual(receipt['log_sha256'],hashlib.sha256(raw).hexdigest())
        merge=json.loads((E/'merge.json').read_text())
        self.assertEqual(merge['tested_commit'],r.COMMIT)
        self.assertEqual(len(merge['files_different']),91)
        self.assertTrue(all(p.startswith('Website/') for p in merge['files_different']))
    def test_manifest_and_partial_coverage(self):
        manifest=json.loads((E/'manifest.json').read_text())
        for name,meta in manifest['files'].items():
            raw=(E/name).read_bytes()
            self.assertEqual(meta['bytes'],len(raw))
            self.assertEqual(meta['sha256'],hashlib.sha256(raw).hexdigest())
        ledger={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        for row in json.loads((E/'source.json').read_text())['files']:
            self.assertEqual(row['sha256'],ledger[row['path']]['sha256'])
            self.assertEqual(ledger[row['path']]['status'],'partially-reviewed')

if __name__=='__main__':unittest.main()
