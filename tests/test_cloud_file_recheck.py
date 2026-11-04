import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence/5.0.2-build104/cloud-file-recheck'
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
BASE='c7acd23bb139864a40273f405d18b479589d2b20'
def sha(b):return hashlib.sha256(b).hexdigest()

class CloudFileRecheckEvidence(unittest.TestCase):
    def archive(self):
        z=zipfile.ZipFile(EVIDENCE/'runs.zip');self.addCleanup(z.close)
        checks=json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()),{f['path'] for f in checks}|{'CHECKSUMS.json'})
        for f in checks:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
        top=json.loads(z.read('result.json'))
        self.assertEqual((top['source_commit'],top['historical_commit']),(PIN,BASE))
        self.assertEqual(top['driver_sha256'],sha((ROOT/'scripts/cloud-file-recheck.py').read_bytes()))
        self.assertEqual(top['boundary_fixture_sha256'],sha((ROOT/'fixtures/backup-file-identity/BackupFileBoundaryTests.swift').read_bytes()))
        for f in top['files']:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
        stages={}
        for row in top['reports']:
            raw=z.read(row['report']);self.assertEqual(sha(raw),row['sha256']);r=json.loads(raw)
            for f in r['files']:self.assertEqual(sha(z.read(row['stage']+'/'+f['path'])),f['sha256'])
            self.assertTrue(r['tracked_source_restored']);self.assertIn('denied',r['runtime_network'])
            stages[row['stage']]=r
        return z,stages
    def test_same_regressions_fail_before_and_pass_after(self):
        z,s=self.archive();before,after=s['before'],s['after']
        self.assertEqual(before['source_commit'],BASE);self.assertEqual(after['source_commit'],PIN)
        self.assertEqual(before['fixtures'],after['fixtures'])
        self.assertEqual([m['selector'] for m in before['methods']],[m['selector'] for m in after['methods']])
        self.assertEqual(len(before['methods']),3)
        for stage in ['before','after']:
            r=s[stage];self.assertTrue(r['instrumented'])
            self.assertNotEqual(r['original_writer_sha256'],r['compiled_writer_sha256'])
            self.assertIn(b'audit-interleaving.oathbackup',z.read(stage+'/instrumentation.patch'))
            for m in r['methods']:
                failed=stage=='before'
                self.assertEqual((m['status'],m['exit_code'],m['assertion_errors']),('failed',1,2) if failed else ('passed',0,0))
                raw=z.read(stage+'/'+m['log']);self.assertEqual(sha(raw),m['log_sha256'])
                self.assertIn(b'Executed 1 test, with 2 failures' if failed else b'Executed 1 test, with 0 failures',raw)
    def test_pristine_package_runs_both_test_frameworks(self):
        z,s=self.archive();r=s['current-package']
        self.assertFalse(r['instrumented']);self.assertEqual(r['fixtures'],{})
        self.assertEqual(r['original_writer_sha256'],r['compiled_writer_sha256'])
        self.assertEqual(r['source_commit'],PIN)
        self.assertEqual(len(r['methods']),64);self.assertEqual(len({m['selector'] for m in r['methods']}),64)
        for m in r['methods']:
            self.assertEqual((m['status'],m['exit_code'],m['assertion_errors']),('passed',0,0))
            raw=z.read('current-package/'+m['log']);self.assertEqual(sha(raw),m['log_sha256'])
            self.assertIn(b'Executed 1 test, with 0 failures',raw)
        t=r['swift_testing'];self.assertEqual((t['tests'],t['status']),(1,'passed'))
        raw=z.read('current-package/'+t['log']);self.assertEqual(sha(raw),t['log_sha256'])
        self.assertIn(b'Test run with 1 test in 0 suites passed',raw)
        self.assertIn(b'resetRejectsPreviouslyIssuedLocationBeforeCloudOrFileAccess',raw)
    def test_executables_are_distinct(self):
        _,s=self.archive();self.assertEqual(len({r['test_executable_sha256'] for r in s.values()}),3)
    def test_scoped_source_dispositions(self):
        b=json.loads((EVIDENCE/'source-binding.json').read_text())
        inv={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(b['reviewed_commit'],PIN);self.assertEqual(len(b['files']),3)
        for f in b['files']:
            self.assertTrue(f['baseline_identical']);self.assertEqual(f['sha256'],inv[f['path']]['sha256'])
            self.assertEqual(f['status'],'reviewed' if f['path'].endswith('/Package.swift') else 'partially-reviewed')
            self.assertEqual(f['status'],inv[f['path']]['status'])
            self.assertIn('review/CLOUD-FILE-RECHECK.md',inv[f['path']]['evidence'])
    def test_history_and_current_retest_are_separate(self):
        findings=json.loads((ROOT/'findings/index.json').read_text())
        for id in ['OW-2026-051','OW-2026-052']:
            f=next(f for f in findings if f['id']==id)
            self.assertEqual(f['status'],'fixed-after-reviewed-commit');self.assertEqual(f['affected_commit'],BASE)
            self.assertEqual(f['current_target']['retest']['commit'],PIN)
            self.assertEqual(f['current_target']['retest']['status'],'passed')
            self.assertFalse(f['available_in_app_store_verified'])
    def test_manifest_and_execution_boundaries(self):
        m=json.loads((EVIDENCE/'manifest.json').read_text())
        for f in m['files']:self.assertEqual(sha((EVIDENCE/f['path']).read_bytes()),f['sha256'])
        for k in ['application_changed','whole_wallet_complete','new_ios_build_performed']:self.assertFalse(m[k])
        driver=(ROOT/'scripts/cloud-file-recheck.py').read_text()
        for phrase in ['Fresh scratch/output required','(deny network*)','require_source_state(copy,pin)','require_source_state(source,PIN)']:
            self.assertIn(phrase,driver)
        w=(ROOT/'.github/workflows/cloud-file-recheck.yml').read_text()
        self.assertIn('contents: read',w);self.assertIn(PIN,w);self.assertNotIn('pull_request',w);self.assertNotIn('secrets.',w)
        report=(ROOT/'review/CLOUD-FILE-RECHECK.md').read_text()
        for phrase in ['whole-wallet audit remains incomplete','No new confirmed defect','not independent certification','No new generic']:
            self.assertIn(phrase,report)
    def test_previous_hosted_provider_replay(self):
        p=ROOT/'evidence/5.0.2-build104/hosted-stellar-provider'
        run=json.loads((p/'run.json').read_text());a=json.loads((p/'artifact.json').read_text())
        self.assertEqual((run['id'],run['head_sha'],run['conclusion']),(41752223483,'742c27d43ef42f626210756e1ca633aa2448a117','success'))
        self.assertEqual(a['digest'],'sha256:'+sha((p/'artifact.zip').read_bytes()))
        with zipfile.ZipFile(p/'artifact.zip') as z:
            b=json.loads(z.read('baseline/result.json'));m=json.loads(z.read('mutation/result.json'))
            for folder,r in [('baseline',b),('mutation',m)]:
                self.assertEqual(r['source_commit'],PIN)
                for f in r['files']:self.assertEqual(sha(z.read(folder+'/'+f['path'])),f['sha256'])
            self.assertEqual(len(b['methods']),12)
            for t in b['methods']:
                self.assertEqual((t['status'],t['exit_code']),('passed',0))
                self.assertEqual(sha(z.read('baseline/'+t['log'])),t['log_sha256'])
            self.assertEqual((m['status'],m['exit_code'],m['observed_authorization_assertion_failures']),('failed',1,1))
            self.assertTrue(m['tracked_source_restored'])
            self.assertNotEqual(b['test_executable_sha256'],m['test_executable_sha256'])
