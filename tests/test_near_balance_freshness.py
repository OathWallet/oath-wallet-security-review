import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BEFORE='5d91d1e4dfd36c56031c7a8fb1ee305446dc54de'
AFTER='fd06fdff104d128e00cc414d2de1472f11752e04'
FAILED={'testFailedTokenReadCannotCompletePostSendRefresh','testNewObservationFromBeforeExecutionBlockIsNotCurrent','testNativeSendRequiresExecutionHeightAndSuccessfulBalance','testFailedTokenReadRecoversOnlyAfterSuccessfulNewRead'}
def digest(raw):return hashlib.sha256(raw).hexdigest()

class NearBalanceFreshnessEvidence(unittest.TestCase):
    def test_paired_production_results_are_bound_to_logs_and_sources(self):
        root=ROOT/'evidence/5.0.2-build104/near-balance-freshness'
        manifest=json.loads((root/'manifest.json').read_text())
        for row in manifest['files']:self.assertEqual(digest((root/row['path']).read_bytes()),row['sha256'])
        fixture=ROOT/'fixtures/near-balance-freshness/NearSendBalanceFreshnessTests.swift'
        names=set(re.findall(r'func (test\w+)\(',fixture.read_text()))
        self.assertEqual(len(names),6)
        with zipfile.ZipFile(root/'runs.zip') as z:
            checks=json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()),{r['path'] for r in checks}|{'CHECKSUMS.json'})
            for row in checks:self.assertEqual(digest(z.read(row['path'])),row['sha256'])
            for mode,pin in [('before',BEFORE),('after',AFTER)]:
                report=json.loads(z.read(mode+'/result.json'))
                self.assertEqual(report['source_commit'],pin)
                self.assertEqual(report['baseline'],mode=='before')
                self.assertEqual(report['source_sha256'],report['executed_source_sha256'])
                self.assertEqual(report['overlay_sha256'],digest(fixture.read_bytes()))
                self.assertEqual(report['driver_sha256'],digest((ROOT/'scripts/near-balance-freshness.py').read_bytes()))
                self.assertEqual(report['isolation_classifier_sha256'],digest((ROOT/'scripts/isolated_tests.py').read_bytes()))
                self.assertEqual({r['method'] for r in report['methods']},names)
                self.assertEqual({r['method'] for r in report['methods'] if r['status']!='passed'},FAILED if mode=='before' else set())
                for row in report['files']:self.assertEqual(digest(z.read(mode+'/'+row['path'])),row['sha256'])
                for row in report['methods']:
                    raw=z.read(mode+'/'+row['log'])
                    self.assertEqual(digest(raw),row['log_sha256'])
                    self.assertIn(b'Executed 1 test',raw)
                    self.assertEqual(row['exit_code']==0,row['status']=='passed')
                    if row['status']=='failed':self.assertIn(b'XCTAssertFalse failed',raw)
            adjacent=json.loads(z.read('adjacent/result.json'))
            self.assertEqual(adjacent['source_commit'],AFTER)
            self.assertEqual(adjacent['driver_sha256'],digest((ROOT/'scripts/near-balance-adjacent.py').read_bytes()))
            self.assertEqual(len(adjacent['methods']),24)
            for row in adjacent['methods']:
                self.assertEqual(row['status'],'passed');self.assertEqual(row['exit_code'],0)
                self.assertNotIn('/testLive',row['method'])
                raw=z.read('adjacent/'+row['log']);self.assertEqual(digest(raw),row['log_sha256']);self.assertIn(b'Executed 1 test',raw)

    def test_workflow_and_source_dispositions_keep_boundaries(self):
        for name in ['near-balance-freshness','near-balance-adjacent']:
            driver=(ROOT/'scripts'/(name+'.py')).read_text()
            self.assertIn('(deny network*)',driver);self.assertIn('require_source_state',driver)
        workflow=(ROOT/'.github/workflows/near-balance-freshness.yml').read_text()
        self.assertIn(BEFORE,workflow);self.assertIn(AFTER,workflow)
        self.assertIn('contents: read',workflow)
        self.assertNotIn('secrets.',workflow);self.assertNotIn('pull_request_target',workflow)
        rows=json.loads((ROOT/'evidence/5.0.2-build104/near-balance-freshness/source-binding.json').read_text())['files']
        ledger={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(len(rows),4)
        for row in rows:
            self.assertEqual(row['sha256'],ledger[row['path']]['sha256'])
            self.assertEqual(row['status'],'partially-reviewed')
            self.assertEqual(row['status'],ledger[row['path']]['status'])

    def test_hosted_lifecycle_receipt_is_exact(self):
        root=ROOT/'evidence/5.0.2-build104/hosted-near-multisig-lifecycle'
        manifest=json.loads((root/'manifest.json').read_text())
        run=json.loads((root/'run.json').read_text());metadata=json.loads((root/'metadata.json').read_text())
        self.assertEqual(run['id'],41617104807);self.assertEqual(run['head_sha'],manifest['audit_commit'])
        self.assertEqual(run['status'],'completed');self.assertEqual(run['conclusion'],'success')
        self.assertEqual(metadata['digest'],'sha256:'+digest((root/'artifact.zip').read_bytes()))
        self.assertEqual(metadata['workflow_run']['head_sha'],run['head_sha'])
        for row in manifest['files']:self.assertEqual(digest((root/row['path']).read_bytes()),row['sha256'])
        with zipfile.ZipFile(root/'artifact.zip') as z:
            for row in manifest['expanded_files_verified']:self.assertEqual(digest(z.read(row['path'])),row['sha256'])
            for mode in ['control','mutant']:
                report=json.loads(z.read(mode+'/result.json'))
                self.assertEqual(report['source_commit'],BEFORE)
                self.assertEqual(len(report['methods']),6)
                failures={r['method'] for r in report['methods'] if r['status']!='passed'}
                self.assertEqual(failures,{'testChangedRequestAndProposalIDNeverReleaseConfirmation'} if mode=='mutant' else set())
                for row in report['files']:self.assertEqual(digest(z.read(mode+'/'+row['path'])),row['sha256'])
