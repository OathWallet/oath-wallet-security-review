import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('source_state', Path(__file__).resolve().parents[1]/'scripts/source_state.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SourceStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Synthetic fixture')
        (self.root/'fixture.swift').write_text('let fixture = 1\n')
        (self.root/'.gitignore').write_text('.build/\n')
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'Synthetic baseline')
        self.sha = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True)

    def test_clean_exact_revision(self):
        self.assertEqual(module.require_source_state(self.root, self.sha), self.sha)

    def test_wrong_revision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'revision'):
            module.require_source_state(self.root, '0'*40)

    def test_modified_tracked_input_is_rejected(self):
        (self.root/'fixture.swift').write_text('let fixture = 2\n')
        with self.assertRaisesRegex(ValueError, 'inputs'):
            module.require_source_state(self.root, self.sha)

    def test_untracked_compilable_input_is_rejected(self):
        (self.root/'extra.swift').write_text('let extra = 3\n')
        with self.assertRaisesRegex(ValueError, 'inputs'):
            module.require_source_state(self.root, self.sha)

    def test_ignored_build_output_does_not_change_source_identity(self):
        (self.root/'.build').mkdir()
        (self.root/'.build'/'output.o').write_bytes(b'fixture')
        self.assertEqual(module.require_source_state(self.root, self.sha), self.sha)
