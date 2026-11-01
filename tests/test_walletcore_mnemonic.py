import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('mnemonic_review',Path(__file__).resolve().parents[1]/'scripts/walletcore-mnemonic.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class MnemonicVectorTests(unittest.TestCase):
 def words(self):
  # First known-answer vector needs indices 0 and 3. Other names are synthetic;
  # this test checks generator boundaries, not the production English wordlist.
  return ['abandon','ability','able','about']+[f'fixture{i}' for i in range(4,2048)]
 def test_generator_boundaries(self):
  rows=module.make_vectors(self.words())
  self.assertEqual(len(rows),150)
  self.assertEqual({len(bytes.fromhex(r['entropy'])) for r in rows},{16,20,24,28,32})
  self.assertTrue(all(len(bytes.fromhex(r['seed']))==64 for r in rows))
  self.assertTrue(all(len(bytes.fromhex(r['password']))<=256 for r in rows))
  self.assertEqual(rows[3]['password'],'65cc81')
 def test_incomplete_or_duplicate_words_rejected(self):
  for words in [[],self.words()[:-1],['abandon']*2048]:
   with self.assertRaises(ValueError):module.make_vectors(words)
 def test_kdf_oracles_cover_both_digests_and_multiple_blocks(self):
  rows=module.make_kdf_vectors()
  self.assertEqual(len(rows),530)
  self.assertEqual(sum(r['kind']==0 for r in rows),242)
  self.assertEqual(sum(r['kind']==1 for r in rows),288)
  self.assertEqual({r['algorithm'] for r in rows},{'sha256','sha512'})
  self.assertEqual({len(bytes.fromhex(r['expected'])) for r in rows if r['kind']==1},{1,31,32,33,63,64,65,129})
