import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence/5.0.2-build104/backup-settings'
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
def sha(b):return hashlib.sha256(b).hexdigest()
class BackupSettingsEvidence(unittest.TestCase):
    def archive(self):
        z=zipfile.ZipFile(EVIDENCE/'runs.zip');self.addCleanup(z.close)
        checks=json.loads(z.read('CHECKSUMS.json'))
        self.assertEqual(set(z.namelist()),{f['path'] for f in checks}|{'CHECKSUMS.json'})
        for f in checks:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
        r=json.loads(z.read('result.json'));self.assertEqual(r['source_commit'],PIN)
        self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/backup-settings-review.py').read_bytes()))
        for f in r['files']:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
        for stage in r['stages']:
            for f in stage['files']:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            self.assertEqual(stage['fixture_sha256'],sha((ROOT/'fixtures/backup-settings/Checks.swift').read_bytes()))
        return z,r
    def test_baseline_and_negative_control(self):
        z,r=self.archive();b,m=r['stages']
        self.assertEqual((b['stage'],b['passed'],b['failed'],b['exit_code']),('baseline',52,0,0))
        self.assertEqual((m['stage'],m['passed'],m['failed'],m['exit_code']),('mutation',40,12,1))
        self.assertNotEqual(b['executable_sha256'],m['executable_sha256'])
        self.assertEqual(b['production_sha256'],m['production_sha256']);self.assertEqual(b['extracted_body_sha256'],m['extracted_body_sha256'])
        self.assertEqual([c['name'] for c in b['cases']],[c['name'] for c in m['cases']])
        self.assertEqual(len(set(c['name'] for c in b['cases'])),52)
        for stage in [b,m]:
            raw=z.read(stage['stage']+'/run.log').decode()
            self.assertEqual([(s.lower(),n) for s,n in re.findall(r'^(PASS|FAIL): (.+)$',raw,re.M)],[(c['status'],c['name']) for c in stage['cases']])
            for c in stage['cases']:
                expected=stage['stage']=='mutation' and c['name'].endswith(('preserves newer progress','preserves newer task'))
                self.assertEqual(c['status'],'fail' if expected else 'pass')
        baseline=z.read('baseline/Model.swift').decode();mutant=z.read('mutation/Model.swift').decode()
        self.assertEqual(mutant,baseline.replace('guard operationID == operation else { return }','// Deliberate test mutation: remove finish ownership guard.'))
    def test_existing_all_wallet_fixture_is_current(self):
        z,r=self.archive();a=r['all_wallet_model']
        self.assertEqual((a['passed'],a['failed'],a['exit_code']),(15,0,0))
        raw=z.read(a['log']);self.assertEqual(sha(raw),a['log_sha256'])
        self.assertEqual(len(re.findall(rb'^PASS: ',raw,re.M)),15)
        self.assertIn(b'Backup presentation checks: 15 passed, 0 failed',raw)
        findings=json.loads((ROOT/'findings/index.json').read_text());f=next(x for x in findings if x['id']=='OW-2026-059')
        self.assertEqual(f['current_target']['retest']['commit'],PIN)
        self.assertFalse(f['available_in_app_store_verified'])
    def test_read_scope_is_partial_and_hash_bound(self):
        b=json.loads((EVIDENCE/'source-binding.json').read_text());self.assertEqual(b['reviewed_commit'],PIN)
        self.assertEqual(len(b['files']),3)
        inv={f['path']:f for f in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        for f in b['files']:
            self.assertEqual(f['status'],'partially-reviewed');self.assertTrue(f['baseline_identical'])
            self.assertEqual(f['sha256'],inv[f['path']]['sha256'])
            self.assertEqual(inv[f['path']]['status'],'partially-reviewed')
            self.assertIn('review/BACKUP-SETTINGS-LIFECYCLE.md',inv[f['path']]['evidence'])
    def test_no_app_change_or_complete_verdict(self):
        m=json.loads((EVIDENCE/'manifest.json').read_text());self.assertEqual(m['source_commit'],PIN)
        for f in m['files']:self.assertEqual(sha((EVIDENCE/f['path']).read_bytes()),f['sha256'])
        for key in ['application_changed','whole_wallet_complete','new_ios_build_performed']:self.assertFalse(m[key])
        report=(ROOT/'review/BACKUP-SETTINGS-LIFECYCLE.md').read_text()
        for phrase in ['whole-wallet audit remains incomplete','No new confirmed application defect','not independent certification','No new generic iOS build']:
            self.assertIn(phrase,report)
    def test_driver_and_workflow_boundaries(self):
        s=(ROOT/'scripts/backup-settings-review.py').read_text()
        for p in ['Fresh scratch/output required','require_source_state(source,PIN)','(deny network*)','await']:
            self.assertIn(p,s if p!='await' else (ROOT/'fixtures/backup-settings/Checks.swift').read_text())
        w=(ROOT/'.github/workflows/backup-settings-review.yml').read_text()
        self.assertIn('contents: read',w);self.assertIn(PIN,w);self.assertNotIn('pull_request',w);self.assertNotIn('secrets.',w)
        self.assertIn('test_backup_settings_review.py',w)
    def test_hosted_backup_replay(self):
        p=ROOT/'evidence/5.0.2-build104/hosted-cloud-file-recheck'
        run=json.loads((p/'run.json').read_text());a=json.loads((p/'artifact.json').read_text())
        self.assertEqual((run['id'],run['head_sha'],run['conclusion']),(41753493347,'02f491149832c6ce8b62e25eb18dd7eef92f7f18','success'))
        self.assertEqual(a['digest'],'sha256:'+sha((p/'artifact.zip').read_bytes()))
        with zipfile.ZipFile(p/'artifact.zip') as z:
            top=json.loads(z.read('result.json'));self.assertEqual(top['source_commit'],PIN)
            exes=[]
            for row in top['reports']:
                raw=z.read(row['report']);self.assertEqual(sha(raw),row['sha256']);s=json.loads(raw);stage=s['stage']
                exes.append(s['test_executable_sha256']);self.assertTrue(s['tracked_source_restored'])
                for f in s['files']:self.assertEqual(sha(z.read(stage+'/'+f['path'])),f['sha256'])
                self.assertEqual(len(s['methods']),64 if stage=='current-package' else 3)
                for m in s['methods']:
                    self.assertEqual((m['status'],m['exit_code'],m['assertion_errors']),('failed',1,2) if stage=='before' else ('passed',0,0))
                    self.assertEqual(sha(z.read(stage+'/'+m['log'])),m['log_sha256'])
                if stage=='current-package':
                    self.assertFalse(s['instrumented']);self.assertEqual(s['original_writer_sha256'],s['compiled_writer_sha256'])
                    self.assertEqual((s['swift_testing']['tests'],s['swift_testing']['status']),(1,'passed'))
            self.assertEqual(len(set(exes)),3)
