import hashlib
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from zipfile import ZipFile

path = Path(__file__).resolve().parents[1] / 'scripts/bdk-distribution.py'
spec = importlib.util.spec_from_file_location('bdk', path)
bdk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bdk)


class BDKDistributionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.resolved = base / 'framework'
        self.resolved.mkdir()
        self.library = self.resolved / 'lib.a'
        self.library.write_bytes(b'synthetic library')
        self.archive = base / 'fixture.zip'
        with ZipFile(self.archive, 'w') as archive:
            archive.writestr('bdkFFI.xcframework/lib.a', self.library.read_bytes())
        self.pin = hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def compare(self):
        with mock.patch.object(bdk, 'PIN', self.pin):
            return bdk.compare(self.archive, self.resolved)

    def test_exact_match(self):
        self.assertEqual(self.compare()['members'], {'lib.a': hashlib.sha256(self.library.read_bytes()).hexdigest()})

    def test_extra_missing_and_modified_installed_members(self):
        (self.resolved / 'other').write_text('extra')
        with self.assertRaises(ValueError):
            self.compare()
        (self.resolved / 'other').unlink()
        self.library.write_text('unexpected')
        with self.assertRaises(ValueError):
            self.compare()
        self.library.unlink()
        with self.assertRaises(ValueError):
            self.compare()

    def test_archive_digest_rejected_before_contents(self):
        with self.assertRaisesRegex(ValueError, 'archive SHA-256'):
            bdk.compare(self.archive, self.resolved)
