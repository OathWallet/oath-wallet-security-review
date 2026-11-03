import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/'evidence/5.0.1-build103/connect-removal'
class EvidenceIntegrity(unittest.TestCase):
    def test_manifest_and_expanded_logs(self):
        m=json.loads((ROOT/'manifest.json').read_text())
        self.assertGreater(len(m['files']),1900)
        for name,item in m['files'].items():
            raw=(ROOT/name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'],name)
            expanded=gzip.decompress(raw) if name.endswith('.gz') else raw
            self.assertEqual(hashlib.sha256(expanded).hexdigest(),item['uncompressed_sha256'],name)

    def test_exact_final_source_and_case_statuses(self):
        m=json.loads((ROOT/'manifest.json').read_text())
        for check in ['public','diagnostics-coverage','build','OathDatabase','OathDiagnostics']:
            r=json.loads((ROOT/'final-validation'/f'{check}.json').read_text())
            self.assertEqual(r['source_commit'],m['after']);self.assertEqual(r['status'],'passed')
        for package,expected in [('OathDatabase',{'passed':744,'skipped':72}),('OathDiagnostics',{'passed':119,'skipped':2})]:
            from collections import Counter
            cases=json.loads((ROOT/'final-validation'/f'{package}-cases.json').read_text())
            self.assertEqual(dict(Counter(c['status'] for c in cases)),expected)

    def test_three_replay_pins_and_failures_remain(self):
        m=json.loads((ROOT/'manifest.json').read_text())
        for phase,count,fail in [('before',4,2),('compatibility',1,1),('after',5,0)]:
            r=json.loads((ROOT/'replay'/phase/'result.json').read_text())
            self.assertEqual(r['source_commit'],m[phase])
            self.assertEqual(len(r['cases']),count)
            self.assertEqual(sum(c['status']=='failed' for c in r['cases']),fail)
            for c in r['cases']:
                p=ROOT/'replay'/phase/(c['log']+'.gz')
                self.assertEqual(hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest(),c['log_sha256'])
