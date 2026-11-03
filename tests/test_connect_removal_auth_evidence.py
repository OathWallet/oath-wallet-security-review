import gzip
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'evidence/5.0.1-build103/connect-removal-auth'
class Evidence(unittest.TestCase):
    def test_retained_files_match(self):
        m=json.loads((P/'manifest.json').read_text())
        for name,item in m['files'].items():
            raw=(P/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'],name)
            if name.endswith('.gz'):raw=gzip.decompress(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['uncompressed_sha256'],name)
    def test_replay_and_mutant_bind_to_same_source_and_fixture(self):
        a=json.loads((P/'replay/result.json').read_text());b=json.loads((P/'mutant/result.json').read_text())
        for key in ['source_commit','source_sha256','fixture_sha256','script_sha256','harness_original_sha256','harness_executed_sha256']:
            self.assertEqual(a[key],b[key],key)
        self.assertEqual(a['compiled_vault_sha256'],a['source_sha256'])
        self.assertNotEqual(b['compiled_vault_sha256'],b['source_sha256'])
        for phase,r,failed in [('replay',a,0),('mutant',b,2)]:
            self.assertEqual(len(r['cases']),38);self.assertEqual(sum(c['status']=='fail' for c in r['cases']),failed)
            self.assertEqual(hashlib.sha256(gzip.decompress((P/phase/'checks.log.gz').read_bytes())).hexdigest(),r['log_sha256'])
        self.assertEqual(a['fixture_sha256'],hashlib.sha256((ROOT/'fixtures/connect-removal-auth/Checks.swift').read_bytes()).hexdigest())
        self.assertEqual(a['script_sha256'],hashlib.sha256((ROOT/'scripts/connect-removal-auth.py').read_bytes()).hexdigest())
    def test_baseline_selected_text_binding(self):
        r=json.loads((P/'source-traces.json').read_text());self.assertEqual(len(r['functions']),11)
        for f in r['functions']:
            self.assertTrue(f['identical_selected_text']);self.assertEqual(f['sources']['baseline']['sha256'],f['sources']['tested']['sha256'])
