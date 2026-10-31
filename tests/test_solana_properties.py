import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('solana_properties', ROOT/'scripts/solana-properties.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class SolanaHarnessTests(unittest.TestCase):
    def test_independent_base58_oracle(self):
        rows = runner.encoding_vectors()
        self.assertEqual(len(rows),528)
        self.assertEqual(rows,runner.encoding_vectors())
        alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        for row in rows:
            raw=bytes.fromhex(row['hex']); value=0
            for char in row['base58']: value=value*58+alphabet.index(char)
            self.assertEqual(value,int.from_bytes(raw,'big'))
            self.assertEqual(len(row['base58'])-len(row['base58'].lstrip('1')),len(raw)-len(raw.lstrip(b'\0')))
        self.assertEqual(rows[0],{'hex':'00','base58':'1'})
        self.assertEqual(rows[1],{'hex':'ff','base58':'5Q'})

    def test_curve_oracle_is_deterministic_and_sign_invariant(self):
        rows=runner.curve_vectors()
        self.assertEqual(len(rows),1038)
        self.assertEqual(rows,runner.curve_vectors())
        self.assertTrue(rows[0]['isPoint'])
        self.assertTrue(rows[2]['isPoint'])
        self.assertFalse(rows[4]['isPoint'])
        self.assertEqual({row['isPoint'] for row in rows},{True,False})
        for a,b in zip(rows[::2],rows[1::2]):
            self.assertEqual(a['isPoint'],b['isPoint'])
            self.assertEqual(int.from_bytes(bytes.fromhex(a['hex']),'little') ^ int.from_bytes(bytes.fromhex(b['hex']),'little'),2**255)

    def test_result_requires_each_named_case_once(self):
        for template in ["Test Case '-[SolanaAudit.SolanaAuditProductionTests {}]' passed (1.0 seconds).",
                         "Test Case 'SolanaAuditProductionTests.{}' passed (1.0 seconds)."]:
            text='\n'.join(template.format(name) for name in sorted(runner.EXPECTED))
            self.assertTrue(runner.successful(text,0))
            for bad,code in [(text,1),(text+'\n'+text,0),('\n'.join(text.splitlines()[1:]),0),('',0),('Build complete!',0)]:
                self.assertFalse(runner.successful(bad,code))
