import json
import unittest
import zipfile
from test_installation_binding_review import ROOT, driver, sha


class HostedInstallationBindingEvidence(unittest.TestCase):
    def test_failed_baseline_and_independent_results_remain_separate(self):
        d = ROOT / 'evidence/5.0.3-build105/hosted-installation-binding'
        run = json.loads((d / 'run.json').read_text())
        jobs = json.loads((d / 'jobs.json').read_text())
        artifact = json.loads((d / 'artifact.json').read_text())
        receipt = json.loads((d / 'verification.json').read_text())
        self.assertEqual((run['status'], run['conclusion']), ('completed', 'failure'))
        self.assertEqual(run['path'], '.github/workflows/installation-binding-review.yml')
        self.assertEqual(run['id'], receipt['run_id'])
        self.assertEqual(run['head_sha'], receipt['audit_commit'])
        self.assertEqual(run['html_url'], receipt['url'])
        self.assertEqual((receipt['workflow_final_status'], receipt['workflow_final_conclusion']), ('completed', 'failure'))
        self.assertFalse(receipt['aggregate_pass'])
        self.assertFalse(receipt['baseline_completed_assertions_known'])
        self.assertEqual(jobs['total_count'], 1)
        self.assertEqual(len(jobs['jobs']), 1)
        job = jobs['jobs'][0]
        self.assertEqual((job['run_id'], job['head_sha']), (run['id'], run['head_sha']))
        self.assertEqual((job['status'], job['conclusion']), ('completed', 'failure'))
        failures = [s for s in job['steps'] if s['conclusion'] == 'failure']
        self.assertEqual(len(failures), 1)
        self.assertIn('git clone', failures[0]['name'])
        self.assertEqual(artifact['workflow_run']['id'], run['id'])
        self.assertEqual(artifact['workflow_run']['head_sha'], run['head_sha'])
        self.assertEqual(artifact['size_in_bytes'], (d / 'artifact.zip').stat().st_size)
        self.assertEqual(artifact['digest'], 'sha256:' + sha((d / 'artifact.zip').read_bytes()))
        with zipfile.ZipFile(d / 'artifact.zip') as z:
            raw = z.read('result.json'); result = json.loads(raw)
            self.assertEqual(sha(raw), receipt['result_sha256'])
            self.assertEqual(result['source_commit'], driver.COMMIT)
            self.assertEqual(receipt['source_commit'], driver.COMMIT)
            self.assertEqual(result['driver_sha256'], sha((ROOT / 'scripts/installation-binding-review.py').read_bytes()))
            self.assertEqual(result['fixture_sha256'], sha((ROOT / driver.FIXTURE).read_bytes()))
            self.assertEqual(result['helper_sha256'], sha((ROOT / 'scripts/source_state.py').read_bytes()))
            self.assertEqual(result['overall_status'], 'failed')
            self.assertEqual(result['duration_seconds'], receipt['duration_seconds'])
            self.assertEqual([s['totals'] for s in result['stages']], receipt['totals'])
            self.assertEqual(receipt['totals'], [None, dict(passed=2647, failed=0, skipped=0), dict(passed=0, failed=12, skipped=0)])
            self.assertEqual([s['stage'] for s in result['stages']], ['baseline', 'production', 'mutation-control'])
            self.assertEqual([s['exit_code'] for s in result['stages']], [-5, 0, 1])
            self.assertFalse(result['stages'][0]['completed_assertions_known'])
            self.assertIn('Installation key is excluded from device backups', z.read('baseline-diagnostic.log').decode())
            for f in result['files']:
                self.assertEqual(sha(z.read(f['path'])), f['sha256'])
            for s in result['stages']:
                self.assertEqual((s['build_exit_code'], s['runtime_network']), (0, 'denied'))
                self.assertEqual(sha(z.read(s['stage']+'-source.swift')), s['source_sha256'])
            original = z.read('production-source.swift').decode()
            self.assertEqual(original.count(driver.GUARD), 1)
            self.assertEqual(z.read('mutation-control-source.swift').decode(), original.replace(driver.GUARD, driver.MUTANT))
            production = json.loads(z.read('production.log'))
            self.assertEqual(len(production['cases']), 2647)
            self.assertEqual(len({c['case'] for c in production['cases']}), 2647)
            self.assertTrue(all(c['passed'] for c in production['cases']))
            driver.validate_mutant(1, json.loads(z.read('mutation-control.log')))
