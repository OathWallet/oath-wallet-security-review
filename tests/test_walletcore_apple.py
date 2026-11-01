import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('walletcore_apple', ROOT/'scripts/walletcore-apple.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class AppleArtifactTests(unittest.TestCase):
    def test_zip_preserves_files_and_executable_mode_without_machine_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'Framework';source.mkdir()
            binary = source/'Core';binary.write_bytes(b'public synthetic binary');binary.chmod(0o755)
            (source/'._Core').write_bytes(b'metadata')
            output = root/'archive.zip'
            module.archive_tree(source, output, 'Core.framework')
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ['Core.framework/Core'])
                self.assertEqual(archive.read('Core.framework/Core'), binary.read_bytes())
                info = archive.getinfo('Core.framework/Core')
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o755)
                self.assertEqual(info.date_time, (2026,1,1,0,0,0))

    def test_symlink_file_or_directory_is_rejected(self):
        for is_directory in [False, True]:
            with self.subTest(is_directory=is_directory), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root/'Framework';source.mkdir()
                target = root/'outside'
                if is_directory:
                    target.mkdir();(target/'file').write_bytes(b'outside')
                else:
                    target.write_bytes(b'outside')
                (source/'link').symlink_to(target, target_is_directory=is_directory)
                with self.assertRaises(ValueError):
                    module.archive_tree(source, root/'archive.zip', 'Core.framework')

    def test_zip_bytes_repeat_for_identical_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'Framework';source.mkdir()
            (source/'Core').write_bytes(b'synthetic')
            for name in ['first.zip','second.zip']:
                module.archive_tree(source, root/name, 'Core.framework')
            self.assertEqual((root/'first.zip').read_bytes(), (root/'second.zip').read_bytes())
