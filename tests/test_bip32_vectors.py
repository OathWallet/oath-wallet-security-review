import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from bip32_vectors import generate, child


class BIP32Oracle(unittest.TestCase):
    def setUp(self):
        self.official = json.loads((ROOT/'tests/fixtures/slip10-vectors.json').read_text())

    def test_standard_anchors_and_deterministic_boundary_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.assertEqual(generate(self.official['rows'], out), dict(official=52, independent_hardened=1920, oracle_anchors=33))
            first = (out/'oracle-vectors.json').read_bytes()
            rows = json.loads(first)['rows']
            self.assertEqual({len(bytes.fromhex(r['seed'])) for r in rows}, {16,32,64})
            self.assertEqual({len(r['indices']) for r in rows}, set(range(6)))
            self.assertEqual(len({r['curve'] for r in rows}), 5)
            indices = {i for r in rows for i in r['indices']}
            self.assertTrue({0x80000000,0xffffffff,0x80000001,0xfffffffe} <= indices)
            generate(self.official['rows'], out)
            self.assertEqual(first, (out/'oracle-vectors.json').read_bytes())

    def test_corrupted_standard_anchor_rejects_oracle(self):
        self.official['rows'][0]['private'] = '00'*32
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AssertionError):
                generate(self.official['rows'], Path(directory))

    def test_nonhardened_is_not_silently_tested_by_hardened_oracle(self):
        with self.assertRaises(AssertionError):
            child(bytes(32), bytes(32), 0x7fffffff, 'ed25519')


if __name__ == '__main__':
    unittest.main()
