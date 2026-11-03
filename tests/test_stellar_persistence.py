import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
def sha(raw): return hashlib.sha256(raw).hexdigest()

class StellarPersistenceEvidence(unittest.TestCase):
    def test_selected_methods_really_executed_and_hashes_match(self):
        root=ROOT/'evidence/5.0.2-build104/stellar-persistence'
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
            for r in checks:self.assertEqual(sha(z.read(r['path'])),r['sha256'])
            r=json.loads(z.read('result.json'))
            self.assertEqual(r['source_commit'],PIN)
            self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/stellar-persistence-regressions.py').read_bytes()))
            self.assertEqual(len(r['methods']),31);self.assertEqual(len({t['method'] for t in r['methods']}),31)
            self.assertEqual(len(r['excluded_live_methods']),1)
            self.assertEqual(r['excluded_live_methods'],['StellarLedgerTests/testLiveProductionSyncAndOfflineCache'])
            for f in r['files']:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            for t in r['methods']:
                self.assertEqual(t['status'],'passed');self.assertEqual(t['exit_code'],0)
                raw=z.read(t['log']);self.assertEqual(sha(raw),t['log_sha256'])
                self.assertIn(b'Executed 1 test',raw)
            self.assertEqual(len(r['test_executable_sha256']),64)

    def test_partial_source_reads_and_manifest_match(self):
        root=ROOT/'evidence/5.0.2-build104/stellar-persistence'
        m=json.loads((root/'manifest.json').read_text())
        self.assertEqual(m['source_commit'],PIN);self.assertEqual(m['passed'],31)
        self.assertFalse(m['application_changed']);self.assertFalse(m['new_ios_build_performed'])
        for f in m['files']:self.assertEqual(sha((root/f['path']).read_bytes()),f['sha256'])
        rows=json.loads((root/'source-binding.json').read_text())['files']
        inv={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(len(rows),7)
        for r in rows:
            self.assertEqual(r['status'],'partially-reviewed');self.assertTrue(r['baseline_identical'])
            self.assertEqual(r['sha256'],inv[r['path']]['sha256'])
            self.assertEqual(inv[r['path']]['status'],'partially-reviewed')
            self.assertIn('review/STELLAR-PERSISTENCE.md',inv[r['path']]['evidence'])

    def test_fresh_build_and_workflow_boundaries(self):
        text=(ROOT/'scripts/stellar-persistence-regressions.py').read_text()
        self.assertIn("if scratch.exists() or out.exists(): raise ValueError",text)
        self.assertIn("scratch/'build'",text);self.assertIn("'--build-tests'",text)
        self.assertIn('(deny network*)',text);self.assertIn('require_source_state(original, COMMIT)',text)
        self.assertNotIn('os.environ.copy()',text)
        workflow=(ROOT/'.github/workflows/stellar-persistence.yml').read_text()
        self.assertIn(PIN,workflow);self.assertIn('contents: read',workflow)
        self.assertNotIn('pull_request',workflow);self.assertNotIn('secrets.',workflow)
        self.assertIn("python-version: '3.14.7'",workflow)

    def test_xdr_scale_hosted_receipt_and_paired_results(self):
        root=ROOT/'evidence/5.0.2-build104/hosted-xdr-scale'
        run=json.loads((root/'run.json').read_text());receipt=json.loads((root/'artifact.json').read_text())
        self.assertEqual(run['id'],41736609601);self.assertEqual(run['conclusion'],'success')
        self.assertEqual(run['head_sha'],'ebb2948d78165f99733c929b5e8728934b83fa3c')
        self.assertEqual(receipt['digest'],'sha256:'+sha((root/'artifact.zip').read_bytes()))
        v=json.loads((root/'verification.json').read_text());self.assertTrue(v['file_and_case_hashes_matched'])
        with zipfile.ZipFile(root/'artifact.zip') as z:
            for row in v['reports']:
                raw=z.read(row['report']);self.assertEqual(sha(raw),row['sha256'])
                r=json.loads(raw);self.assertEqual(r['source_commit'],row['source_commit'])
                prefix=row['report'].rsplit('/',1)[0]+'/'
                for f in r['files']:self.assertEqual(sha(z.read(prefix+f['path'])),f['sha256'])
                for t in r.get('methods',[]):self.assertEqual(sha(z.read(prefix+t['log'])),t['log_sha256'])
            self.assertEqual(v['reports'][0]['exit_codes'].count(-5),6)
            self.assertEqual(v['reports'][0]['exit_codes'].count(0),3)
            self.assertEqual(v['reports'][1]['exit_codes'],[0]*9)
            cases=json.loads(z.read('adjacent/OathAnkr-cases.json'));self.assertEqual(len(cases),40)
            for t in cases:
                self.assertEqual(t['status'],'passed');self.assertEqual(t['exit_code'],0)
                self.assertEqual(sha(z.read('adjacent/'+t['log'])),t['log_sha256'])

    def test_report_keeps_unresolved_integration_scope(self):
        text=(ROOT/'review/STELLAR-PERSISTENCE.md').read_text()
        for phrase in ['whole-wallet audit remains incomplete','not independent certification','provider','remain open','No new vulnerability']:
            self.assertIn(phrase,text)
