import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence/5.0.3-build105/installation-binding'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('installation_binding_review', ROOT / 'scripts/installation-binding-review.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

def sha(b): return hashlib.sha256(b).hexdigest()

class InstallationBindingEvidence(unittest.TestCase):
    def archive(self, name):
        z = zipfile.ZipFile(E / name); self.addCleanup(z.close)
        files = json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()), {f['path'] for f in files} | {'CHECKSUMS.json'})
        self.assertEqual(len(z.namelist()), len(files) + 1)
        for f in files: self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z

    def result(self):
        z = self.archive('runs.zip'); r = json.loads(z.read('result.json'))
        self.assertEqual(r['source_commit'], driver.COMMIT)
        self.assertEqual(r['driver_sha256'], sha((E / 'driver-initial.py').read_bytes()))
        self.assertEqual(r['fixture_sha256'], sha((ROOT / driver.FIXTURE).read_bytes()))
        self.assertEqual(r['helper_sha256'], sha((ROOT / 'scripts/source_state.py').read_bytes()))
        for f in r['files']: self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        return z, r

    def test_production_complete_real_result(self):
        z, r = self.result()
        self.assertEqual([s['stage'] for s in r['stages']], ['baseline','production','mutation-control'])
        self.assertEqual([s['totals'] for s in r['stages']], [dict(passed=56,failed=0,skipped=0),dict(passed=2647,failed=0,skipped=0),dict(passed=0,failed=12,skipped=0)])
        self.assertEqual(z.read('baseline.log').decode().strip(), 'Passed 56 installation ownership, encryption, reinstall, failure recovery and protected-file host checks.')
        result = json.loads(z.read('production.log'))
        self.assertEqual(len(result['cases']), 2647)
        self.assertEqual(len({c['case'] for c in result['cases']}),2647)
        self.assertTrue(all(c['passed'] for c in result['cases']))
        for prefix, count in [('purpose-',12),('sealed-bit-',2272),('truncated-',284),('wrong-key-',32),('reset-revokes-',4),('other-installation-',4)]:
            self.assertEqual(sum(c['case'].startswith(prefix) for c in result['cases']),count)
        for s in r['stages']:
            self.assertEqual((s['build_exit_code'],s['runtime_network']),(0,'denied'))
            self.assertEqual(sha(z.read(s['stage']+'-source.swift')), s['source_sha256'])
        self.assertEqual([s['exit_code'] for s in r['stages']],[0,0,1])
        self.assertEqual(len({s['executable_sha256'] for s in r['stages']}),3)

    def test_mutation_exact_failure_and_only_intended_change(self):
        z, r = self.result(); result=json.loads(z.read('mutation-control.log'))
        driver.validate_mutant(1,result)
        original=z.read('production-source.swift').decode()
        self.assertEqual(original.count(driver.GUARD),1)
        self.assertEqual(z.read('mutation-control-source.swift').decode(),original.replace(driver.GUARD,driver.MUTANT))
        for code in [0,-5,2]:
            with self.assertRaises(ValueError): driver.validate_mutant(code,result)
        for k,v in [('passed',1),('failed',11),('skipped',1),('cases',[])]:
            wrong=copy.deepcopy(result);wrong[k]=v
            with self.assertRaises(ValueError): driver.validate_mutant(1,wrong)
        wrong=copy.deepcopy(result);wrong['cases'][0]['case']='unrelated'
        with self.assertRaises(ValueError):driver.validate_mutant(1,wrong)

    def test_first_failed_driver_attempt_retained(self):
        z=self.archive('attempt1.zip')
        self.assertIn('Inherited baseline did not complete',z.read('driver.log').decode())
        self.assertIn('Passed 56 installation',z.read('results/baseline.log').decode())
        self.assertIn('Passed 57 installation',z.read('driver.py').decode())
        self.assertNotIn('results/production.log',z.namelist())

    def test_manual_scope_and_file_manifests(self):
        z,r=self.result();s=self.archive('validation.zip')
        b=json.loads((E/'source-binding.json').read_text())
        self.assertEqual(b['reviewed_commit'],driver.COMMIT)
        self.assertTrue(b['frozen_inventory_unchanged'])
        self.assertTrue(b['automated_tests_do_not_promote_manual_review'])
        self.assertEqual(len(b['files']),12)
        for f in b['files']:
            data=s.read('reviewed-source/'+f['path'])
            self.assertEqual(sha(data),f['sha256']);self.assertEqual(f['status'],'partially-reviewed')
            self.assertTrue(f['remaining'])
            for a,end in f['lines']:self.assertTrue(1<=a<=end<=len(data.splitlines()))
        self.assertEqual(s.read('reviewed-source/'+driver.SOURCE),z.read('production-source.swift'))
        m=json.loads((E/'manifest.json').read_text())
        for f in m['files']:self.assertEqual(sha((E/f['path']).read_bytes()),f['sha256'])
        for field in ['new_app_finding','app_modified','whole_wallet_complete','simulator_used','physical_device_used','app_store_upload']:self.assertFalse(m[field])

    def test_workflow_pinned_readonly_scope(self):
        w=(ROOT/'.github/workflows/installation-binding-review.yml').read_text()
        self.assertIn(driver.COMMIT,w);self.assertIn('contents: read',w)
        self.assertNotIn('pull_request',w);self.assertNotIn('secrets.',w)
        self.assertIn('test_installation_binding_review.py',w)
        for action in re.findall(r'uses: ([^\s]+)',w):self.assertRegex(action,r'@[0-9a-f]{40}$')
