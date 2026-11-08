import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence/5.0.3-build105/late-authentication'


class CancellationSourceTrace(unittest.TestCase):
    def test_exact_inputs_and_unexecuted_scope_remain_explicit(self):
        record = json.loads((E / 'cancellation-trace.json').read_text())
        self.assertEqual(record['application_commit'], 'a9c062a3a1d492799b9f6e9d083630c7006183ea')
        self.assertEqual(record['dependency']['state']['revision'], '533286eab041d826ed4a46c56b213fa3d2cebb7a')
        self.assertTrue(record['manual_source_trace'])
        self.assertFalse(record['runtime_test_performed'])
        self.assertTrue(record['frozen_inventory_unchanged'])
        self.assertEqual(len(record['files']), 7)
        with zipfile.ZipFile(E / 'cancellation-trace-source.zip') as archive:
            self.assertEqual(set(archive.namelist()), {f['archive_path'] for f in record['files']})
            for file in record['files']:
                data = archive.read(file['archive_path'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), file['sha256'])
                self.assertEqual(file['status'], 'partially-reviewed')
                expected_commit = record['application_commit'] if file['kind'] == 'application' else record['dependency']['state']['revision']
                self.assertEqual(file['source_commit'], expected_commit)
                self.assertTrue(file['reviewed_ranges'])
                for start, end in file['reviewed_ranges']:
                    self.assertTrue(1 <= start <= end <= len(data.splitlines()))

    def test_solana_followup_does_not_claim_new_runtime_coverage(self):
        record = json.loads((E / 'solana-followup.json').read_text())
        self.assertEqual(record['application_commit'], 'a9c062a3a1d492799b9f6e9d083630c7006183ea')
        self.assertTrue(record['manual_source_trace'])
        self.assertTrue(record['frozen_inventory_unchanged'])
        self.assertEqual(record['new_runtime_tests'], 0)
        self.assertEqual(len(record['files']), 4)
        with zipfile.ZipFile(E / 'solana-followup-source.zip') as archive:
            self.assertEqual(set(archive.namelist()), {f['path'] for f in record['files']})
            for file in record['files']:
                data = archive.read(file['path'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), file['sha256'])
                self.assertEqual(file['status'], 'partially-reviewed')
                for start, end in file['reviewed_ranges']:
                    self.assertTrue(1 <= start <= end <= len(data.splitlines()))
        current = json.loads((E / 'publication-source-status.json').read_text())
        self.assertEqual(current['reviewed_application_commit'], record['application_commit'])
        self.assertTrue(current['application_inputs_identical'])
        objects = current['non_website_root_objects']
        self.assertEqual(objects[current['reviewed_application_commit']], objects[current['observed_main_commit']])

    def test_swap_source_reads_preserve_runtime_gaps(self):
        record = json.loads((E / 'swap-followup.json').read_text())
        self.assertEqual(record['application_commit'], 'a9c062a3a1d492799b9f6e9d083630c7006183ea')
        self.assertTrue(record['manual_source_trace'])
        self.assertTrue(record['frozen_inventory_unchanged'])
        self.assertEqual(record['new_runtime_tests'], 0)
        self.assertEqual(record['confirmed_findings'], [])
        self.assertEqual(len(record['files']), 2)
        with zipfile.ZipFile(E / 'swap-followup-source.zip') as archive:
            self.assertEqual(set(archive.namelist()), {f['path'] for f in record['files']})
            for file in record['files']:
                data = archive.read(file['path'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), file['sha256'])
                self.assertEqual(file['status'], 'partially-reviewed')
                self.assertTrue(file['limitations'])
                for start, end in file['reviewed_ranges']:
                    self.assertTrue(1 <= start <= end <= len(data.splitlines()))
