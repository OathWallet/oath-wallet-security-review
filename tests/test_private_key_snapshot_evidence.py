"""Integrity checks for the bounded synthetic snapshot experiment, not runtime reruns."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence/5.0.1-build103/private-key-snapshot'

class SnapshotEvidenceTests(unittest.TestCase):
    def test_original_snapshot_hashes(self):
        for directory in ['snapshots-before', 'snapshots-clear-model']:
            manifest = json.loads((E / directory / 'manifest.json').read_text())
            self.assertEqual(len(manifest), 4)
            for row in manifest:
                data = (E / directory / row['file']).read_bytes()
                if 'bytes' in row: self.assertEqual(len(data), row['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])

    def test_ocr_requires_foreground_and_before_positive_controls(self):
        result = json.loads((E / 'ocr.json').read_text())
        positives = {'captures/foreground', 'captures/foreground-after', 'captures/snapshot-before-2', 'captures/snapshot-before-3'}
        negatives = {f'snapshots-clear-model/{i}' for i in range(4)}
        self.assertEqual(set(result), positives | negatives)
        for name, rows in result.items():
            text = re.sub('[^A-Z]', '', ''.join(r['text'].upper() for r in rows))
            self.assertEqual('AUDITSNAPSHOTTESTNOTAPRIVATEKEY' in text, name in positives, name)

    def test_lifecycle_before_and_after_are_locked(self):
        for name, visible in [('lifecycle-before.jsonl', True), ('lifecycle-clear-model.jsonl', False)]:
            rows = [json.loads(line) for line in (E / name).read_text().splitlines()]
            ready = [r for r in rows if r['event'] == 'ready']
            self.assertEqual(len(ready), 1)
            self.assertTrue(ready[0]['has_value'])
            background = [r for r in rows if r['event'] == 'background']
            self.assertEqual(len(background), 1)
            self.assertTrue(background[0]['locked'])
            self.assertFalse(background[0]['unlocked'])
            self.assertEqual(background[0]['has_value'], visible)
            self.assertEqual(background[0]['revealed'], visible)

    def test_host_and_build_logs_match_receipts(self):
        for name in ['host-after', 'host-multiwallet', 'validation/build', 'validation/public', 'validation/OathDiagnostics', 'validation/diagnostics-coverage']:
            row = json.loads((E / (name+'.json')).read_text())
            data = gzip.decompress((E / (name+'.log.gz')).read_bytes())
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['log_sha256'])
            self.assertEqual(row['source_commit'], 'b5621109b64d606dcf6cd906d2c4f2c2f9e78686')
            self.assertEqual(row['exit_code'], 0)

    def test_repair_model_hash_and_cleanup(self):
        match = json.loads((E / 'model-match.json').read_text())
        self.assertEqual(match['runtime_trial_model_sha256'], match['candidate_model_sha256'])
        self.assertNotEqual(match['baseline_model_sha256'], match['candidate_model_sha256'])
        self.assertTrue(json.loads((E / 'device.json').read_text())['shut_down_and_deleted'])

    def test_original_host_failure_is_preserved(self):
        log = gzip.decompress((E / 'host-before-flushed.log.gz').read_bytes()).decode()
        self.assertEqual(len(re.findall('^PASS:', log, re.M)), 7)
        self.assertEqual(len(re.findall('^FAIL:', log, re.M)), 4)
        self.assertEqual(json.loads((E / 'host-before-exit.json').read_text())['exit_code'], 1)

if __name__ == '__main__': unittest.main()
