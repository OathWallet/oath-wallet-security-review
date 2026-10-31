import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from bounded_process import logged_command

class BoundedProcessTests(unittest.TestCase):
    def test_preserves_success_and_failure_exit_codes(self):
        with tempfile.TemporaryFile(mode='w+') as stream:
            for code in [0,7]:
                result=logged_command([sys.executable,'-c',f'print("fixture"); raise SystemExit({code})'],stream=stream,timeout=5)
                self.assertEqual(result,(code,False))
            stream.seek(0);self.assertEqual(stream.read().count('fixture'),2)

    @unittest.skipUnless(os.name=='posix','Private process groups require POSIX')
    def test_timeout_kills_child_and_retains_failure_evidence(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryFile(mode='w+') as stream:
            path=Path(temporary)/'child-completed'
            child=f'import time; from pathlib import Path; print("child ready",flush=True); time.sleep(5); Path({str(path)!r}).write_text("unexpected")'
            parent=f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); print("child started",flush=True); time.sleep(30)'
            self.assertEqual(logged_command([sys.executable,'-c',parent],stream=stream,timeout=3),(124,True))
            time.sleep(5.2)
            self.assertFalse(path.exists())
            stream.seek(0);text=stream.read()
            self.assertIn('child started',text)
            self.assertIn('child ready',text)
            self.assertIn('AUDIT TEST TIMEOUT',text)
