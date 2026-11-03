import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('audit_checkout', ROOT / 'scripts/checkout.py')
checkout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkout)


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'upstream'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic Test')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'source.txt').write_text('original\n')
        self.git('add', 'source.txt')
        self.git('commit', '-qm', 'synthetic source')
        self.pin = self.git('rev-parse', 'HEAD').strip()
        self.dest = self.root / 'workspace/source'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def prepare(self, **kwargs):
        return checkout.checkout(str(self.repo), self.pin, self.dest, **kwargs)

    def test_clean_checkout_pins_requested_commit_and_retains_history(self):
        (self.repo / 'source.txt').write_text('later\n')
        self.git('commit', '-qam', 'later source')
        later = self.git('rev-parse', 'HEAD').strip()
        self.assertEqual(self.prepare(), self.pin)
        self.assertEqual((self.dest / 'source.txt').read_text(), 'original\n')
        subprocess.run(['git', '-C', str(self.dest), 'cat-file', '-e', later], check=True)
        self.assertEqual(self.prepare(), self.pin)

    def test_dirty_existing_checkout_is_rejected_without_altering_it(self):
        self.prepare()
        (self.dest / 'source.txt').write_text('do not overwrite\n')
        with self.assertRaisesRegex(ValueError, 'modified or untracked'):
            self.prepare()
        self.assertEqual((self.dest / 'source.txt').read_text(), 'do not overwrite\n')

    def test_wrong_existing_revision_is_preserved(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'Wrong source revision'):
            checkout.checkout(str(self.repo), '0' * 40, self.dest)
        self.assertEqual((self.dest / 'source.txt').read_text(), 'original\n')

    def test_partial_failed_clone_is_not_published_or_reused(self):
        original = subprocess.run
        attempts = []
        def run(args, **kwargs):
            if args[:2] == ['git', 'clone']:
                attempts.append(args[-1])
                self.assertFalse(self.dest.exists())
                if len(attempts) == 1:
                    partial = Path(args[-1]); partial.mkdir()
                    (partial / 'partial.txt').write_text('incomplete')
                    raise subprocess.CalledProcessError(128, args)
            return original(args, **kwargs)
        with patch.object(checkout.subprocess, 'run', side_effect=run):
            self.prepare()
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(*attempts)
        self.assertFalse((self.dest / 'partial.txt').exists())
        self.assertFalse(list(self.dest.parent.glob('.source-download-*')))

    def test_timeouts_are_bounded_and_leave_no_ready_source(self):
        original = subprocess.run
        calls = []
        def run(args, **kwargs):
            if args[:2] == ['git', 'clone']:
                calls.append(args)
                self.assertEqual(kwargs['timeout'], 7)
                raise subprocess.TimeoutExpired(args, 7)
            return original(args, **kwargs)
        with patch.object(checkout.subprocess, 'run', side_effect=run):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.prepare(attempts=3, timeout=7)
        self.assertEqual(len(calls), 3)
        self.assertFalse(self.dest.exists())
        self.assertFalse(list(self.dest.parent.glob('.source-download-*')))

    def test_bad_pin_is_not_retried_as_network_failure(self):
        original = subprocess.run
        clones = []
        def run(args, **kwargs):
            if args[:2] == ['git', 'clone']: clones.append(args)
            return original(args, **kwargs)
        with patch.object(checkout.subprocess, 'run', side_effect=run):
            with self.assertRaises(subprocess.CalledProcessError):
                checkout.checkout(str(self.repo), '0' * 40, self.dest)
        self.assertEqual(len(clones), 1)
        self.assertFalse(self.dest.exists())

    def test_new_destination_during_download_is_preserved(self):
        original = subprocess.run
        def run(args, **kwargs):
            result = original(args, **kwargs)
            if len(args) > 4 and args[3] == 'checkout':
                self.dest.mkdir()
                (self.dest / 'user.txt').write_text('preserve')
            return result
        with patch.object(checkout.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(ValueError, 'appeared during download'):
                self.prepare()
        self.assertEqual((self.dest / 'user.txt').read_text(), 'preserve')

    def test_zero_attempts_cannot_report_success(self):
        with self.assertRaisesRegex(ValueError, 'At least one'):
            self.prepare(attempts=0)
        self.assertFalse(self.dest.exists())


if __name__ == '__main__':
    unittest.main()
