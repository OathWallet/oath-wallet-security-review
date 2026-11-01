import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

scripts=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('release_inputs',scripts/'release-inputs.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class CompilerDependencyTests(unittest.TestCase):
    def test_continued_lines_and_escaped_spaces_remain_one_filename(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'fixture.d'
            p.write_text('dependencies: \\\n  /tmp/first.h \\\n  /tmp/with\\ space/header.h\n')
            self.assertEqual(runner.c_dependencies(p), [Path('/tmp/first.h'),Path('/tmp/with space/header.h')])
            p.write_text('truncated dependency list')
            with self.assertRaises(ValueError):runner.c_dependencies(p)
