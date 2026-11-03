import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PIN = '5d91d1e4dfd36c56031c7a8fb1ee305446dc54de'
EXPECTED = {
    'NearAuditJournalRaceTests/testConcurrentDuplicateWalletsReserveExactlyOneSender',
    'NearAuditJournalRaceTests/testLateAcknowledgementsPreserveEveryTerminalStateAfterReopen',
    'NearAuditJournalRaceTests/testMalformedReceiptsCannotPartiallyMutateSignedJournal',
    'NearSendJournalTests/testCrossWalletReservationAndCancelledAuthenticationReleasesOnlyUnsigned',
    'NearSendJournalTests/testExactSignedBytesSurviveReopenAndUnknownBroadcastReservesSender',
    'NearSendJournalTests/testSubmissionObservationRequiresFinalJournalAndWalletScope',
    'NearSendJournalTests/testTamperedSignedTransactionAndTestnetPlanRejectedBeforeJournal',
    'NearSendJournalTests/testFailedExecutionSettlesAsFailureAndNeverSuccess',
    'NearSendJournalTests/testProvenExpiryReleasesSenderWithoutClaimingFeeOrBalanceRefresh',
}
NEGATIVE = {n for n in EXPECTED if n.split('/')[-1] in {
    'testConcurrentDuplicateWalletsReserveExactlyOneSender',
    'testCrossWalletReservationAndCancelledAuthenticationReleasesOnlyUnsigned',
    'testExactSignedBytesSurviveReopenAndUnknownBroadcastReservesSender',
}}

def digest(raw): return hashlib.sha256(raw).hexdigest()

class NearJournalRaceEvidence(unittest.TestCase):
    def test_results_logs_sources_and_negative_control_are_bound(self):
        root = ROOT/'evidence/5.0.2-build104/near-journal-races'
        manifest = json.loads((root/'manifest.json').read_text())
        for row in manifest['files']:
            self.assertEqual(digest((root/row['path']).read_bytes()), row['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as archive:
            checks = json.loads(archive.read('CHECKSUMS.json'))
            self.assertEqual(set(archive.namelist()), {r['path'] for r in checks}|{'CHECKSUMS.json'})
            for row in checks: self.assertEqual(digest(archive.read(row['path'])), row['sha256'])
            reports = {mode: json.loads(archive.read(mode+'/result.json')) for mode in ('control','mutant')}
            for mode, report in reports.items():
                self.assertEqual(report['source_commit'], PIN)
                self.assertEqual(len(report['methods']), 9)
                self.assertEqual({r['method'] for r in report['methods']}, EXPECTED)
                self.assertEqual({r['method'] for r in report['methods'] if r['status']!='passed'}, NEGATIVE if mode=='mutant' else set())
                self.assertEqual(report['mutant'], mode=='mutant')
                self.assertEqual(report['overlay_sha256'], digest((ROOT/'fixtures/near-journal-races/NearAuditJournalRaceTests.swift').read_bytes()))
                self.assertEqual(report['driver_sha256'], digest((ROOT/'scripts/near-journal-races.py').read_bytes()))
                self.assertEqual(report['isolation_classifier_sha256'], digest((ROOT/'scripts/isolated_tests.py').read_bytes()))
                for row in report['files']: self.assertEqual(digest(archive.read(mode+'/'+row['path'])), row['sha256'])
                for row in report['methods']:
                    log = archive.read(mode+'/'+row['log'])
                    self.assertIn(b'Executed 1 test', log)
                    self.assertIn(row['status'], ['passed','failed'])
                    self.assertEqual(row['exit_code']==0, row['status']=='passed')
                    self.assertEqual(digest(log), row['log_sha256'])
            self.assertEqual(reports['control']['source_sha256'], reports['control']['executed_source_sha256'])
            self.assertEqual(reports['control']['source_sha256'], reports['mutant']['source_sha256'])
            self.assertNotEqual(reports['mutant']['source_sha256'], reports['mutant']['executed_source_sha256'])
            patch = archive.read('mutant/mutation.patch').decode()
            self.assertEqual(patch.count('\n@@'), 1)
            self.assertIn('NearIdentity.address($0.senderAddress) == plan.sender', patch)
            binding = json.loads((root/'source-binding.json').read_text())
            ledger = {r['path']: r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
            for row in binding['files']:
                self.assertEqual(row['sha256'], ledger[row['path']]['sha256'])
                self.assertEqual(row['status'], ledger[row['path']]['status'])
            fixture = next(r for r in binding['files'] if r['path'].endswith('/NearSendJournalTests.swift'))
            self.assertEqual(fixture['sha256'], reports['control']['existing_fixture_sha256'])
            self.assertEqual(fixture['sha256'], reports['mutant']['existing_fixture_sha256'])

    def test_test_selection_and_workflow_boundaries(self):
        text = (ROOT/'fixtures/near-journal-races/NearAuditJournalRaceTests.swift').read_text()
        names = {'NearAuditJournalRaceTests/'+n for n in re.findall(r'func (test\w+)\(',text)}
        self.assertEqual(names, {n for n in EXPECTED if n.startswith('NearAuditJournalRaceTests/')})
        driver = (ROOT/'scripts/near-journal-races.py').read_text()
        self.assertIn('(deny network*)', driver)
        self.assertIn('require_source_state(source,COMMIT)', driver)
        workflow = (ROOT/'.github/workflows/near-journal-races.yml').read_text()
        self.assertNotIn('pull_request_target', workflow)
        self.assertNotIn('secrets.', workflow)
        self.assertIn('contents: read', workflow)
