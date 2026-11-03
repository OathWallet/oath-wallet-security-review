import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PIN = 'fd06fdff104d128e00cc414d2de1472f11752e04'
def digest(raw): return hashlib.sha256(raw).hexdigest()

class TronTonLedgerEvidence(unittest.TestCase):
    def test_production_case_evidence_and_partial_scope(self):
        root = ROOT/'evidence/5.0.2-build104/tron-ton-ledger'
        manifest = json.loads((root/'manifest.json').read_bytes())
        self.assertEqual(manifest['source_commit'], PIN)
        for row in manifest['files']:
            self.assertEqual(digest((root/row['path']).read_bytes()), row['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()), {row['path'] for row in checks}|{'CHECKSUMS.json'})
            for row in checks: self.assertEqual(digest(z.read(row['path'])), row['sha256'])
            report = json.loads(z.read('result.json'))
            self.assertEqual(report['source_commit'], PIN)
            self.assertEqual(report['driver_sha256'], digest((ROOT/'scripts/tron-ton-ledger.py').read_bytes()))
            self.assertEqual(report['classifier_sha256'], digest((ROOT/'scripts/isolated_tests.py').read_bytes()))
            self.assertEqual(len(report['methods']),27)
            self.assertEqual(len({row['method'] for row in report['methods']}),27)
            self.assertEqual(report['excluded_live_methods'], ['TronLedgerTests/testLiveCompleteSmallPublicAccountHistoryAndReopen','TonLedgerTests/testLiveSmallFundedWalletCompleteHistoryAndOfflineReopen'])
            self.assertEqual(len(report['test_executable_sha256']),64)
            for row in report['methods']:
                self.assertEqual(row['status'],'passed'); self.assertEqual(row['exit_code'],0)
                self.assertNotIn('/testLive',row['method'])
                raw=z.read(row['log']); self.assertEqual(digest(raw),row['log_sha256'])
                self.assertIn(b'Executed 1 test',raw)
            for row in report['files']: self.assertEqual(digest(z.read(row['path'])),row['sha256'])
        binding=json.loads((root/'source-binding.json').read_bytes())
        ledger=json.loads((ROOT/'scope/inventory.json').read_bytes())
        self.assertEqual(binding['byte_identical_baseline'],ledger['source_commit'])
        rows={row['path']:row for row in ledger['files']}
        self.assertEqual(len(binding['files']),4)
        for row in binding['files']:
            self.assertEqual(row['sha256'],rows[row['path']]['sha256'])
            self.assertEqual(row['status'],'partially-reviewed')
            self.assertEqual(rows[row['path']]['status'],'partially-reviewed')
        workflow=(ROOT/'.github/workflows/tron-ton-ledger.yml').read_text()
        self.assertIn(PIN,workflow);self.assertIn('contents: read',workflow)
        self.assertNotIn('secrets.',workflow);self.assertNotIn('pull_request_target',workflow)
        driver=(ROOT/'scripts/tron-ton-ledger.py').read_text()
        self.assertIn('(deny network*)',driver);self.assertIn("'--build-tests'",driver)

    def test_hosted_activation_result_matches_downloaded_artifact(self):
        root=ROOT/'evidence/5.0.2-build104/hosted-near-multisig-activation'
        run=json.loads((root/'run.json').read_bytes());meta=json.loads((root/'metadata.json').read_bytes());manifest=json.loads((root/'manifest.json').read_bytes())
        self.assertEqual(run['id'],41618881396)
        self.assertEqual(run['status'],'completed');self.assertEqual(run['conclusion'],'success')
        self.assertEqual(run['head_sha'],manifest['audit_commit'])
        self.assertEqual(meta['workflow_run']['head_sha'],run['head_sha'])
        self.assertEqual(meta['digest'],'sha256:'+digest((root/'artifact.zip').read_bytes()))
        for row in manifest['files']:self.assertEqual(digest((root/row['path']).read_bytes()),row['sha256'])
        with zipfile.ZipFile(root/'artifact.zip') as z:
            for row in manifest['expanded_files_verified']:self.assertEqual(digest(z.read(row['path'])),row['sha256'])
            for mode in ['control','mutant']:
                report=json.loads(z.read(mode+'/result.json'))
                self.assertEqual(report['source_commit'],'5d91d1e4dfd36c56031c7a8fb1ee305446dc54de')
                self.assertEqual(report['driver_sha256'],digest((ROOT/'scripts/near-multisig-activation.py').read_bytes()))
                self.assertEqual(report['overlay_sha256'],digest((ROOT/'fixtures/near-multisig-activation/NearAuditMultisigActivationTests.swift').read_bytes()))
                self.assertEqual(len(report['methods']),6)
                self.assertEqual({r['method'] for r in report['methods'] if r['status']!='passed'}, {'testUnexpectedBootstrapAuthorityAndNonceAreRejected'} if mode=='mutant' else set())
                for row in report['files']:self.assertEqual(digest(z.read(mode+'/'+row['path'])),row['sha256'])
                for row in report['methods']:
                    raw=z.read(mode+'/'+row['log']);self.assertEqual(digest(raw),row['log_sha256']);self.assertIn(b'Executed 1 test',raw)
                    self.assertEqual(row['exit_code']==0,row['status']=='passed')
