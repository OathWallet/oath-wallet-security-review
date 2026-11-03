import gzip
import hashlib
import json
from pathlib import Path
import unittest

E=Path(__file__).resolve().parents[1]/'evidence/5.0.1-build103/xrpl-codec'
class CodecEvidence(unittest.TestCase):
    def test_evidence_hashes(self):
        m=json.loads((E/'manifest.json').read_text())
        for name,r in m['files'].items():
            data=(E/name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'],name)
            self.assertEqual(len(data),r['bytes'],name)
            raw=gzip.decompress(data) if name.endswith('.gz') else data
            self.assertEqual(hashlib.sha256(raw).hexdigest(),r['uncompressed_sha256'],name)

    def test_provenance_and_runtime_remain_distinct(self):
        p=json.loads((E/'provenance-final/result.json').read_text())
        self.assertTrue(p['byte_identical'])
        self.assertEqual(p['shipped_bundle_sha256'],p['rebuilt_bundle_sha256'])
        self.assertEqual(len(p['inputs']),171)
        self.assertEqual(sum(x['package'] is not None for x in p['inputs']),170)
        self.assertTrue(all(x['bytes_in_output']>0 for x in p['inputs']))
        self.assertEqual(len(p['packages']),11)
        r=json.loads((E/'replay/result.json').read_text())
        self.assertEqual(r['source_commit'],p['source_commit'])
        self.assertEqual(len(r['methods']),6)
        self.assertTrue(all(x['status']=='passed' and x['exit_code']==0 for x in r['methods']))
        self.assertEqual(r['runtime_network'],'denied by sandbox-exec')
