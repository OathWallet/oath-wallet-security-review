import hashlib
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import near_contract_unwind as driver


class ContractUnwindEvidence(unittest.TestCase):
    def test_patch_is_limited_to_native_panic_boundary(self):
        sdk='prefix\nextern "C" fn panic_utf8(a:u64,b:u64) -> ! { panic!() }\nsuffix\n'
        sys='extern "C" {\n    pub fn panic_utf8(len: u64, ptr: u64) -> !;\n}\n'
        changed_sdk,changed_sys=driver.patch_mock(sdk,sys)
        self.assertEqual(changed_sdk.replace('C-unwind','C'),sdk)
        self.assertIn('#[cfg(target_arch = "wasm32")]',changed_sys)
        self.assertIn('#[cfg(not(target_arch = "wasm32"))]\nextern "C-unwind"',changed_sys)
        for a,b in [(sdk+sdk,sys),(sdk,sys+sys),('other',sys),(sdk,'other')]:
            with self.assertRaises(ValueError):driver.patch_mock(a,b)

    def test_invalid_fixtures_and_aborts_never_inflate_passes(self):
        success='test result: ok. 1 passed; 0 failed; 0 ignored;'
        messages={driver.WRONG_KEY:'cooldown','case':'guard'}
        self.assertEqual(driver.classify(driver.WRONG_KEY,0,success+'cooldown',messages),'invalid_fixture_pass')
        self.assertEqual(driver.classify(driver.WRONG_FIXTURE,0,success+' called `Result::unwrap()` on an `Err` value',messages),'invalid_fixture_pass')
        self.assertEqual(driver.classify('case',-6,'guard non-unwinding panic',messages),'blocked_sdk_abort')
        for code,log in [(0,success+'wrong reason'),(-6,'other panic'),(1,'guard'),(0,'guard')]:
            self.assertEqual(driver.classify('case',code,log,messages),'failed')

    def test_paired_evidence_and_exact_mutation_sensitivity(self):
        root=ROOT/'evidence/5.0.2-build104/near-contract-unwind'
        manifest=json.loads((root/'manifest.json').read_text())
        for row in manifest['files']:
            self.assertEqual(hashlib.sha256((root/row['path']).read_bytes()).hexdigest(),row['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
            for row in checks:self.assertEqual(hashlib.sha256(z.read(row['path'])).hexdigest(),row['sha256'])
            reports={mode:json.loads(z.read(mode+'/result.json')) for mode in ('before','after','mutant')}
            before,after,mutant=[reports[m] for m in ('before','after','mutant')]
            self.assertEqual(before['counts'],{'passed':9,'blocked_sdk_abort':10,'invalid_fixture_pass':1})
            self.assertEqual(after['counts'],{'passed':18,'invalid_fixture_pass':2})
            self.assertEqual(mutant['counts'],{'passed':14,'invalid_fixture_pass':2,'failed':4})
            self.assertEqual(z.read('before/inputs/src/lib.rs'),z.read('after/inputs/src/lib.rs'))
            self.assertEqual(before['overlay_sha256'],after['overlay_sha256'])
            self.assertNotEqual(mutant['executed_contract_source_sha256'],after['executed_contract_source_sha256'])
            self.assertEqual({r['name'] for r in mutant['cases'] if r['status']=='failed'},driver.MUTANT_FAILURES)
            self.assertEqual(z.read('after/inputs/src/lib.rs').replace(b'if self.members.contains(&member) {',b'if true {'),z.read('mutant/inputs/src/lib.rs'))
            for mode,report in reports.items():
                self.assertFalse(report['production_app_changed'])
                self.assertFalse(report['wasm_execution_verified'])
                self.assertFalse(report['source_to_binary_rebuild_verified'])
                self.assertEqual(report['driver_sha256'],hashlib.sha256((ROOT/'scripts/near_contract_unwind.py').read_bytes()).hexdigest())
                for row in report['files']:
                    self.assertEqual(hashlib.sha256(z.read(mode+'/'+row['path'])).hexdigest(),row['sha256'])
                changed=[r['path'] for r in report['sdk_files'] if r['original_sha256']!=r['executed_sha256']]
                self.assertEqual(len(changed),0 if mode=='before' else 2)

    def test_verified_hosted_multisig_vectors(self):
        root=ROOT/'evidence/5.0.2-build104/hosted-near-multisig-vectors'
        report=json.loads((root/'manifest.json').read_text())
        for row in report['files']:
            self.assertEqual(hashlib.sha256((root/row['path']).read_bytes()).hexdigest(),row['sha256'])
        self.assertEqual((report['run_id'],report['methods'],report['multisig_bundles'],report['transaction_parts'],report['verifier_controls']),(41611022824,3,50,188,5))
        metadata=json.loads((root/'metadata.json').read_text())
        self.assertEqual(metadata['digest'],'sha256:'+hashlib.sha256((root/'artifact.zip').read_bytes()).hexdigest())
        with zipfile.ZipFile(root/'artifact.zip') as z:
            for row in report['expanded_files_verified']:
                if row['path'].startswith('extracted/'):
                    self.assertEqual(hashlib.sha256(z.read(row['path'].removeprefix('extracted/'))).hexdigest(),row['sha256'])
            import near_multisig_signing_evidence
            near_multisig_signing_evidence.validate(json.loads(z.read('result.json')))
            controls=json.loads(z.read('verifier-controls.json'))['controls']
            self.assertEqual(len(controls),5)
            for row in controls:
                self.assertEqual(row['exit_code'],1)
                self.assertEqual(hashlib.sha256(z.read(row['log'])).hexdigest(),row['log_sha256'])
                self.assertIn(row['expected_error'],z.read(row['log']).decode())
        native=ROOT/'evidence/5.0.2-build104/hosted-near-contract-native'
        replay=json.loads((native/'manifest.json').read_text())
        for row in replay['files']:
            self.assertEqual(hashlib.sha256((native/row['path']).read_bytes()).hexdigest(),row['sha256'])
        self.assertEqual(replay['run_id'],41614094759)
        self.assertEqual(replay['counts'],{'passed':9,'blocked_sdk_abort':5,'invalid_fixture_pass':1})
        self.assertFalse(replay['all_contract_tests_passed'])
        self.assertFalse(replay['wasm_execution_verified'])
        meta=json.loads((native/'metadata.json').read_text())
        self.assertEqual(meta['digest'],'sha256:'+hashlib.sha256((native/'artifact.zip').read_bytes()).hexdigest())
