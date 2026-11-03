import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
def sha(raw):return hashlib.sha256(raw).hexdigest()
class StellarDecodingEvidence(unittest.TestCase):
    def test_corpus_reproduces_with_independent_stdlib_generator(self):
        spec=importlib.util.spec_from_file_location('stellar_vectors',ROOT/'scripts/stellar-decoding-vectors.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        raw=(ROOT/'fixtures/stellar-decoding/vectors.json').read_text();v=json.loads(raw)
        self.assertEqual(raw,json.dumps(mod.generate(),sort_keys=True,indent=2)+'\n')
        self.assertEqual(v['seed'],'oath-stellar-decoding-v1')
        self.assertEqual([len(v[k]) for k in ['addresses','contracts','amounts','maps','events','malformed']],[64,128,128,72,12,256])
        self.assertEqual(len({r['account'] for r in v['addresses']}),64)
        self.assertEqual(len({r['contract'] for r in v['contracts']}),128)
        for r in v['amounts']:
            self.assertEqual(int.from_bytes(base64.b64decode(r['xdr'])[4:],'big',signed=True),int(r['integer']))
            self.assertEqual(int.from_bytes(base64.b64decode(r['negative_xdr'])[4:],'big',signed=True),int(r['negative']))
        generator=(ROOT/'scripts/stellar-decoding-vectors.py').read_text()
        self.assertNotIn('subprocess',generator);self.assertNotIn('OathAnkr',generator)

    def test_replay_executes_production_parser_and_checks_every_selected_method(self):
        folder=ROOT/'evidence/5.0.2-build104/stellar-decoding'
        with zipfile.ZipFile(folder/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
            for r in checks:self.assertEqual(sha(z.read(r['path'])),r['sha256'])
            r=json.loads(z.read('result.json'))
            self.assertEqual(r['source_commit'],PIN);self.assertEqual(len(r['methods']),7)
            self.assertEqual(len({m['method'] for m in r['methods']}),7)
            for name,key in [('scripts/stellar-decoding-review.py','driver_sha256'),('scripts/stellar-decoding-vectors.py','generator_sha256'),('fixtures/stellar-decoding/vectors.json','vectors_sha256'),('fixtures/stellar-decoding/StellarDecodingReviewTests.swift','overlay_sha256')]:
                self.assertEqual(sha((ROOT/name).read_bytes()),r[key])
            self.assertEqual(r['sdk_commit'],'b5dac0a6e8ff312d597c9a3b4269b03131d66e0d')
            for f in r['files']:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            for m in r['methods']:
                self.assertEqual(m['status'],'passed');self.assertEqual(m['exit_code'],0)
                raw=z.read(m['log']);self.assertEqual(sha(raw),m['log_sha256']);self.assertIn(b'Executed 1 test',raw)

    def test_negative_control_fails_and_restores_source(self):
        with zipfile.ZipFile(ROOT/'evidence/5.0.2-build104/stellar-decoding/mutation.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            for row in checks:self.assertEqual(sha(z.read(row['path'])),row['sha256'])
            r=json.loads(z.read('result.json'))
            self.assertEqual(r['source_commit'],PIN);self.assertEqual(r['exit_code'],1)
            self.assertEqual(r['status'],'failed');self.assertTrue(r['tracked_source_restored'])
            self.assertEqual(r['observed_checksum_assertion_failures'],64)
            self.assertNotEqual(r['original_sha256'],r['mutated_sha256'])
            self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/stellar-decoding-mutation.py').read_bytes()))
            for f in r['files']:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            self.assertEqual(z.read('mutation.log').count(b'XCTAssertThrowsError failed: did not throw an error'),64)
            self.assertIn(b'Executed 1 test, with 64 failures',z.read('mutation.log'))

    def test_source_dispositions_remain_partial(self):
        folder=ROOT/'evidence/5.0.2-build104/stellar-decoding'
        manifest=json.loads((folder/'manifest.json').read_text())
        self.assertEqual(manifest['source_commit'],PIN)
        self.assertEqual(manifest['passed_methods'],7)
        self.assertFalse(manifest['application_changed']);self.assertFalse(manifest['whole_wallet_complete'])
        for row in manifest['files']:self.assertEqual(sha((folder/row['path']).read_bytes()),row['sha256'])
        rows=json.loads((ROOT/'evidence/5.0.2-build104/stellar-decoding/source-binding.json').read_text())['files']
        inventory={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(len(rows),2)
        for row in rows:
            self.assertEqual(row['sha256'],inventory[row['path']]['sha256'])
            self.assertEqual(row['status'],'partially-reviewed');self.assertTrue(row['baseline_identical'])
            self.assertEqual(inventory[row['path']]['status'],'partially-reviewed')
            self.assertIn('review/STELLAR-DECODING.md',inventory[row['path']]['evidence'])

    def test_execution_boundaries_and_report_limits(self):
        driver=(ROOT/'scripts/stellar-decoding-review.py').read_text()
        for phrase in ['Fresh scratch/output required','require_source_state(source,PIN)','(deny network*)','Unexpected overlay files','SDK source pin or state mismatch']:
            self.assertIn(phrase,driver)
        workflow=(ROOT/'.github/workflows/stellar-decoding.yml').read_text()
        self.assertIn(PIN,workflow);self.assertIn('contents: read',workflow)
        self.assertNotIn('pull_request',workflow);self.assertNotIn('secrets.',workflow)
        report=(ROOT/'review/STELLAR-DECODING.md').read_text()
        for phrase in ['whole-wallet audit remains incomplete','No new confirmed defect','not independent certification','No new generic iOS build']:
            self.assertIn(phrase,report)
