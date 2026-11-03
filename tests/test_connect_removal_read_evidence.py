import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/5.0.2-build104/connect-removal-read'
PIN = '0614556b993f85808b13e3a69984ce36050a8dfe'
def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

class Evidence(unittest.TestCase):
    def test_archive_hashes(self):
        for directory in ['attempts', 'validation']:
            root = EVIDENCE / directory
            entries = read(root / 'manifest.json')['files']
            self.assertEqual(len({e['path'] for e in entries}), len(entries))
            for entry in entries:
                self.assertEqual(digest(root / entry['path']), entry['published_sha256'], entry['path'])
        for entry in read(EVIDENCE / 'supplemental-manifest.json')['files']:
            self.assertEqual(digest(EVIDENCE / entry['path']), entry['published_sha256'])

    def test_exact_focused_receipts_and_executed_drivers(self):
        for directory, driver, fixture, count in [
            ('final-v2', 'connect-removal-read.py', 'Checks.swift', 66),
            ('pending-consent-fixed', 'pending-consent-removal.py', 'PendingConsent.swift', 14),
        ]:
            data = read(EVIDENCE / 'validation' / directory / 'result.json')
            self.assertEqual(data['source_commit'], PIN)
            self.assertEqual(data['exit_code'], 0)
            self.assertEqual(len(data['cases']), count)
            self.assertTrue(all(case['status'] == 'pass' for case in data['cases']))
            self.assertEqual(data['script_sha256'], digest(EVIDENCE / 'executed-drivers' / driver))
            self.assertEqual(data['fixture_sha256'], digest(ROOT / 'fixtures/connect-removal-read' / fixture))
            self.assertEqual(data['runtime_network'], 'denied')

    def test_all_broader_receipts(self):
        manifest = read(EVIDENCE / 'validation/manifest.json')
        checks = manifest['broader_host_checks']
        self.assertEqual({c['check'] for c in checks}, set('evm-send walletconnect permission-batch solana-send tron-send xrpl-send stellar-send aptos-send sui-send near-send ton-send thorchain-send arc-send lifecycle authentication'.split()))
        self.assertEqual(sum(c['assertions'] for c in checks), 616)
        for check in checks:
            receipt = read(EVIDENCE / 'validation/final-v2-host-regressions' / (check['check'] + '.json'))
            self.assertEqual(receipt['source_commit'], PIN)
            self.assertEqual(receipt['status'], 'passed')
            self.assertEqual(receipt['exit_code'], 0)
            self.assertEqual(receipt['summaries'], check['summary'])

    def test_merge_changes_are_website_only_and_historical_pin_preserved(self):
        binding = read(EVIDENCE / 'merge-binding.json')
        self.assertEqual(binding['tested_commit'], PIN)
        self.assertEqual(binding['merged_commit'], '501915920e99475e63af5fcb9e658f3c834f3cc8')
        self.assertTrue(binding['changed_paths'])
        self.assertTrue(all(path.startswith('Website/') for path in binding['changed_paths']))
        self.assertEqual(read(ROOT / 'scope/source.json')['baseline_commit'], '0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d')
