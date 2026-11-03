import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0'
AFTER = '2f914715224db31e91f1ce1f0dea4c236c043920'
def sha(raw): return hashlib.sha256(raw).hexdigest()

class XDRScaleEvidence(unittest.TestCase):
    def test_paired_crashes_and_adjacent_results(self):
        root = ROOT / 'evidence/5.0.2-build104/xdr-scale-buffers'
        with zipfile.ZipFile(root / 'runs.zip') as z:
            files = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()), {f['path'] for f in files} | {'CHECKSUMS.json'})
            for f in files: self.assertEqual(sha(z.read(f['path'])), f['sha256'])
            for mode,pin,codes in [('before',BEFORE,[0,-5,-5,-5,0,-5,-5,0,-5]),('after',AFTER,[0]*9)]:
                r = json.loads(z.read(mode + '/result.json'))
                self.assertEqual(r['source_commit'],pin)
                self.assertEqual([t['exit_code'] for t in r['methods']],codes)
                self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/xdr-scale-buffers.py').read_bytes()))
                self.assertEqual(r['overlay_sha256'],sha((ROOT/'fixtures/xdr-scale-buffers/TransactionBufferTests.swift').read_bytes()))
                for f in r['production']: self.assertEqual(f['source_sha256'],f['executed_sha256'])
                for t in r['methods']:
                    log = z.read(mode + '/' + t['log'])
                    self.assertEqual(sha(log), t['log_sha256'])
                    if t['exit_code'] == 0:
                        self.assertEqual(t['status'],'passed');self.assertIn(b'Executed 1 test',log)
                for f in r['files']: self.assertEqual(sha(z.read(mode + '/' + f['path'])),f['sha256'])
            r = json.loads(z.read('adjacent/result.json'))
            self.assertEqual(r['source_commit'],AFTER);self.assertEqual(r['passed'],40)
            self.assertEqual(r['script_sha256'],sha((ROOT/'scripts/xdr-scale-regressions.py').read_bytes()))
            self.assertEqual(r['isolation_driver_sha256'],sha((ROOT/'scripts/isolated_tests.py').read_bytes()))
            for f in r['files']: self.assertEqual(sha(z.read('adjacent/' + f['path'])),f['sha256'])
            rows = json.loads(z.read('adjacent/OathAnkr-cases.json'))
            self.assertEqual(len(rows),40);self.assertEqual(len({r['selector'] for r in rows}),40)
            for row in rows:
                self.assertEqual(row['status'],'passed');self.assertEqual(row['exit_code'],0)
                self.assertNotIn('/testLive',row['selector'])
                self.assertEqual(sha(z.read('adjacent/'+row['log'])),row['log_sha256'])

    def test_regression_selection_rejects_empty_duplicate_skipped_and_failed(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location('xdr_scale_regressions',ROOT/'scripts/xdr-scale-regressions.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        expected=[f'Suite/test{i}' for i in range(40)]
        rows=[{'selector':n,'status':'passed','exit_code':0} for n in expected]
        module.validate_results(rows,expected)
        for invalid in [[],rows[:-1],rows[:-1]+[rows[0]],rows[:-1]+[dict(rows[-1],status='skipped')],rows[:-1]+[dict(rows[-1],exit_code=1)]]:
            with self.assertRaises(ValueError): module.validate_results(invalid,expected)

    def test_scope_is_partial_and_hash_bound(self):
        rows=json.loads((ROOT/'evidence/5.0.2-build104/xdr-scale-buffers/source-binding.json').read_text())['files']
        inv={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(len(rows),4)
        for r in rows:
            self.assertTrue(r['baseline_identical']);self.assertEqual(r['status'],'partially-reviewed')
            self.assertEqual(r['sha256'],inv[r['path']]['sha256'])
            self.assertIn('review/XDR-SCALE-BUFFERS.md',inv[r['path']]['evidence'])

    def test_workflow_pins_and_network_boundary(self):
        text=(ROOT/'.github/workflows/xdr-scale-buffers.yml').read_text()
        self.assertIn(BEFORE,text);self.assertIn(AFTER,text);self.assertIn('contents: read',text)
        self.assertNotIn('pull_request',text);self.assertNotIn('secrets.',text)
        for name in ['xdr-scale-buffers.py','xdr-scale-regressions.py']:
            source=(ROOT/'scripts'/name).read_text()
            self.assertIn('(deny network*)',source);self.assertIn('require_source_state',source)
            self.assertIn("'--build-tests'",source)

    def test_validation_and_merge_are_bound_to_repair(self):
        root=ROOT/'evidence/5.0.2-build104/xdr-scale-buffers'
        m=json.loads((root/'manifest.json').read_text())
        self.assertEqual(m['before_commit'],BEFORE);self.assertEqual(m['repair_commit'],AFTER)
        for f in m['files']:self.assertEqual(sha((root/f['path']).read_bytes()),f['sha256'])
        binding=json.loads((root/'validation/merge-binding.json').read_text())
        self.assertEqual(binding['repair_commit'],AFTER);self.assertTrue(binding['complete_trees_equal'])
        self.assertEqual(binding['merge_commit'],m['merge_commit'])
        self.assertEqual(json.loads((root/'validation/ios-build-result.json').read_text())['exit_code'],0)
        self.assertIn('** BUILD SUCCEEDED **',(root/'validation/ios-build.log').read_text())
        self.assertEqual(json.loads((root/'validation/diagnostics-result.json').read_text())['exit_code'],0)
        self.assertIn('Executed 121 tests, with 2 tests skipped and 0 failures',(root/'validation/diagnostics-tests.log').read_text())
