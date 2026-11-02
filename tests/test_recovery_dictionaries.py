import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('dictionary_review',scripts/'bip39-dictionaries.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class DictionaryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.src=self.root/'OathApp/Resources/BIP39';self.src.mkdir(parents=True)
        self.app=self.root/'Product.app';self.app.mkdir()
        self.dictionary=('\n'.join(f'word{i}' for i in range(2048))+'\n').encode()
        self.entries=[]
        for lang in m.LANGUAGES:
            name='bip39_'+lang+'.txt'
            for d in (self.src,self.app):(d/name).write_bytes(self.dictionary)
            self.entries.append(dict(id=lang,count=2048,sha256=m.sha(self.dictionary),
                source=f'https://raw.githubusercontent.com/bitcoin/bips/{m.REV}/bip-0039/{lang}.txt'))
        self.manifests()
        self.git=patch.object(m.subprocess,'check_output',side_effect=lambda cmd,**kwargs:self.dictionary if 'show' in cmd else 'fake-git-blob\n')
        self.git.start();self.addCleanup(self.git.stop)

    def manifests(self):
        for d in (self.src,self.app):
            (d/'bip39_manifest.json').write_text(json.dumps({'commit':m.REV,'lists':self.entries}))

    def test_all_ten_inputs_compared(self):
        rows,_=m.check(self.root,self.app,self.root)
        self.assertEqual(sum(r['words'] for r in rows),20480)
        self.assertEqual(self.git.target.check_output.call_count,20)

    def test_bundle_reorder_rejected(self):
        p=self.app/'bip39_english.txt'
        p.write_bytes(self.dictionary.replace(b'word0\nword1\n',b'word1\nword0\n'))
        with self.assertRaisesRegex(ValueError,'Ordered dictionary differs'):m.check(self.root,self.app,self.root)

    def test_self_consistent_modified_source_and_bundle_rejected(self):
        changed=self.dictionary.replace(b'word0\nword1\n',b'word1\nword0\n')
        for d in (self.src,self.app):(d/'bip39_english.txt').write_bytes(changed)
        self.entries[0]['sha256']=m.sha(changed);self.manifests()
        with self.assertRaisesRegex(ValueError,'Ordered dictionary differs'):m.check(self.root,self.app,self.root)

    def test_missing_language_rejected(self):
        self.entries.pop();self.manifests()
        with self.assertRaisesRegex(ValueError,'dictionary manifest'):m.check(self.root,self.app,self.root)

class RecoveryIntegrationEvidenceTests(unittest.TestCase):
    def test_requires_real_suite_and_expected_coverage(self):
        from run import recovery_case_count
        self.assertEqual(recovery_case_count('aezeed','Passed 30 aezeed host integration checks: all checks.'),30)
        line='Passed 201 Electrum host integration checks across 5 formats: all checks.'
        self.assertEqual(recovery_case_count('electrum',line),201)
        for wrong in ('Build complete!', line.replace('201','1'), line.replace('5 formats','1 formats'), line+'\n'+line):
            self.assertIsNone(recovery_case_count('electrum',wrong))
