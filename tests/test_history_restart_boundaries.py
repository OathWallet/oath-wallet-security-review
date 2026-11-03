import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '05e7917f0a3c26072b1a6b88d2e9e4a0d0310427'
AFTER = 'b3f1f6af98bedfe850d390cac684a563c598e3ac'
FAILURES = {'SuiLedgerTests/testAuditRestartRejectsOverflowFromDecodedProviderCheckpoint',
            'SuiLedgerTests/testAuditRestartRejectsAnotherAccountsCursor',
            'XrplLedgerTests/testAuditRestartRejectsAnotherAccountsCursor'}
def sha(raw): return hashlib.sha256(raw).hexdigest()

class HistoryRestartEvidence(unittest.TestCase):
    def test_paired_production_results_and_hashes(self):
        root = ROOT/'evidence/5.0.2-build104/history-restart-boundaries'
        m = json.loads((root/'manifest.json').read_bytes())
        self.assertEqual(m['before_commit'], BEFORE); self.assertEqual(m['repair_commit'], AFTER)
        for f in m['files']: self.assertEqual(sha((root/f['path']).read_bytes()), f['sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()), {f['path'] for f in checks}|{'CHECKSUMS.json'})
            for f in checks: self.assertEqual(sha(z.read(f['path'])), f['sha256'])
            for mode, pin in [('before', BEFORE), ('after', AFTER)]:
                r = json.loads(z.read(mode+'/result.json'))
                self.assertEqual(r['source_commit'], pin)
                self.assertEqual(r['driver_sha256'], sha((ROOT/'scripts/history-restart-boundaries.py').read_bytes()))
                self.assertEqual(r['overlay_sha256'], sha((ROOT/'fixtures/history-restart-boundaries/SuiHistoryRestartBoundaryTests.swift').read_bytes()))
                self.assertEqual(len(r['source_files']), 4)
                for f in r['source_files']: self.assertEqual(f['source_sha256'], f['executed_sha256'])
                self.assertEqual(len(r['methods']), 4)
                self.assertEqual({t['method'] for t in r['methods'] if t['status'] != 'passed'}, FAILURES if mode == 'before' else set())
                for f in r['files']: self.assertEqual(sha(z.read(mode+'/'+f['path'])), f['sha256'])
                for t in r['methods']:
                    raw = z.read(mode+'/'+t['log'])
                    self.assertEqual(sha(raw), t['log_sha256'])
                    self.assertIn(b'Test Case ', raw)
                    if mode == 'before' and 'RejectsOverflow' in t['method']:
                        self.assertEqual(t['exit_code'], -5)
                        self.assertNotIn(b'Executed 1 test', raw)
                    else:
                        self.assertIn(b'Executed 1 test', raw)
                        self.assertEqual(t['exit_code'] == 0, t['status'] == 'passed')
            r = json.loads(z.read('adjacent/result.json'))
            self.assertEqual(r['source_commit'], AFTER)
            self.assertEqual(r['driver_sha256'], sha((ROOT/'scripts/history-restart-adjacent.py').read_bytes()))
            self.assertEqual(len(r['methods']), 22)
            self.assertEqual(len(r['excluded_live_methods']), 2)
            for t in r['methods']:
                self.assertEqual(t['status'], 'passed'); self.assertEqual(t['exit_code'], 0)
                self.assertEqual(sha(z.read('adjacent/'+t['log'])), t['log_sha256'])
            for f in r['files']: self.assertEqual(sha(z.read('adjacent/'+f['path'])), f['sha256'])

    def test_hosted_previous_repairs(self):
        for folder, runid, before, after, cases, failed, adjacent in [
            ('hosted-near-balance-freshness',41622627422,'5d91d1e4dfd36c56031c7a8fb1ee305446dc54de','fd06fdff104d128e00cc414d2de1472f11752e04',6,4,24),
            ('hosted-inventory-flight-time',41626421156,'fd06fdff104d128e00cc414d2de1472f11752e04','63e0be4a10106fc577792a7fb3c6d69b1cc8870c',5,3,27)]:
            root = ROOT/'evidence/5.0.2-build104'/folder
            manifest = json.loads((root/'manifest.json').read_bytes())
            run = json.loads((root/'run.json').read_bytes()); meta = json.loads((root/'metadata.json').read_bytes())
            self.assertEqual(run['id'], runid); self.assertEqual(run['conclusion'], 'success'); self.assertEqual(run['status'], 'completed')
            self.assertEqual(run['head_sha'], manifest['audit_commit']); self.assertEqual(meta['workflow_run']['head_sha'], run['head_sha'])
            self.assertEqual(meta['digest'], 'sha256:'+sha((root/'artifact.zip').read_bytes()))
            for f in manifest['files']: self.assertEqual(sha((root/f['path']).read_bytes()), f['sha256'])
            with zipfile.ZipFile(root/'artifact.zip') as z:
                for f in manifest['expanded_files_verified']: self.assertEqual(sha(z.read(f['path'])), f['sha256'])
                for mode, pin, count, failures in [('before',before,cases,failed),('after',after,cases,0),('adjacent',after,adjacent,0)]:
                    r = json.loads(z.read(mode+'/result.json')); self.assertEqual(r['source_commit'], pin)
                    self.assertEqual(len(r['methods']), count); self.assertEqual(sum(t['status']!='passed' for t in r['methods']), failures)
                    for t in r['methods']:
                        raw = z.read(mode+'/'+t['log']); self.assertEqual(sha(raw), t['log_sha256']); self.assertIn(b'Executed 1 test',raw)
                        self.assertEqual(t['exit_code']==0, t['status']=='passed')

    def test_workflow_pins_and_network_boundary(self):
        s = (ROOT/'.github/workflows/history-restart-boundaries.yml').read_text()
        self.assertIn(BEFORE,s); self.assertIn(AFTER,s); self.assertIn('contents: read',s)
        self.assertNotIn('secrets.',s); self.assertNotIn('pull_request_target',s)
        for script in ['history-restart-boundaries.py','history-restart-adjacent.py']:
            text = (ROOT/'scripts'/script).read_text()
            self.assertIn('(deny network*)',text); self.assertIn('require_source_state',text); self.assertIn("'--build-tests'",text)
