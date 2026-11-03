import copy
import hashlib
import json
import zipfile
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import near_multisig_signing_evidence as evidence

class NearMultisigSigningEvidence(unittest.TestCase):
    def setUp(self):
        self.report={'source_commit':evidence.COMMIT,'methods':[{'method':n,'status':'passed','exit_code':0} for n in evidence.METHODS], 'multisig_bundles':50,'transaction_parts':188,'independent_signature_verification':True}
    def test_exact_matrix_receipt(self):
        evidence.validate(self.report)
    def test_incomplete_or_other_source_rejected(self):
        for edit in [{'source_commit':'0'*40},{'multisig_bundles':49},{'transaction_parts':187},{'independent_signature_verification':False},{'methods':self.report['methods'][:-1]}]:
            with self.assertRaises(ValueError): evidence.validate(self.report|edit)
    def test_failed_skipped_or_repeated_case_rejected(self):
        for edit in [{'status':'skipped'},{'exit_code':1},{'method':evidence.METHODS[0]}]:
            r=copy.deepcopy(self.report);r['methods'][-1].update(edit)
            with self.assertRaises(ValueError):evidence.validate(r)

    def test_published_archive_and_final_fixture_bindings(self):
        root=Path(__file__).resolve().parents[1]
        folder=root/'evidence/5.0.2-build104/near-multisig-vectors'
        manifest=json.loads((folder/'manifest.json').read_text())
        for f in manifest['files']:
            self.assertEqual(hashlib.sha256((folder/f['path']).read_bytes()).hexdigest(),f['sha256'])
        with zipfile.ZipFile(folder/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(len(checks),manifest['archive_file_count'])
            for name,sha in checks.items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),sha)
            report=json.loads(z.read('attempt2/result.json'));evidence.validate(report)
            self.assertEqual(report['overlay_sha256'],hashlib.sha256((root/'fixtures/near-multisig-signing/NearAuditMultisigTests.swift').read_bytes()).hexdigest())
            self.assertEqual(report['script_sha256'],hashlib.sha256((root/'scripts/near-multisig-signing.py').read_bytes()).hexdigest())
            self.assertEqual(report['generator_sha256'],hashlib.sha256((root/'fixtures/near-multisig-signing/generate.mjs').read_bytes()).hexdigest())
            self.assertEqual(report['verifier_sha256'],hashlib.sha256((root/'fixtures/near-multisig-signing/verify.mjs').read_bytes()).hexdigest())
