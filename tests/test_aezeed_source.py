import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from aezeed_source import prepared_bridge


class PreparedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bridge = self.root/'Tools/AezeedBridge'
        self.bridge.mkdir(parents=True)
        self.manifest = {'patch_sha256': 'fixture-patch', 'files': []}
        (self.bridge/'DependencyRepairs.json').write_text(json.dumps(self.manifest))

    def prepare(self, mutation=None, code=0, expired=False):
        (self.bridge/'prepare_source.py').write_text('# fixture preparer')
        def run(command, **kwargs):
            output = Path(command[-1])
            selected = output/'Tools/AezeedBridge'
            selected.mkdir(parents=True)
            (selected/'main.go').write_bytes(b'public fixture')
            manifest = {'patch_sha256': 'fixture-patch', 'repairs': [],
                        'vendor_files': {}, 'source_files': {'main.go': hashlib.sha256(b'public fixture').hexdigest()}}
            if mutation:
                mutation(selected, manifest)
            (output/'prepared-source.json').write_text(json.dumps(manifest))
            return code, expired
        return patch('aezeed_source.logged_command', side_effect=run)

    def test_original_source_keeps_original_path(self):
        with prepared_bridge(self.root) as (selected, manifest):
            self.assertEqual(selected, self.bridge)
            self.assertIsNone(manifest)

    def test_prepared_source_and_evidence(self):
        out = self.root/'evidence'
        with self.prepare(), prepared_bridge(self.root, out) as (selected, manifest):
            self.assertEqual((selected/'main.go').read_bytes(), b'public fixture')
            self.assertEqual(json.loads((out/'prepared-source.json').read_text()), manifest)

    def test_failed_and_expired_preparation_rejected(self):
        for code, expired in [(1, False), (0, True)]:
            with self.subTest(code=code, expired=expired), self.prepare(code=code, expired=expired):
                with self.assertRaises(RuntimeError), prepared_bridge(self.root):
                    self.fail('Unsuccessful preparation was accepted')

    def test_mismatched_repair_identity_rejected(self):
        for key, value in [('patch_sha256', 'changed'), ('repairs', [{'unexpected': True}])]:
            with self.subTest(key=key), self.prepare(lambda selected, manifest: manifest.update({key: value})):
                with self.assertRaises(ValueError), prepared_bridge(self.root):
                    self.fail('Mismatched repair was accepted')

    def test_modified_missing_and_extra_files_rejected(self):
        mutations = [lambda p, m: (p/'main.go').write_bytes(b'changed'),
                     lambda p, m: (p/'main.go').unlink(),
                     lambda p, m: (p/'extra.go').write_bytes(b'extra')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.prepare(mutation):
                with self.assertRaises(ValueError), prepared_bridge(self.root):
                    self.fail('Uninventoried source was accepted')

    def test_mutation_during_validation_rejected(self):
        with self.prepare():
            with self.assertRaises(ValueError):
                with prepared_bridge(self.root) as (selected, manifest):
                    (selected/'main.go').write_bytes(b'changed after entry')


if __name__ == '__main__':
    unittest.main()
