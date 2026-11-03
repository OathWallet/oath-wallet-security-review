import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class CodecReplayContract(unittest.TestCase):
    def test_runtime_methods_are_exact(self):
        m=load('xrpl-connect-boundaries')
        self.assertEqual(len(m.METHODS),6)
        self.assertEqual(len(set(m.METHODS)),6)
        swift=(ROOT/'fixtures/xrpl-signing/WalletConnectXrplAuditBoundaryTests.swift').read_text()
        for method in m.METHODS:self.assertEqual(swift.count('func '+method+'('),1)

    def test_source_pins_and_network_denial(self):
        for name in ['xrpl-codec-provenance','xrpl-connect-boundaries']:
            m=load(name);self.assertEqual(m.COMMIT,'8a31eb265c34ef7f37ba21741201842366d43b7b')
            code=(ROOT/'scripts'/(name+'.py')).read_text()
            self.assertEqual(code.count('require_source_state(source,COMMIT)'),2)
            self.assertIn('(deny network*)',code)
        code=(ROOT/'scripts/xrpl-codec-provenance.py').read_text()
        self.assertIn('--ignore-scripts',code)
        self.assertIn("if not same:raise ValueError",code)

    def test_upstream_inventory_keeps_review_gaps(self):
        a=json.loads((ROOT/'scope/upstream-xrpl-codec.json').read_text())
        self.assertEqual(len(a['files']),170)
        self.assertEqual(len({r['path'] for r in a['files']}),170)
        self.assertTrue(all(r['status']=='outstanding' and len(r['sha256'])==64 for r in a['files']))
