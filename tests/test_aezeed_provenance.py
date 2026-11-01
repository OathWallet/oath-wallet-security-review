import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))

spec = importlib.util.spec_from_file_location('provenance', Path(__file__).resolve().parents[1]/'scripts/aezeed-provenance.py')
provenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provenance)


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in [provenance.BRIDGE/'main.go', provenance.FRAMEWORK/'lib.a']:
            target = self.root/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'public synthetic fixture')
        manifest = {'input_hashes': {str(provenance.BRIDGE/p): h for p, h in provenance.hashes(self.root/provenance.BRIDGE).items()},
                    'framework_files': provenance.hashes(self.root/provenance.FRAMEWORK)}
        (self.root/'Packages/OathAezeed/BuildProvenance.json').write_text(json.dumps(manifest))

    def test_exact_match(self):
        self.assertEqual(len(provenance.verify_manifest(self.root)['input_hashes']), 1)

    def test_modified_input_rejected(self):
        (self.root/provenance.BRIDGE/'main.go').write_bytes(b'changed')
        with self.assertRaises(ValueError): provenance.verify_manifest(self.root)

    def test_modified_binary_rejected(self):
        (self.root/provenance.FRAMEWORK/'lib.a').write_bytes(b'changed')
        with self.assertRaises(ValueError): provenance.verify_manifest(self.root)

    def test_extra_or_missing_file_rejected(self):
        path = self.root/provenance.BRIDGE/'extra.go'
        path.write_bytes(b'new source')
        with self.assertRaises(ValueError): provenance.verify_manifest(self.root)
        path.unlink()
        (self.root/provenance.FRAMEWORK/'lib.a').unlink()
        with self.assertRaises(ValueError): provenance.verify_manifest(self.root)

    def test_symlink_rejected(self):
        (self.root/provenance.BRIDGE/'alias.go').symlink_to('main.go')
        with self.assertRaises(ValueError): provenance.verify_manifest(self.root)
