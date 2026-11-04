import hashlib
import json
from pathlib import Path
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
EVIDENCE=ROOT/'evidence/5.0.2-build104/stellar-multisig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
class StellarMultisigEvidence(unittest.TestCase):
    def archive(self,name):
        z=zipfile.ZipFile(EVIDENCE/name);self.addCleanup(z.close)
        checks=json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
        for row in checks:self.assertEqual(sha(z.read(row['path'])),row['sha256'])
        result=json.loads(z.read('result.json'))
        self.assertEqual(result['source_commit'],PIN)
        for row in result['files']:self.assertEqual(sha(z.read(row['path'])),row['sha256'])
        return z,result
    def test_actual_production_execution_and_all_selected_methods(self):
        z,r=self.archive('runs.zip')
        self.assertEqual(len(r['methods']),10)
        self.assertEqual(len({m['method'] for m in r['methods']}),10)
        self.assertEqual(sum(m['suite']=='StellarMultisigReviewTests' for m in r['methods']),6)
        self.assertEqual(r['sdk_commit'],'b5dac0a6e8ff312d597c9a3b4269b03131d66e0d')
        for path,key in [('scripts/stellar-multisig-review.py','driver_sha256'),('fixtures/stellar-multisig/StellarMultisigReviewTests.swift','overlay_sha256')]:
            self.assertEqual(sha((ROOT/path).read_bytes()),r[key])
        for method in r['methods']:
            self.assertEqual(method['status'],'passed');self.assertEqual(method['exit_code'],0)
            raw=z.read(method['log']);self.assertEqual(sha(raw),method['log_sha256'])
            self.assertIn(b'Executed 1 test, with 0 failures',raw)
    def test_negative_control_rebuild_fails_and_restores_source(self):
        z,r=self.archive('mutation.zip')
        self.assertEqual(r['exit_code'],1);self.assertEqual(r['status'],'failed')
        self.assertEqual(r['observed_threshold_assertion_failures'],627)
        self.assertTrue(r['tracked_source_restored']);self.assertNotEqual(r['original_sha256'],r['mutated_sha256'])
        self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/stellar-multisig-mutation.py').read_bytes()))
        self.assertEqual(z.read('mutation.log').count(b'XCTAssertFalse failed - lower threshold must be rejected'),627)
        self.assertIn(b'Executed 1 test, with 627 failures',z.read('mutation.log'))
        _,before=self.archive('runs.zip')
        self.assertNotEqual(r['test_executable_sha256'],before['test_executable_sha256'])
    def test_scope_retains_partial_review_and_source_binding(self):
        binding=json.loads((EVIDENCE/'source-binding.json').read_text())
        self.assertEqual(binding['reviewed_commit'],PIN);self.assertEqual(len(binding['files']),3)
        inventory={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        for row in binding['files']:
            self.assertTrue(row['baseline_identical']);self.assertEqual(row['status'],'partially-reviewed')
            self.assertEqual(row['sha256'],inventory[row['path']]['sha256'])
            self.assertEqual(inventory[row['path']]['status'],'partially-reviewed')
            self.assertIn('review/STELLAR-MULTISIG.md',inventory[row['path']]['evidence'])
    def test_manifest_hashes_and_no_application_change_claim(self):
        r=json.loads((EVIDENCE/'manifest.json').read_text())
        self.assertEqual(r['source_commit'],PIN);self.assertEqual(r['passed_methods'],10)
        self.assertEqual(r['policy_combinations'],209);self.assertFalse(r['application_changed'])
        self.assertFalse(r['whole_wallet_complete']);self.assertFalse(r['new_ios_build_performed'])
        for row in r['files']:self.assertEqual(sha((EVIDENCE/row['path']).read_bytes()),row['sha256'])
    def test_hosted_receipts_match_artifact_and_individual_logs(self):
        for folder,runid,pin,counts in [('stellar-plan-timestamps',41738980809,'e857ad953226689a9c64ded880bf4aff053efbd8',[6,6,40]),('stellar-persistence',41740254836,'527c44962fbcc7e2d194dfa4dfa2b4be4fb30090',[31])]:
            p=ROOT/'evidence/5.0.2-build104'/('hosted-'+folder)
            run=json.loads((p/'run.json').read_text());a=json.loads((p/'artifact.json').read_text());v=json.loads((p/'verification.json').read_text())
            self.assertEqual(run['id'],runid);self.assertEqual(run['head_sha'],pin);self.assertEqual(run['conclusion'],'success')
            self.assertEqual(a['digest'],'sha256:'+sha((p/'artifact.zip').read_bytes()))
            self.assertEqual(sorted(r['methods'] for r in v['reports']),counts)
            with zipfile.ZipFile(p/'artifact.zip') as z:
                for r in v['reports']:
                    raw=z.read(r['report']);self.assertEqual(sha(raw),r['sha256'])
                    data=json.loads(raw);base=Path(r['report']).parent
                    for f in data['files']:self.assertEqual(sha(z.read(str(base/f['path']))),f['sha256'])
                    cases=data.get('methods')
                    if cases is None:cases=json.loads(z.read(str(base/'OathAnkr-cases.json')))
                    for c in cases:self.assertEqual(sha(z.read(str(base/c['log']))),c['log_sha256'])
                    codes=[c['exit_code'] for c in cases];self.assertEqual(codes,r['exit_codes'])
                    self.assertEqual(codes,[0,-5,-5,0,-5,0] if r['report']=='before/result.json' else [0]*len(cases))
    def test_execution_limits_and_reproducibility(self):
        driver=(ROOT/'scripts/stellar-multisig-review.py').read_text()
        for phrase in ['Fresh scratch/output required','require_source_state(source,PIN)','(deny network*)','SDK source pin or state mismatch','Unexpected overlay files']:
            self.assertIn(phrase,driver)
        workflow=(ROOT/'.github/workflows/stellar-multisig.yml').read_text()
        self.assertIn('contents: read',workflow);self.assertIn(PIN,workflow)
        self.assertIn('test_stellar_multisig_review.py',workflow);self.assertNotIn('test_stellar_decoding_review.py',workflow)
        self.assertNotIn('pull_request',workflow);self.assertNotIn('secrets.',workflow)
        report=(ROOT/'review/STELLAR-MULTISIG.md').read_text()
        for phrase in ['whole-wallet audit remains incomplete','No new confirmed defect','not independent certification','No new generic iOS build','No simulator, UI interaction']:
            self.assertIn(phrase,report)
