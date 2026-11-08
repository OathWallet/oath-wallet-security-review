import json
import tempfile
import unittest
import zipfile
from test_message_domain_review import ROOT, driver, sha

class HostedMessageDomains(unittest.TestCase):
    def test_exact_source_and_complete_terminal_results(self):
        d = ROOT / 'evidence/5.0.3-build105/hosted-message-domains'
        r = json.loads((d/'run.json').read_text())
        jobs = json.loads((d/'jobs.json').read_text())
        a = json.loads((d/'artifact.json').read_text())
        self.assertEqual(r['id'], 42261460895)
        self.assertEqual(r['head_sha'], '571fdf769a6e8ee7d88713ea05825c561b76d605')
        self.assertEqual((r['status'],r['conclusion']), ('completed','success'))
        self.assertEqual(r['path'], '.github/workflows/message-domain-review.yml')
        self.assertEqual(jobs['total_count'], 1)
        for j in jobs['jobs']:
            self.assertEqual((j['run_id'],j['head_sha']), (r['id'],r['head_sha']))
            self.assertEqual(j['conclusion'], 'success')
            self.assertTrue(all(s['conclusion']=='success' for s in j['steps']))
        raw = (d/'host.zip').read_bytes()
        self.assertEqual(a['digest'], 'sha256:'+sha(raw))
        self.assertEqual(a['size_in_bytes'],len(raw))
        self.assertEqual(a['workflow_run']['id'], r['id'])
        self.assertEqual(a['workflow_run']['head_sha'], r['head_sha'])
        with zipfile.ZipFile(d/'host.zip') as z:
            result = json.loads(z.read('result.json'))
            self.assertEqual(result['source_commit'],driver.COMMIT)
            self.assertEqual(result['fixture_sha256'],sha((ROOT/driver.FIXTURE).read_bytes()))
            self.assertEqual(result['driver_sha256'],sha((ROOT/'scripts/message-domain-review.py').read_bytes()))
            for n,digest in result['helper_sha256'].items():
                self.assertEqual(digest,sha((ROOT/'scripts'/n).read_bytes()))
            for f in result['files']:
                self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            self.assertEqual([s['totals'] for s in result['stages']], [dict(passed=27,skipped=0,failed=0),dict(passed=0,skipped=0,failed=1)])
            manifests=[]
            for s in result['stages']:
                self.assertEqual(s['source_commit'],driver.COMMIT)
                self.assertEqual((s['build_exit_code'],s['runtime_network']), (0,'denied'))
                self.assertEqual(sha(z.read(s['stage']+'/Package.resolved')),s['dependency_lock_sha256'])
                manifests.append({f['path']:f['sha256'] for f in json.loads(z.read(s['stage']+'/source-manifest.json'))})
                for c in s['cases']:
                    self.assertEqual(sha(z.read(c['log'])),c['log_sha256'])
                    self.assertEqual(driver.classify(z.read(c['log']).decode(),c['exit_code']),c['status'])
            self.assertEqual(manifests[0][driver.TARGET],result['fixture_sha256'])
            self.assertEqual(set(manifests[0]),set(manifests[1]))
            self.assertEqual([p for p in manifests[0] if manifests[0][p]!=manifests[1][p]],[driver.CRYPTO])
            self.assertEqual(len({c['selector'] for c in result['stages'][0]['cases']}),27)
            with tempfile.TemporaryDirectory() as tmp:
                out=__import__('pathlib').Path(tmp)
                for c in result['stages'][1]['cases']:
                    p=out/c['log'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(c['log']))
                driver.validate_mutant(result['stages'][1]['cases'],out)
            self.assertIn('Xcode 27.1',z.read('xcode.log').decode())

    def test_merge_receipt_keeps_tested_application_objects(self):
        d=ROOT/'evidence/5.0.3-build105/pr117-merge'
        r=json.loads((d/'source-equivalence.json').read_text())
        pr=json.loads((d/'pull-request.json').read_text())
        self.assertEqual(pr['state'],'MERGED')
        self.assertEqual(pr['headRefOid'],driver.COMMIT)
        self.assertEqual(pr['mergeCommit']['oid'],r['merge_commit'])
        self.assertEqual(r['tested_commit'],driver.COMMIT)
        self.assertEqual(r['non_website_root_objects'][driver.COMMIT],r['non_website_root_objects'][r['merge_commit']])
        self.assertEqual(len(r['all_changed_paths']),21)
        self.assertTrue(all(p.startswith('Website/') for p in r['all_changed_paths']))
        self.assertFalse(r['merge_build_run'])
