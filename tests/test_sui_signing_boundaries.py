import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BEFORE='b3f1f6af98bedfe850d390cac684a563c598e3ac'
AFTER='018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0'
def sha(b):return hashlib.sha256(b).hexdigest()

class SuiSigningEvidence(unittest.TestCase):
    def test_paired_slice_failures_and_signing_results(self):
        root=ROOT/'evidence/5.0.2-build104/sui-signing-boundaries'
        manifest=json.loads((root/'manifest.json').read_text())
        self.assertEqual(manifest['before_commit'],BEFORE);self.assertEqual(manifest['repair_commit'],AFTER)
        for f in manifest['files']:self.assertEqual(sha((root/f['path']).read_bytes()),f['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{f['path'] for f in checks}|{'CHECKSUMS.json'})
            for f in checks:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            for mode,pin,codes in [('before',BEFORE,[0,-5,-5]),('after',AFTER,[0,0,0])]:
                r=json.loads(z.read(mode+'/result.json'));self.assertEqual(r['source_commit'],pin)
                self.assertEqual(r['source_sha256'],r['executed_sha256'])
                self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/sui-transaction-slices.py').read_bytes()))
                self.assertEqual(r['overlay_sha256'],sha((ROOT/'fixtures/sui-signing-boundaries/SuiAuditSliceTests.swift').read_bytes()))
                self.assertEqual([t['exit_code'] for t in r['methods']],codes)
                for t in r['methods']:
                    raw=z.read(mode+'/'+t['log']);self.assertEqual(sha(raw),t['log_sha256']);self.assertIn(b'Test Case ',raw)
                    if t['exit_code']==0:self.assertIn(b'Executed 1 test',raw);self.assertEqual(t['status'],'passed')
                for f in r['files']:self.assertEqual(sha(z.read(mode+'/'+f['path'])),f['sha256'])
            for mode,pin,count in [('initial-signing',BEFORE,21),('signing',AFTER,34)]:
                r=json.loads(z.read(mode+'/result.json'));self.assertEqual(r['source_commit'],pin)
                driver=z.read(mode+'/executed-driver.py') if mode=='initial-signing' else (ROOT/'scripts/sui-signing-boundaries.py').read_bytes()
                self.assertEqual(r['driver_sha256'],sha(driver));self.assertEqual(r['vectors'],336)
                self.assertEqual(r['overlay_sha256'],sha((ROOT/'fixtures/sui-signing-boundaries/SuiAuditSigningBoundaryTests.swift').read_bytes()))
                self.assertEqual(len(r['methods']),count);self.assertEqual(len(r['live_methods_excluded']),3)
                for t in r['methods']:
                    self.assertEqual(t['status'],'passed');self.assertEqual(t['exit_code'],0)
                    raw=z.read(mode+'/'+t['log']);self.assertEqual(sha(raw),t['log_sha256']);self.assertIn(b'Executed 1 test',raw)
                for f in r['source_files']:self.assertEqual(f['source_sha256'],f['executed_sha256'])
                for f in r['files']:self.assertEqual(sha(z.read(mode+'/'+f['path'])),f['sha256'])

    def test_independent_vectors_are_deterministic(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location('sui_signing_vectors',ROOT/'scripts/sui-signing-boundaries.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        vectors=module.vectors();self.assertEqual(len(vectors),336);self.assertEqual(vectors,module.vectors())
        self.assertEqual({v['length'] for v in vectors},{1,16,32,64})
        for v in vectors:
            if v['input']=='' and v['length']==32:self.assertEqual(v['hash'],'0e5751c026e543b2e8ab2eb06099daa1d1e5df47778f7787faab45cdf12fe3a8')
        with zipfile.ZipFile(ROOT/'evidence/5.0.2-build104/sui-signing-boundaries/runs.zip') as z:
            self.assertEqual(vectors,json.loads(z.read('signing/vectors.json')))

    def test_workflow_does_not_run_outside_contributions_or_use_secrets(self):
        text=(ROOT/'.github/workflows/sui-signing-boundaries.yml').read_text()
        self.assertIn(BEFORE,text);self.assertIn(AFTER,text);self.assertIn('contents: read',text)
        self.assertNotIn('pull_request',text);self.assertNotIn('secrets.',text)
        for name in ['sui-signing-boundaries.py','sui-transaction-slices.py']:
            s=(ROOT/'scripts'/name).read_text()
            self.assertIn('(deny network*)',s);self.assertIn('require_source_state',s);self.assertIn("'--build-tests'",s)

    def test_partial_source_scope_is_hash_bound(self):
        rows=json.loads((ROOT/'evidence/5.0.2-build104/sui-signing-boundaries/source-binding.json').read_text())['files']
        inventory={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(len(rows),10)
        for r in rows:
            self.assertTrue(r['baseline_identical']);self.assertEqual(r['sha256'],inventory[r['path']]['sha256'])
            self.assertEqual(r['status'],'partially-reviewed');self.assertIn('review/SUI-SIGNING-BOUNDARIES.md',inventory[r['path']]['evidence'])
