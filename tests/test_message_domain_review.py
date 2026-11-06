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
E = ROOT / 'evidence/5.0.3-build105/message-domains'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('message_domain_review', ROOT / 'scripts/message-domain-review.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

def sha(b):
    return hashlib.sha256(b).hexdigest()

class MessageDomainEvidence(unittest.TestCase):
    def bundle(self):
        z = zipfile.ZipFile(E / 'runs.zip'); self.addCleanup(z.close)
        checks = json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()), {f['path'] for f in checks} | {'CHECKSUMS.json'})
        self.assertEqual(len(z.namelist()), len(checks) + 1)
        for f in checks:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        r = json.loads(z.read('result.json'))
        self.assertEqual(r['source_commit'], driver.COMMIT)
        self.assertEqual(r['fixture_sha256'], sha((ROOT / r['fixture']).read_bytes()))
        self.assertEqual(r['driver_sha256'], sha((ROOT / 'scripts/message-domain-review.py').read_bytes()))
        for n, digest in r['helper_sha256'].items():
            self.assertEqual(digest, sha((ROOT / 'scripts' / n).read_bytes()))
        for f in r['files']:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z, r

    def test_all_production_methods_pass_offline(self):
        z, r = self.bundle()
        self.assertEqual(r['stages'][0]['totals'], dict(passed=27, skipped=0, failed=0))
        cases = r['stages'][0]['cases']
        self.assertEqual(len({c['selector'] for c in cases}), 27)
        for family, count in [('MessageDomainReviewTests', 7), ('WalletConnectSolanaTests', 15), ('WalletConnectTonTests', 5)]:
            self.assertEqual(sum(c['selector'].startswith('OathAnkrTests.' + family + '/') for c in cases), count)
        for c in cases:
            self.assertEqual((c['status'], c['exit_code']), ('passed', 0))
            self.assertEqual(sha(z.read(c['log'])), c['log_sha256'])
            self.assertIn('Executed 1 test, with 0 failures', z.read(c['log']).decode())
        for stage in r['stages']:
            self.assertEqual((stage['build_exit_code'], stage['runtime_network']), (0, 'denied'))
            self.assertEqual(sha(z.read(stage['stage'] + '/Package.resolved')), stage['dependency_lock_sha256'])

    def test_mutant_changes_only_domain_binding_and_fails_exactly(self):
        z, r = self.bundle()
        manifests = [{f['path']: f['sha256'] for f in json.loads(z.read(s['stage'] + '/source-manifest.json'))} for s in r['stages']]
        self.assertEqual(set(manifests[0]), set(manifests[1]))
        self.assertEqual([p for p in manifests[0] if manifests[0][p] != manifests[1][p]], [driver.CRYPTO])
        self.assertEqual(r['stages'][1]['totals'], dict(passed=0, skipped=0, failed=1))
        self.assertEqual(len({s['executable_sha256'] for s in r['stages']}), 2)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            cases = r['stages'][1]['cases']
            for c in cases:
                p = out / c['log']; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(c['log']))
            driver.validate_mutant(cases, out)
            for change in [{'status': 'passed'}, {'exit_code': -5}, {'selector': 'other'}]:
                altered = copy.deepcopy(cases); altered[0].update(change)
                with self.assertRaises(ValueError): driver.validate_mutant(altered, out)

    def test_source_scope_and_archives_are_hash_bound(self):
        z, r = self.bundle()
        m = json.loads((E / 'manifest.json').read_text())
        self.assertEqual(m['source_commit'], driver.COMMIT)
        for key in ['new_app_finding', 'application_changed', 'whole_wallet_complete', 'simulator_used', 'physical_device_used', 'app_store_upload']:
            self.assertFalse(m[key])
        for f in m['files']:
            self.assertEqual(sha((E / f['path']).read_bytes()), f['sha256'])
        b = json.loads((E / 'source-binding.json').read_text())
        self.assertEqual(b['reviewed_commit'], driver.COMMIT)
        self.assertTrue(b['frozen_inventory_unchanged'])
        with zipfile.ZipFile(E / 'validation.zip') as v:
            for f in json.loads(v.read('CHECKSUMS.json')):
                self.assertEqual(sha(v.read(f['path'])), f['sha256'])
            for f in b['files']:
                name = 'inherited-vectors/' + Path(f['path']).name if f['status'] == 'test-fixture' else 'reviewed-source/' + f['path']
                self.assertEqual(sha(v.read(name)), f['sha256'])
                if f['status'] != 'test-fixture':
                    self.assertEqual(f['status'], 'partially-reviewed')
                    lines = len(v.read(name).splitlines())
                    for start, end in f['reviewed_ranges']:
                        self.assertTrue(1 <= start <= end <= lines)

    def test_fixture_has_controls_and_bounded_negative_corpus(self):
        text = (ROOT / driver.FIXTURE).read_text()
        self.assertEqual(len(re.findall(r'func test\w+\(', text)), 7)
        for marker in ['UInt8.min...UInt8.max', 'XCTAssertEqual(accepted, 95)', 'XCTAssertEqual(rejected, 161)', 'Domain binding removed', 'isValidSignature', '4097', '4096']:
            self.assertIn(marker, text)
        self.assertNotIn('URLSession', text)
        report = (ROOT / 'review/MESSAGE-DOMAINS.md').read_text()
        for marker in ['not independent', 'partial', 'No simulator', 'not a discovered vulnerability', 'network-denied']:
            self.assertIn(marker, report)

    def test_workflow_is_pinned_and_unprivileged(self):
        w = (ROOT / '.github/workflows/message-domain-review.yml').read_text()
        self.assertIn(driver.COMMIT, w)
        self.assertIn('test_message_domain_review.py', w)
        self.assertIn('contents: read', w)
        self.assertNotIn('secrets.', w)
        self.assertNotIn('pull_request', w)
        for a in re.findall(r'uses: ([^\s]+)', w):
            self.assertRegex(a, r'@[0-9a-f]{40}$')
