import hashlib
import json
from pathlib import Path
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
EVIDENCE=ROOT/'evidence/5.0.2-build104/stellar-provider'
def sha(raw):return hashlib.sha256(raw).hexdigest()
class StellarProviderEvidence(unittest.TestCase):
    def archive(self,name):
        z=zipfile.ZipFile(EVIDENCE/name);self.addCleanup(z.close)
        checks=json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
        for row in checks:self.assertEqual(sha(z.read(row['path'])),row['sha256'])
        result=json.loads(z.read('result.json'))
        self.assertEqual(result['source_commit'],PIN)
        for row in result['files']:self.assertEqual(sha(z.read(row['path'])),row['sha256'])
        return z,result
    def test_all_selected_production_methods_ran(self):
        z,r=self.archive('runs.zip')
        self.assertEqual(len(r['methods']),12)
        self.assertEqual(len({m['method'] for m in r['methods']}),12)
        self.assertEqual(sum(m['suite']=='StellarProviderReviewTests' for m in r['methods']),4)
        self.assertEqual(r['sdk_commit'],'b5dac0a6e8ff312d597c9a3b4269b03131d66e0d')
        for path,key in [('scripts/stellar-provider-review.py','driver_sha256'),('fixtures/stellar-provider/StellarProviderReviewTests.swift','overlay_sha256')]:
            self.assertEqual(sha((ROOT/path).read_bytes()),r[key])
        for m in r['methods']:
            self.assertEqual(m['status'],'passed');self.assertEqual(m['exit_code'],0)
            raw=z.read(m['log']);self.assertEqual(sha(raw),m['log_sha256'])
            self.assertIn(b'Executed 1 test, with 0 failures',raw)
    def test_negative_control_rebuild_and_restore(self):
        z,r=self.archive('mutation.zip')
        self.assertEqual(r['status'],'failed');self.assertEqual(r['exit_code'],1)
        self.assertEqual(r['observed_authorization_assertion_failures'],1)
        self.assertTrue(r['tracked_source_restored'])
        self.assertNotEqual(r['original_sha256'],r['mutated_sha256'])
        self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/stellar-provider-mutation.py').read_bytes()))
        self.assertEqual(z.read('mutation.log').count(b'failed - Accepted changedAuthorization'),1)
        self.assertIn(b'Executed 1 test, with 1 failure',z.read('mutation.log'))
        _,before=self.archive('runs.zip')
        self.assertNotEqual(r['test_executable_sha256'],before['test_executable_sha256'])
    def test_partial_read_scope_preserved(self):
        binding=json.loads((EVIDENCE/'source-binding.json').read_text())
        self.assertEqual(binding['reviewed_commit'],PIN);self.assertEqual(len(binding['files']),3)
        inventory={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        for row in binding['files']:
            self.assertTrue(row['baseline_identical']);self.assertEqual(row['status'],'partially-reviewed')
            self.assertEqual(row['sha256'],inventory[row['path']]['sha256'])
            self.assertEqual(inventory[row['path']]['status'],'partially-reviewed')
            self.assertIn('review/STELLAR-PROVIDER.md',inventory[row['path']]['evidence'])
    def test_manifest_does_not_claim_an_app_fix(self):
        r=json.loads((EVIDENCE/'manifest.json').read_text())
        self.assertEqual(r['source_commit'],PIN);self.assertEqual(r['passed_methods'],12)
        self.assertFalse(r['application_changed']);self.assertFalse(r['whole_wallet_complete'])
        self.assertFalse(r['new_ios_build_performed'])
        for row in r['files']:self.assertEqual(sha((EVIDENCE/row['path']).read_bytes()),row['sha256'])
    def test_failed_fixture_attempt_is_retained_separately(self):
        z,r=self.archive('attempt1.zip')
        self.assertEqual(r['status'],'fixture-build-failed');self.assertEqual(r['executed_tests'],0)
        self.assertIn(b"error: type 'Data' has no member 'init(base64Encoded:)'",z.read('build.log'))
        self.assertNotEqual(sha(z.read('StellarProviderReviewTests.swift')),sha((ROOT/'fixtures/stellar-provider/StellarProviderReviewTests.swift').read_bytes()))
    def test_hosted_replays_are_pinned_and_hash_verified(self):
        for name,id,head,count,field,failures in [('decoding',41742064900,'0912368d2ca979cd873dad19acd97229000733e4',7,'checksum',64),('multisig',41743870642,'ce39c04c1ec70201f80b9c7f259e8e67ae398a70',10,'threshold',627)]:
            p=ROOT/f'evidence/5.0.2-build104/hosted-stellar-{name}'
            run=json.loads((p/'run.json').read_text());a=json.loads((p/'artifact.json').read_text())
            self.assertEqual((run['id'],run['head_sha'],run['conclusion']),(id,head,'success'))
            self.assertEqual(a['digest'],'sha256:'+sha((p/'artifact.zip').read_bytes()))
            with zipfile.ZipFile(p/'artifact.zip') as z:
                b=json.loads(z.read('baseline/result.json'));m=json.loads(z.read('mutation/result.json'))
                for folder,r in [('baseline',b),('mutation',m)]:
                    self.assertEqual(r['source_commit'],PIN)
                    for f in r['files']:self.assertEqual(sha(z.read(folder+'/'+f['path'])),f['sha256'])
                self.assertEqual(len(b['methods']),count)
                for c in b['methods']:
                    self.assertEqual(c['status'],'passed');self.assertEqual(c['exit_code'],0)
                    self.assertEqual(sha(z.read('baseline/'+c['log'])),c['log_sha256'])
                self.assertEqual(m['exit_code'],1);self.assertEqual(m['status'],'failed')
                self.assertEqual(m[f'observed_{field}_assertion_failures'],failures)
                self.assertTrue(m['tracked_source_restored'])
                self.assertNotEqual(b['test_executable_sha256'],m['test_executable_sha256'])
    def test_execution_boundaries(self):
        driver=(ROOT/'scripts/stellar-provider-review.py').read_text()
        for phrase in ['Fresh scratch/output required','require_source_state(source,PIN)','(deny network*)','SDK source pin or state mismatch','Unexpected overlay files']:
            self.assertIn(phrase,driver)
        w=(ROOT/'.github/workflows/stellar-provider.yml').read_text()
        self.assertIn('contents: read',w);self.assertIn(PIN,w);self.assertNotIn('pull_request',w);self.assertNotIn('secrets.',w)
        self.assertIn('test_stellar_provider_review.py',w)
        report=(ROOT/'review/STELLAR-PROVIDER.md').read_text()
        for phrase in ['whole-wallet audit remains incomplete','No new confirmed defect','not independent certification','No new generic iOS build']:
            self.assertIn(phrase,report)
