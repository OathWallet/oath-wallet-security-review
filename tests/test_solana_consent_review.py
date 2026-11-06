import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence/5.0.3-build105/solana-consent'
BEFORE = '7ffd0f449c3312d9fafd01eda59c6b9eb813f9ca'
AFTER = '247ac898168cc8f97be28398c69337f569fb5f96'
FIX = '7c79fe5bf89de44168fc9bc25e7e781d9051fdfe'
CASE = 'OathAnkrTests.WalletConnectSolanaConsentRegressionTests/testPermissionChangeWithIdenticalBalancesMustChangeReview'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class SolanaConsentEvidence(unittest.TestCase):
    def archive(self, name='runs.zip'):
        z = zipfile.ZipFile(E / name)
        self.addCleanup(z.close)
        rows = json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()), {f['path'] for f in rows} | {'CHECKSUMS.json'})
        self.assertEqual(len(z.namelist()), len(rows) + 1)
        for f in rows:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z

    def result(self):
        z = self.archive()
        r = json.loads(z.read('result.json'))
        self.assertEqual((r['baseline_commit'], r['fix_commit'], r['retest_commit']), (BEFORE, FIX, AFTER))
        self.assertEqual(r['driver_sha256'], sha((ROOT / 'scripts/solana-consent-review.py').read_bytes()))
        self.assertEqual(r['fixture_sha256'], sha((ROOT / r['fixture']).read_bytes()))
        for name, digest in r['helper_sha256'].items():
            self.assertEqual(digest, sha((ROOT / 'scripts' / name).read_bytes()))
        for f in r['files']:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z, r

    def test_identical_fixture_and_independent_executables(self):
        z, r = self.result()
        self.assertEqual([s['stage'] for s in r['stages']], ['before', 'after'])
        self.assertEqual(len({s['executable_sha256'] for s in r['stages']}), 2)
        target = 'Packages/OathAnkr/Tests/OathAnkrTests/WalletConnectSolanaConsentRegressionTests.swift'
        for s in r['stages']:
            self.assertEqual(s['build_exit_code'], 0)
            self.assertEqual(s['runtime_network'], 'denied')
            self.assertEqual(s['fixture_sha256'], r['fixture_sha256'])
            self.assertEqual(sha(z.read(s['stage'] + '/Package.resolved')), s['dependency_lock_sha256'])
            manifest = json.loads(z.read(s['stage'] + '/source-manifest.json'))
            self.assertEqual([f['sha256'] for f in manifest if f['path'] == target], [r['fixture_sha256']])

    def test_before_has_only_the_expected_assertion_failure(self):
        z, r = self.result()
        s = r['stages'][0]
        self.assertEqual(s['totals'], dict(passed=0, skipped=0, failed=1))
        self.assertEqual(len(s['cases']), 1)
        c = s['cases'][0]
        self.assertEqual((c['selector'], c['status'], c['exit_code']), (CASE, 'failed', 1))
        log = z.read(c['log']).decode()
        failures = re.findall(r'^.* error: .* : (.*)$', log, re.M)
        self.assertEqual(len(failures), 1)
        self.assertIn('A different token delegate must not be represented by an identical review', failures[0])

    def test_after_all_methods_pass_with_no_skips(self):
        z, r = self.result()
        s = r['stages'][1]
        self.assertEqual(s['totals'], dict(passed=36, skipped=0, failed=0))
        self.assertEqual(len({c['selector'] for c in s['cases']}), 36)
        self.assertIn(CASE, [c['selector'] for c in s['cases']])
        for c in s['cases']:
            self.assertEqual((c['status'], c['exit_code']), ('passed', 0))
            self.assertEqual(sha(z.read(c['log'])), c['log_sha256'])
            self.assertIn('Executed 1 test, with 0 failures', z.read(c['log']).decode())

    def test_source_binding_remains_partial_and_manifest_matches(self):
        z, _ = self.result()
        b = json.loads((E / 'source-binding.json').read_text())
        self.assertEqual(b['reviewed_commit'], AFTER)
        self.assertTrue(b['frozen_inventory_unchanged'])
        self.assertEqual(len(b['files']), 5)
        source = {f['path']: f['sha256'] for f in json.loads(z.read('after/source-manifest.json'))}
        for f in b['files']:
            self.assertEqual(f['status'], 'partially-reviewed')
            self.assertRegex(f['sha256'], r'^[0-9a-f]{64}$')
            if f['path'] in source:
                self.assertEqual(f['sha256'], source[f['path']])
        m = json.loads((E / 'manifest.json').read_text())
        for f in m['files']:
            self.assertEqual(sha((E / f['path']).read_bytes()), f['sha256'])
        for key in ['application_changed_by_checkpoint', 'new_ios_build_performed', 'whole_wallet_complete']:
            self.assertFalse(m[key])

    def test_original_discovery_failure_is_retained_and_excluded(self):
        z = self.archive('attempt1.zip')
        self.assertNotIn('result.json', z.namelist())
        self.assertFalse(any('/cases/' in p for p in z.namelist()))
        self.assertIn('ValueError: Unexpected discovery output', z.read('driver.log').decode())
        self.assertIn('Build complete!', z.read('before/build.log').decode())

    def test_workflow_pins_and_scope_disclosures(self):
        w = (ROOT / '.github/workflows/solana-consent-review.yml').read_text()
        self.assertIn(AFTER, w)
        self.assertIn('contents: read', w)
        self.assertNotIn('pull_request', w)
        self.assertNotIn('secrets.', w)
        for action in re.findall(r'uses: ([^\s]+)', w):
            self.assertRegex(action, r'@[0-9a-f]{40}$')
        report = (ROOT / 'review/SOLANA-CONSENT.md').read_text()
        for phrase in ['whole-wallet audit', 'remains incomplete', 'not independent certification',
                       'No test executed', 'No new generic iOS build', 'already', 'Ibnu']:
            self.assertIn(phrase, report)
        driver = (ROOT / 'scripts/solana-consent-review.py').read_text()
        for phrase in ['require_source_state(source, AFTER)', '(deny network*)', 'Fresh scratch and output',
                       '--force-resolved-versions', "stderr=", 'ASSERTION not in failures[0]']:
            self.assertIn(phrase, driver)
