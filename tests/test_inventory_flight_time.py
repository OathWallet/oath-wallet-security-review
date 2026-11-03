import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BEFORE = 'fd06fdff104d128e00cc414d2de1472f11752e04'
AFTER = '63e0be4a10106fc577792a7fb3c6d69b1cc8870c'
FAILURES = {'testTronPreFinalityReadCompletingLateIsNotCurrent',
            'testTonPreFinalityReadCompletingLateIsNotCurrent',
            'testTronRequiresLocalFinalityEvenWithOlderBlockTimestamp'}
def sha(raw): return hashlib.sha256(raw).hexdigest()

class InventoryFlightEvidence(unittest.TestCase):
    def test_identical_fixture_and_exact_before_after_failures(self):
        root = ROOT/'evidence/5.0.2-build104/inventory-flight-time'
        manifest = json.loads((root/'manifest.json').read_bytes())
        self.assertEqual(manifest['before_commit'], BEFORE)
        self.assertEqual(manifest['repair_commit'], AFTER)
        for row in manifest['files']:
            self.assertEqual(sha((root/row['path']).read_bytes()), row['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()), {r['path'] for r in checks}|{'CHECKSUMS.json'})
            for row in checks: self.assertEqual(sha(z.read(row['path'])), row['sha256'])
            for mode, pin in [('before', BEFORE), ('after', AFTER)]:
                r = json.loads(z.read(mode+'/result.json'))
                self.assertEqual(r['source_commit'], pin)
                self.assertEqual(r['baseline'], mode == 'before')
                self.assertEqual(r['driver_sha256'], sha((ROOT/'scripts/inventory-flight-time.py').read_bytes()))
                self.assertEqual(r['overlay_sha256'], sha((ROOT/'fixtures/inventory-flight-time/InventoryFlightTimeTests.swift').read_bytes()))
                self.assertEqual(len(r['source_files']), 3)
                for f in r['source_files']: self.assertEqual(f['source_sha256'], f['executed_sha256'])
                self.assertEqual(len(r['methods']), 5)
                self.assertEqual(len({m['method'] for m in r['methods']}), 5)
                self.assertEqual({m['method'] for m in r['methods'] if m['status'] != 'passed'}, FAILURES if mode == 'before' else set())
                for f in r['files']: self.assertEqual(sha(z.read(mode+'/'+f['path'])), f['sha256'])
                for m in r['methods']:
                    raw = z.read(mode+'/'+m['log'])
                    self.assertEqual(sha(raw), m['log_sha256'])
                    self.assertIn(b'Executed 1 test', raw)
                    self.assertEqual(m['exit_code'] == 0, m['status'] == 'passed')
                self.assertEqual(r['runtime_network'], 'denied by sandbox-exec')
            r = json.loads(z.read('adjacent/result.json'))
            self.assertEqual(r['source_commit'], AFTER)
            self.assertEqual(r['driver_sha256'], sha((ROOT/'scripts/inventory-flight-adjacent.py').read_bytes()))
            self.assertEqual(len(r['methods']), 27)
            self.assertEqual(len(r['excluded_live_methods']), 2)
            for m in r['methods']:
                self.assertEqual(m['status'], 'passed'); self.assertEqual(m['exit_code'], 0)
                self.assertEqual(sha(z.read('adjacent/'+m['log'])), m['log_sha256'])
            for f in r['files']: self.assertEqual(sha(z.read('adjacent/'+f['path'])), f['sha256'])

    def test_replay_workflow_is_pinned_and_unprivileged(self):
        workflow = (ROOT/'.github/workflows/inventory-flight-time.yml').read_text()
        self.assertIn(BEFORE, workflow); self.assertIn(AFTER, workflow)
        self.assertIn('contents: read', workflow)
        self.assertNotIn('secrets.', workflow); self.assertNotIn('pull_request_target', workflow)
        for name in ['inventory-flight-time.py', 'inventory-flight-adjacent.py']:
            driver = (ROOT/'scripts'/name).read_text()
            self.assertIn('(deny network*)', driver)
            self.assertIn("'--build-tests'", driver)
            self.assertIn('require_source_state', driver)

    def test_hosted_journal_receipt_and_negative_control(self):
        root = ROOT/'evidence/5.0.2-build104/hosted-near-journal-races'
        manifest = json.loads((root/'manifest.json').read_bytes())
        run = json.loads((root/'run.json').read_bytes())
        meta = json.loads((root/'metadata.json').read_bytes())
        self.assertEqual(run['id'], 41620145140)
        self.assertEqual(run['status'], 'completed'); self.assertEqual(run['conclusion'], 'success')
        self.assertEqual(run['head_sha'], manifest['audit_commit'])
        self.assertEqual(meta['workflow_run']['head_sha'], run['head_sha'])
        self.assertEqual(meta['digest'], 'sha256:'+sha((root/'artifact.zip').read_bytes()))
        for row in manifest['files']: self.assertEqual(sha((root/row['path']).read_bytes()), row['sha256'])
        with zipfile.ZipFile(root/'artifact.zip') as z:
            for row in manifest['expanded_files_verified']: self.assertEqual(sha(z.read(row['path'])), row['sha256'])
            for mode in ['control', 'mutant']:
                r = json.loads(z.read(mode+'/result.json'))
                self.assertEqual(r['source_commit'], '5d91d1e4dfd36c56031c7a8fb1ee305446dc54de')
                self.assertEqual(r['driver_sha256'], sha((ROOT/'scripts/near-journal-races.py').read_bytes()))
                self.assertEqual(r['overlay_sha256'], sha((ROOT/'fixtures/near-journal-races/NearAuditJournalRaceTests.swift').read_bytes()))
                expected = {'NearAuditJournalRaceTests/testConcurrentDuplicateWalletsReserveExactlyOneSender', 'NearSendJournalTests/testCrossWalletReservationAndCancelledAuthenticationReleasesOnlyUnsigned', 'NearSendJournalTests/testExactSignedBytesSurviveReopenAndUnknownBroadcastReservesSender'} if mode == 'mutant' else set()
                self.assertEqual({m['method'] for m in r['methods'] if m['status'] != 'passed'}, expected)
                self.assertEqual(len(r['methods']), 9)
                for f in r['files']: self.assertEqual(sha(z.read(mode+'/'+f['path'])), f['sha256'])
                for m in r['methods']:
                    raw = z.read(mode+'/'+m['log'])
                    self.assertEqual(sha(raw), m['log_sha256'])
                    self.assertIn(b'Executed 1 test', raw)
                    self.assertEqual(m['exit_code'] == 0, m['status'] == 'passed')
