import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
E = ROOT/'evidence/5.0.1-build103/xrpl-connect-simulation'

class SimulationEvidence(unittest.TestCase):
    def test_file_hashes_and_source_identity(self):
        a = json.loads((E/'manifest.json').read_text())
        self.assertTrue(a['before_client_matches_baseline'])
        self.assertTrue(a['identical_tests_before_after'])
        for name, expected in a['files'].items():
            data=(E/name).read_bytes()
            self.assertEqual(len(data), expected['bytes'], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected['sha256'], name)
            raw=gzip.decompress(data) if name.endswith('.gz') else data
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected['uncompressed_sha256'], name)

    def test_paired_replay_and_validation(self):
        a=json.loads((E/'manifest.json').read_text())
        for phase in ['before','after']:
            r=json.loads((E/'replay'/phase/'result.json').read_text())
            self.assertEqual(r['source_commit'],a[phase])
            self.assertEqual(len(r['cases']),6)
            self.assertEqual(sum(c['status']=='failed' for c in r['cases']),2 if phase=='before' else 0)
            self.assertEqual(sum(c['status']=='passed' for c in r['cases']),4 if phase=='before' else 6)
        exits=json.loads((E/'validation/driver-exits.json').read_text())
        self.assertEqual(exits,dict(public=0,**{'diagnostics-coverage':0,'OathDiagnostics':0,'build':0,'gitleaks':0}))
        for check in ['public','diagnostics-coverage','OathDiagnostics','build']:
            r=json.loads((E/'validation'/(check+'.json')).read_text())
            self.assertEqual(r['source_commit'],a['after'])
            self.assertEqual(r['status'],'passed')
