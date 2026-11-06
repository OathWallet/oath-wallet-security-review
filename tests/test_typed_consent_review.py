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
E = ROOT / 'evidence/5.0.3-build105/typed-consent'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('typed_consent_review', ROOT / 'scripts/typed-consent-review.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class TypedConsentEvidence(unittest.TestCase):
    def archive(self, name):
        z = zipfile.ZipFile(E / name)
        self.addCleanup(z.close)
        checks = json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(len(z.namelist()), len(checks) + 1)
        self.assertEqual(set(z.namelist()), {f['path'] for f in checks} | {'CHECKSUMS.json'})
        for f in checks:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z

    def result(self):
        z = self.archive('runs.zip')
        r = json.loads(z.read('result.json'))
        self.assertEqual(r['source_commit'], driver.COMMIT)
        self.assertEqual(r['driver_sha256'], sha((ROOT / 'scripts/typed-consent-review.py').read_bytes()))
        self.assertEqual(r['fixture_sha256'], sha((ROOT / r['fixture']).read_bytes()))
        for name, digest in r['helper_sha256'].items():
            self.assertEqual(digest, sha((ROOT / 'scripts' / name).read_bytes()))
        for f in r['files']:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z, r

    def test_complete_production_selection_and_real_process_results(self):
        z, r = self.result()
        p = r['stages'][0]
        self.assertEqual(p['stage'], 'production')
        self.assertEqual(p['totals'], dict(passed=20, skipped=0, failed=0))
        self.assertEqual(len({c['selector'] for c in p['cases']}), 20)
        for family, count in [('TypedConsentReviewTests', 7), ('WalletConnectTypedDataTests', 8), ('WalletConnectSignInTests', 3), ('WalletConnectJSONCollectionLimitTests', 2)]:
            self.assertEqual(sum(c['selector'].startswith('OathAnkrTests.' + family + '/') for c in p['cases']), count)
        for c in p['cases']:
            self.assertEqual((c['status'], c['exit_code']), ('passed', 0))
            self.assertEqual(sha(z.read(c['log'])), c['log_sha256'])
            self.assertEqual(driver.classify(z.read(c['log']).decode(), c['exit_code']), 'passed')
            self.assertIn('Executed 1 test, with 0 failures', z.read(c['log']).decode())

    def test_separate_clean_builds_and_only_the_deliberate_guard_change(self):
        z, r = self.result()
        self.assertEqual([s['stage'] for s in r['stages']], ['production', 'mutation-control'])
        self.assertEqual(len({s['executable_sha256'] for s in r['stages']}), 2)
        self.assertEqual(len({s['source_archive_sha256'] for s in r['stages']}), 1)
        manifests = []
        for s in r['stages']:
            self.assertEqual(s['build_exit_code'], 0)
            self.assertEqual(s['runtime_network'], 'denied')
            self.assertEqual(sha(z.read(s['stage'] + '/Package.resolved')), s['dependency_lock_sha256'])
            m = {f['path']: f['sha256'] for f in json.loads(z.read(s['stage'] + '/source-manifest.json'))}
            self.assertEqual(m[driver.TARGET], r['fixture_sha256'])
            self.assertEqual(m[driver.VECTOR_TARGET], r['reference']['vectors_sha256'])
            manifests.append(m)
        self.assertEqual(set(manifests[0]), set(manifests[1]))
        self.assertEqual([p for p in manifests[0] if manifests[0][p] != manifests[1][p]], [driver.CRYPTO])
        source = self.archive('validation.zip').read('reviewed-source/' + driver.CRYPTO).decode()
        self.assertEqual(source.count(driver.GUARD), 1)
        self.assertEqual(sha(source.replace(driver.GUARD, driver.MUTATION).encode()), manifests[1][driver.CRYPTO])

    def test_mutant_requires_expected_assertions_not_crash_skip_or_other_failure(self):
        z, r = self.result()
        stage = r['stages'][1]
        self.assertEqual(stage['totals'], dict(passed=0, skipped=0, failed=1))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            c = stage['cases'][0]
            path = out / c['log']; path.parent.mkdir(parents=True); path.write_bytes(z.read(c['log']))
            self.assertEqual(sha(path.read_bytes()), c['log_sha256'])
            driver.validate_mutant(stage['cases'], out)
            for key, bad in [('exit_code', -5), ('exit_code', 0), ('status', 'passed'), ('status', 'skipped'), ('selector', 'Other/test')]:
                cases = copy.deepcopy(stage['cases']); cases[0][key] = bad
                with self.assertRaises(ValueError): driver.validate_mutant(cases, out)
            with self.assertRaises(ValueError): driver.validate_mutant([], out)
            original = path.read_text()
            for body in [original.replace('Executed 1 test', 'missing summary'), original + '\nx.swift:1: error: Test.method : unrelated assertion\n', 'crashed']:
                path.write_text(body)
                with self.assertRaises(ValueError): driver.validate_mutant(stage['cases'], out)

    def test_reference_corpus_is_bound_to_generator_and_locked_ethers(self):
        z, r = self.result()
        ref = r['reference']
        self.assertEqual(ref['version'], 'ethers@6.15.0')
        directory = ROOT / 'fixtures/typed-consent'
        for name, key in [('package-lock.json','lock_sha256'), ('vectors.json','vectors_sha256'), ('generate.cjs','generator_sha256')]:
            self.assertEqual(sha((directory / name).read_bytes()), ref[key])
        self.assertEqual(z.read('reference-vectors.json'), (directory / 'vectors.json').read_bytes())
        self.assertEqual(z.read('reference-lock.json'), (directory / 'package-lock.json').read_bytes())
        lock = json.loads(z.read('reference-lock.json'))
        self.assertEqual(lock['packages']['node_modules/ethers']['version'], '6.15.0')
        for name, package in lock['packages'].items():
            if name:
                self.assertTrue(package['integrity'].startswith('sha512-'))
                self.assertTrue(package['resolved'].startswith('https://registry.npmjs.org/'))
        corpus = json.loads(z.read('reference-vectors.json'))
        self.assertEqual(len(corpus['vectors']), 616)
        self.assertEqual(len(corpus['invalid']), 192)
        self.assertEqual(len({v['name'] for v in corpus['vectors']}), 616)
        self.assertEqual(len({v['name'] for v in corpus['invalid']}), 192)
        for v in corpus['vectors']:
            for key in ['digest', 'domainHash', 'messageHash']:
                self.assertRegex(v[key], r'^0x[0-9a-f]{64}$')
            self.assertRegex(v['signature'], r'^0x[0-9a-f]{130}$')
        self.assertIn('TypedDataEncoder.hash(d,types,message)', (directory / 'generate.cjs').read_text())
        self.assertIn('wallet.signTypedData(d,types,message)', (directory / 'generate.cjs').read_text())
        self.assertIn('"vectors":616,"invalid":192', z.read('reference-generation.log').decode())

    def test_manual_coverage_is_scoped_and_hash_bound(self):
        z, r = self.result()
        source = self.archive('validation.zip')
        binding = json.loads((E / 'source-binding.json').read_text())
        self.assertEqual(binding['reviewed_commit'], driver.COMMIT)
        self.assertTrue(binding['frozen_inventory_unchanged'])
        self.assertEqual(len(binding['files']), 9)
        production = {f['path']: f['sha256'] for f in json.loads(z.read('production/source-manifest.json'))}
        for f in binding['files']:
            data = source.read('reviewed-source/' + f['path'])
            self.assertEqual(sha(data), f['sha256'])
            self.assertEqual(f['status'], 'partially-reviewed')
            self.assertTrue(f['remaining'])
            for first, last in f['lines']: self.assertTrue(1 <= first <= last <= len(data.splitlines()))
            if f['path'].startswith('Packages/'): self.assertEqual(production[f['path']], f['sha256'])
        m = json.loads((E / 'manifest.json').read_text())
        for f in m['files']: self.assertEqual(sha((E / f['path']).read_bytes()), f['sha256'])
        for field in ['new_app_finding', 'app_modified', 'whole_wallet_complete', 'app_store_upload', 'physical_device_used', 'simulator_used']:
            self.assertFalse(m[field])

    def test_workflow_has_pinned_readonly_scope(self):
        w = (ROOT / '.github/workflows/typed-consent-review.yml').read_text()
        self.assertIn(driver.COMMIT, w)
        self.assertIn('contents: read', w)
        self.assertNotIn('pull_request', w)
        self.assertNotIn('secrets.', w)
        for action in re.findall(r'uses: ([^\s]+)', w): self.assertRegex(action, r'@[0-9a-f]{40}$')
