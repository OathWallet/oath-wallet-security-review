import copy
import hashlib
import json
from pathlib import Path
import sys
import tomllib
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import near_contract_unit as driver


class NativeContractEvidence(unittest.TestCase):
    def locks(self):
        with zipfile.ZipFile(ROOT/'evidence/5.0.2-build104/near-contract-unit/runs.zip') as z:
            return (tomllib.loads(z.read('original/Cargo.lock').decode()),
                    tomllib.loads(z.read('final/inputs/Cargo.lock').decode()))

    def test_pruned_dependency_versions_checksums_and_closure(self):
        before, after = self.locks()
        result = driver.verify_lock(before, after)
        self.assertEqual((result['original_packages'],result['unit_packages']),(335,70))
        self.assertTrue(result['retained_versions_and_checksums_match'])
        self.assertEqual(len(result['removed_edges']),2)
        for mutate in ('checksum','version','missing','extra','edge'):
            changed = copy.deepcopy(after)
            if mutate == 'checksum': changed['package'][0]['checksum'] = '0'*64
            elif mutate == 'version': changed['package'][0]['version'] = '99.0.0'
            elif mutate == 'missing': changed['package'].pop()
            elif mutate == 'extra': changed['package'].append(copy.deepcopy(changed['package'][0]))
            else:
                next(p for p in changed['package'] if p['name']=='multisig2')['dependencies'] = []
            with self.assertRaises(ValueError, msg=mutate): driver.verify_lock(before, changed)

    def test_abort_and_wrong_fixture_never_count_as_passes(self):
        success = 'test result: ok. 1 passed; 0 failed; 0 ignored;'
        for name, message in driver.ABORTS.items():
            name = 'tests::'+name
            self.assertEqual(driver.classify(name,-6,message+' non-unwinding panic'),'blocked_sdk_abort')
            for code, log in [(0,success),(-6,'other panic'),(1,message+' non-unwinding panic')]:
                self.assertEqual(driver.classify(name,code,log),'unexpected')
        name = 'tests::test_panics_add_key_different_account'
        self.assertEqual(driver.classify(name,0,success+' called `Result::unwrap()` on an `Err` value'),'invalid_fixture_pass')
        self.assertEqual(driver.classify(name,0,success),'unexpected')
        self.assertEqual(driver.classify('audit_contract::case',0,success),'passed')
        self.assertEqual(driver.classify('audit_contract::case',0,'0 passed;'),'unexpected')

    def test_published_inputs_results_and_preserved_failure_hashes(self):
        root = ROOT/'evidence/5.0.2-build104/near-contract-unit'
        manifest = json.loads((root/'manifest.json').read_text())
        for entry in manifest['files']:
            self.assertEqual(hashlib.sha256((root/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checksums = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),set(checksums)|{'CHECKSUMS.json'})
            for path, digest in checksums.items():
                self.assertEqual(hashlib.sha256(z.read(path)).hexdigest(),digest)
            report = json.loads(z.read('final/result.json'))
            self.assertFalse(report['all_contract_tests_passed'])
            self.assertFalse(report['wasm_execution_verified'])
            self.assertFalse(report['source_to_binary_rebuild_verified'])
            statuses = [r['status'] for r in report['cases']]
            self.assertEqual((statuses.count('passed'),statuses.count('blocked_sdk_abort'),statuses.count('invalid_fixture_pass')),(9,5,1))
            self.assertEqual(report['source_sha256'],driver.SOURCE_SHA)
            self.assertEqual(report['driver_sha256'],hashlib.sha256((ROOT/'scripts/near_contract_unit.py').read_bytes()).hexdigest())
            original = z.read('original/src/lib.rs')
            overlay = (ROOT/'fixtures/near-contract-unit/audit.rs').read_bytes()
            self.assertEqual(z.read('final/inputs/src/lib.rs'),original+b'\n'+overlay)
            self.assertEqual(hashlib.sha256(overlay).hexdigest(),report['overlay_sha256'])
            for row in report['cases']:
                data = z.read('final/'+row['log'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
                self.assertEqual(driver.classify(row['name'],row['exit_code'],data.decode()),row['status'])
            self.assertIn('non-unwinding panic',z.read('original/unit-tests.log').decode())

    def test_hosted_app_evidence_remains_separate(self):
        root = ROOT/'evidence/5.0.2-build104/hosted-near-multisig'
        manifest = json.loads((root/'manifest.json').read_text())
        for entry in manifest['files']:
            self.assertEqual(hashlib.sha256((root/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
        self.assertEqual((manifest['run_id'],manifest['passed'],manifest['copies']),(41609444047,10,4))
        meta = json.loads((root/'metadata.json').read_text())
        self.assertEqual(meta['digest'],'sha256:'+hashlib.sha256((root/'artifact.zip').read_bytes()).hexdigest())
        self.assertFalse(manifest['source_to_binary_rebuild_verified'])

    def test_secret_scanner_matches_are_bound_to_real_log_checksums(self):
        root = ROOT/'evidence/5.0.2-build104/near-contract-unit'
        report = json.loads((root/'secret-scan-classification.json').read_text())
        raw = (root/'secret-scan-redacted.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),report['raw_report_sha256'])
        self.assertEqual(len(json.loads(raw)),8)
        self.assertEqual((report['raw_findings'],report['unresolved_findings']),(8,0))
        self.assertEqual(hashlib.sha256((root/'runs.zip').read_bytes()).hexdigest(),report['archive_sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            lines = z.read('CHECKSUMS.json').decode().splitlines()
            rows = report['verified_checksum_false_positives']
            self.assertEqual(len(rows),8)
            for row in rows:
                self.assertEqual(row['rule'],'generic-api-key')
                self.assertIn(row['sha256'],lines[row['line']-1])
                self.assertEqual(hashlib.sha256(z.read(row['member'])).hexdigest(),row['sha256'])
