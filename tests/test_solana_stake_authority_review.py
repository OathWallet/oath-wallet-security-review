import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence/5.0.3-build105/solana-stake-authority'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('solana_stake_authority_review', ROOT / 'scripts/solana-stake-authority-review.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class SolanaStakeAuthorityEvidence(unittest.TestCase):
    def result(self):
        z = zipfile.ZipFile(E / 'runs.zip')
        self.addCleanup(z.close)
        checks = json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()), {f['path'] for f in checks} | {'CHECKSUMS.json'})
        self.assertEqual(len(z.namelist()), len(checks) + 1)
        for f in checks:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        r = json.loads(z.read('result.json'))
        self.assertEqual(r['baseline_commit'], driver.BEFORE)
        self.assertEqual(r['retest_commit'], driver.AFTER)
        self.assertEqual(r['fix_commit'], driver.AFTER)
        self.assertEqual(r['driver_sha256'], sha((ROOT / 'scripts/solana-stake-authority-review.py').read_bytes()))
        self.assertEqual(r['fixture_sha256'], sha((ROOT / r['fixture']).read_bytes()))
        self.assertEqual(r['corpus_sha256'], sha((ROOT / r['corpus']).read_bytes()))
        for name, digest in r['helper_sha256'].items():
            self.assertEqual(digest, sha((ROOT / 'scripts' / name).read_bytes()))
        for f in r['files']:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z, r

    def test_clean_paired_builds_use_identical_fixture_and_distinct_executables(self):
        z, r = self.result()
        self.assertEqual([s['stage'] for s in r['stages']], ['before', 'after'])
        self.assertEqual(len({s['executable_sha256'] for s in r['stages']}), 2)
        for s in r['stages']:
            self.assertEqual(s['build_exit_code'], 0)
            self.assertEqual(s['runtime_network'], 'denied')
            self.assertEqual(s['fixture_sha256'], r['fixture_sha256'])
            self.assertEqual(sha(z.read(s['stage'] + '/Package.resolved')), s['dependency_lock_sha256'])
            manifest = json.loads(z.read(s['stage'] + '/source-manifest.json'))
            self.assertEqual([f['sha256'] for f in manifest if f['path'] == driver.TARGET], [r['fixture_sha256']])
            self.assertEqual([f['sha256'] for f in manifest if f['path'] == driver.CORPUS_TARGET], [r['corpus_sha256']])

    def test_before_controls_pass_and_only_expected_context_failures_qualify(self):
        z, r = self.result()
        before = r['stages'][0]
        self.assertEqual(before['totals'], dict(passed=2, skipped=0, failed=7))
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for c in before['cases']:
                p = out / c['log']; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(c['log']))
            driver.validate_baseline(before['cases'], out)
            for index in range(9):
                altered = copy.deepcopy(before['cases'])
                altered[index]['exit_code'] = 99
                with self.assertRaises(ValueError):
                    driver.validate_baseline(altered, out)
            with self.assertRaises(ValueError):
                driver.validate_baseline(before['cases'][:-1], out)
            failed = next(c for c in before['cases'] if c['status'] == 'failed')
            path = out / failed['log']
            path.write_text(path.read_text() + '\ncase.swift:1: error: Test.method : unrelated failure\n')
            with self.assertRaises(ValueError):
                driver.validate_baseline(before['cases'], out)

    def test_after_all_67_methods_pass_without_skips(self):
        z, r = self.result()
        after = r['stages'][1]
        self.assertEqual(after['totals'], dict(passed=67, skipped=0, failed=0))
        self.assertEqual(len({c['selector'] for c in after['cases']}), 67)
        paired = [c for c in after['cases'] if c['selector'].startswith(driver.CASE_PREFIX)]
        self.assertEqual(len(paired), 9)
        for c in after['cases']:
            self.assertEqual((c['status'], c['exit_code']), ('passed', 0))
            self.assertEqual(sha(z.read(c['log'])), c['log_sha256'])
            self.assertIn('Executed 1 test, with 0 failures', z.read(c['log']).decode())

    def test_source_review_is_partial_and_hash_bound(self):
        z, _ = self.result()
        binding = json.loads((E / 'source-binding.json').read_text())
        self.assertEqual(binding['reviewed_commit'], driver.AFTER)
        self.assertTrue(binding['frozen_inventory_unchanged'])
        files = {f['path']: f['sha256'] for f in json.loads(z.read('after/source-manifest.json'))}
        validation = zipfile.ZipFile(E / 'validation.zip')
        self.addCleanup(validation.close)
        for f in binding['files']:
            self.assertEqual(sha(validation.read('reviewed-source/' + f['path'])), f['sha256'])
            if f['path'].startswith('Packages/'):
                self.assertEqual(files[f['path']], f['sha256'])
            else:
                self.assertRegex(f['sha256'], r'^[0-9a-f]{64}$')
            self.assertEqual(f['status'], 'test-reviewed' if '/Tests/' in f['path'] else 'partially-reviewed')
        m = json.loads((E / 'manifest.json').read_text())
        for f in m['files']:
            self.assertEqual(sha((E / f['path']).read_bytes()), f['sha256'])
        self.assertFalse(m['whole_wallet_complete'])
        self.assertFalse(m['app_store_upload'])
        self.assertEqual(m['diagnostics'], dict(passed=119, skipped=2, failed=0))

    def test_generic_build_and_exploratory_attempts_are_preserved(self):
        z = zipfile.ZipFile(E / 'validation.zip'); self.addCleanup(z.close)
        checks = json.loads(z.read('CHECKSUMS.json'))
        for f in checks:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        self.assertIn('** BUILD SUCCEEDED **', z.read('ios.log').decode())
        self.assertIn('no leaks found', z.read('direct-scan.log').decode())
        self.assertIn('0 failures', z.read('diagnostics.log').decode())
        self.assertIn('Executed 1 test, with 0 failures', z.read('diagnostics-trace.log').decode())
        self.assertIn('exploratory/baseline-tests.log', z.namelist())
        self.assertIn('38 failures', z.read('exploratory/baseline-tests.log').decode())
        self.assertIn('28 failures', z.read('exploratory/baseline-tests-corrected.log').decode())

    def test_fix_build_and_pr_are_bound_separately(self):
        b = json.loads((E / 'build-receipt.json').read_text())
        p = json.loads((E / 'pr.json').read_text())
        self.assertIn(p['state'], ['OPEN', 'MERGED'])
        self.assertEqual(p['headRefOid'], driver.AFTER)
        self.assertEqual(b['commit'], driver.AFTER)
        self.assertEqual(b['exit_code'], 0)
        self.assertEqual(b['status'], '')
        self.assertIn('generic/platform=iOS', b['command'])
        self.assertIn('CODE_SIGNING_ALLOWED=NO', b['command'])

    def test_workflow_scope_and_report_limitations(self):
        w = (ROOT / '.github/workflows/solana-stake-authority-review.yml').read_text()
        self.assertIn(driver.AFTER, w)
        self.assertIn('contents: read', w)
        self.assertNotIn('pull_request', w)
        self.assertNotIn('secrets.', w)
        for a in re.findall(r'uses: ([^\s]+)', w):
            self.assertRegex(a, r'@[0-9a-f]{40}$')
        report = (ROOT / 'review/SOLANA-STAKE-AUTHORITY.md').read_text()
        for phrase in ['not independent', 'does not prove provider honesty', 'No simulator', 'frozen inventory remains']:
            self.assertIn(phrase, report)
