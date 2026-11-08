import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/5.0.3-build105/late-authentication'
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('late_authentication_review',ROOT/'scripts/late-authentication-review.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
def sha(b):return hashlib.sha256(b).hexdigest()

class LateAuthenticationReview(unittest.TestCase):
    def test_evidence_and_actual_compiled_sources(self):
        with zipfile.ZipFile(E/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{f['path'] for f in checks}|{'CHECKSUMS.json'})
            for f in checks:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            results=[]
            for stage,mutant in [('production',False),('mutation',True)]:
                r=json.loads(z.read(stage+'/result.json'));results.append(r)
                self.assertEqual(r['source_commit'],driver.COMMIT)
                self.assertEqual(r['deliberate_mutation'],mutant)
                self.assertEqual(r['fixture_sha256'],sha((ROOT/'fixtures/late-authentication/Checks.swift').read_bytes()))
                self.assertEqual(r['script_sha256'],sha((ROOT/'scripts/late-authentication-review.py').read_bytes()))
                raw=z.read(stage+'/checks.log');self.assertEqual(sha(raw),r['log_sha256'])
                expected=driver.validate(r['exit_code'],raw.decode(),mutant)
                self.assertEqual(r['cases'],[dict(name=n,status=s.lower()) for s,n in expected])
                self.assertEqual(len(r['cases']),66)
                self.assertEqual(r['runtime_network'],'denied')
                self.assertEqual(sha(z.read(stage+'/Package.resolved')),r['dependency_lock_sha256'])
                self.assertEqual(sha(z.read(stage+'/executed-harness.py')),r['harness_executed_sha256'])
                for f in json.loads(z.read(stage+'/generated-manifest.json')):
                    self.assertEqual(sha(z.read(stage+'/generated-host/'+f['path'])),f['sha256'])
                self.assertEqual(sha(z.read(stage+'/generated-host/Sources/OathWalletVault.swift')),r['compiled_vault_sha256'])
                self.assertEqual(sha(z.read(stage+'/generated-host/Sources/CheckWalletConnectAuthorization.swift')),r['fixture_sha256'])
            self.assertEqual(results[0]['source_sha256'],results[0]['compiled_vault_sha256'])
            self.assertEqual(results[0]['source_sha256'],results[1]['source_sha256'])
            self.assertNotEqual(results[1]['source_sha256'],results[1]['compiled_vault_sha256'])
            self.assertEqual(json.loads(z.read('production/Package.resolved'))['pins'],json.loads(z.read('mutation/Package.resolved'))['pins'])
            manifests=[{f['path']:f['sha256'] for f in json.loads(z.read(stage+'/generated-manifest.json'))} for stage in ['production','mutation']]
            self.assertEqual(set(manifests[0]),set(manifests[1]))
            self.assertEqual([p for p in manifests[0] if manifests[0][p]!=manifests[1][p]],['Sources/OathWalletVault.swift'])
            self.assertNotEqual(results[0]['executable_sha256'],results[1]['executable_sha256'])

    def test_failure_parser_does_not_accept_crashes_skips_or_missing_checks(self):
        for mutant in [False,True]:
            cases=driver.expected_cases(mutant)
            failures=2 if mutant else 0
            text='\n'.join(s+': '+n for s,n in cases)+f'\nLate authentication checks: {66-failures} passed, {failures} failed\n'
            driver.validate(1 if mutant else 0,text,mutant)
            for code,altered in [(-5,text),(0,''),(0,text.replace('PASS:','SKIP:',1)),(0,text.split('\n',1)[1])]:
                with self.assertRaises(ValueError):driver.validate(code,altered,mutant)

    def test_captured_credential_and_preserved_attempts(self):
        f=(ROOT/'fixtures/late-authentication/Checks.swift').read_text()
        self.assertLess(f.index('guard let captured = credential'),f.index('await withCheckedContinuation'))
        self.assertIn('return captured',f)
        for op in driver.OPERATIONS:self.assertIn('"'+op+'"',f)
        with zipfile.ZipFile(E/'initial-attempts.zip') as z:
            for entry in json.loads(z.read('CHECKSUMS.json')):self.assertEqual(sha(z.read(entry['path'])),entry['sha256'])
            self.assertIn('54 passed, 2 failed',z.read('oath-late-auth-result-prod/checks.log').decode())
            self.assertIn('Mutation boundary changed',z.read('original/oath-late-auth-driver-mutant.log').decode())

    def test_workflow_and_partial_coverage(self):
        w=(ROOT/'.github/workflows/late-authentication-review.yml').read_text()
        self.assertIn(driver.COMMIT,w);self.assertIn('contents: read',w)
        self.assertNotIn('secrets.',w);self.assertNotIn('pull_request',w)
        for a in re.findall(r'uses: ([^\s]+)',w):self.assertRegex(a,r'@[0-9a-f]{40}$')
        b=json.loads((E/'source-binding.json').read_text());self.assertEqual(b['reviewed_commit'],driver.COMMIT)
        self.assertTrue(b['frozen_inventory_unchanged'])
        with zipfile.ZipFile(E/'source.zip') as z:
            for f in b['files']:
                self.assertEqual(sha(z.read(f['path'])),f['sha256'])
                self.assertEqual(f['status'],'partially-reviewed')
                for start,end in f['reviewed_ranges']:self.assertTrue(1<=start<=end<=len(z.read(f['path']).splitlines()))
