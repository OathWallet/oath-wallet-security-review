import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'testStagedTransferColdRestartPreservesBytesAndFees',
    'testStatusNeverBroadcastsAndFailureStopsRemainingParts',
    'testChangedRequestAndProposalIDNeverReleaseConfirmation',
    'testExpiryRequiresUnusedPartNonce',
    'testCancelledStatusReplyNeverReleasesNextPart',
    'testConcurrentReplaysOnlyBroadcastIdenticalAuthorizedPart',
}

class MultisigLifecycleEvidence(unittest.TestCase):
    def test_complete_evidence_and_mutation_failure_are_bound_to_sources(self):
        root = ROOT/'evidence/5.0.2-build104/near-multisig-lifecycle'
        manifest = json.loads((root/'manifest.json').read_text())
        for row in manifest['files']:
            self.assertEqual(hashlib.sha256((root/row['path']).read_bytes()).hexdigest(),row['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
            for row in checks:self.assertEqual(hashlib.sha256(z.read(row['path'])).hexdigest(),row['sha256'])
            reports = {mode:json.loads(z.read(mode+'/result.json')) for mode in ('control','mutant')}
            for mode,report in reports.items():
                self.assertEqual(report['source_commit'],'5d91d1e4dfd36c56031c7a8fb1ee305446dc54de')
                self.assertEqual({r['method'] for r in report['methods']},EXPECTED)
                self.assertEqual(len(report['methods']),6)
                self.assertEqual(report['overlay_sha256'],hashlib.sha256((ROOT/'fixtures/near-multisig-lifecycle/NearAuditMultisigLifecycleTests.swift').read_bytes()).hexdigest())
                self.assertEqual(report['driver_sha256'],hashlib.sha256((ROOT/'scripts/near-multisig-lifecycle.py').read_bytes()).hexdigest())
                self.assertEqual(report['mutant'],mode=='mutant')
                failed = {r['method'] for r in report['methods'] if r['status']!='passed'}
                self.assertEqual(failed,{'testChangedRequestAndProposalIDNeverReleaseConfirmation'} if mode=='mutant' else set())
                for row in report['methods']:
                    log=z.read(mode+'/'+row['log'])
                    self.assertEqual(hashlib.sha256(log).hexdigest(),row['log_sha256'])
                    self.assertIn(b'Executed 1 test',log)
                    self.assertEqual(row['exit_code']==0,row['status']=='passed')
                for row in report['files']:self.assertEqual(hashlib.sha256(z.read(mode+'/'+row['path'])).hexdigest(),row['sha256'])
            self.assertEqual(reports['control']['source_sha256'],reports['control']['executed_source_sha256'])
            self.assertEqual(reports['control']['source_sha256'],reports['mutant']['source_sha256'])
            self.assertNotEqual(reports['mutant']['source_sha256'],reports['mutant']['executed_source_sha256'])
            patch=z.read('mutant/mutation.patch').decode()
            self.assertEqual(patch.count('\n@@'),1)
            self.assertIn('-                    guard request == (try c.request(plan)) else { throw NearSendError.changed }',patch)

    def test_test_selection_and_runtime_network_boundary(self):
        overlay=(ROOT/'fixtures/near-multisig-lifecycle/NearAuditMultisigLifecycleTests.swift').read_text()
        self.assertEqual(set(re.findall(r'func (test\w+)\(',overlay)),EXPECTED)
        script=(ROOT/'scripts/near-multisig-lifecycle.py').read_text()
        self.assertIn('(deny network*)',script)
        self.assertIn("require_source_state(source,COMMIT)",script)
        workflow=(ROOT/'.github/workflows/near-multisig-lifecycle.yml').read_text()
        self.assertNotIn('pull_request_target',workflow)
        self.assertNotIn('secrets.',workflow)
        self.assertIn('contents: read',workflow)
