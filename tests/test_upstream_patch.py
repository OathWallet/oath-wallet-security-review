"""Integrity gates around disposable dependency patch checks."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import upstream_patch

class PatchedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.source=self.root/'repo';self.source.mkdir()
        self.git('init','-q');self.git('config','user.name','Audit Fixture');self.git('config','user.email','audit@example.invalid')
        (self.source/'value.txt').write_text('before\n');self.git('add','value.txt');self.git('commit','-qm','fixture')
        self.pin=self.git('rev-parse','HEAD').strip()
        (self.source/'value.txt').write_text('after\n')
        self.patch=self.root/'repair.patch';self.patch.write_text(self.git('diff'))
        self.git('checkout','--','value.txt')
        self.mock=patch.object(upstream_patch,'PATCH',self.patch);self.mock.start();self.addCleanup(self.mock.stop)
    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.source),*args],text=True)
    def test_baseline_is_unmodified(self):
        with upstream_patch.upstream_source(self.source,self.pin) as (source,metadata):
            self.assertEqual(source,self.source);self.assertIsNone(metadata)
    def test_patch_only_applies_to_disposable_checkout(self):
        with upstream_patch.upstream_source(self.source,self.pin,True) as (source,metadata):
            self.assertNotEqual(source,self.source);self.assertEqual((source/'value.txt').read_text(),'after\n')
            self.assertEqual((self.source/'value.txt').read_text(),'before\n')
            self.assertFalse(metadata['incorporated_in_shipped_framework'])
            self.assertEqual(len(metadata['patch_sha256']),64)
        self.assertFalse(source.exists());self.assertEqual(self.git('status','--porcelain'),'')
    def test_wrong_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError,'Wrong source revision'):
            with upstream_patch.upstream_source(self.source,'0'*40,True):pass
    def test_dirty_baseline_rejected(self):
        (self.source/'extra.c').write_text('untracked')
        with self.assertRaisesRegex(ValueError,'modified or untracked'):
            with upstream_patch.upstream_source(self.source,self.pin,True):pass
    def test_changed_patched_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'changed during validation'):
            with upstream_patch.upstream_source(self.source,self.pin,True) as (source,_):
                (source/'value.txt').write_text('unexpected\n')
    def test_new_untracked_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'Untracked inputs'):
            with upstream_patch.upstream_source(self.source,self.pin,True) as (source,_):
                (source/'extra.c').write_text('unexpected\n')
    def test_changed_patch_rejected(self):
        with self.assertRaisesRegex(ValueError,'Published patch changed'):
            with upstream_patch.upstream_source(self.source,self.pin,True):
                self.patch.write_text('changed')

if __name__=='__main__':unittest.main()
