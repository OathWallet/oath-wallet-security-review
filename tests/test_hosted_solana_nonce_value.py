import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from test_solana_nonce_value_review import ROOT, driver, sha


class HostedSolanaNonceValueEvidence(unittest.TestCase):
    def test_hosted_replay_binds_terminal_run_artifact_and_each_test(self):
        directory = ROOT / 'evidence/5.0.3-build105/hosted-solana-nonce-value'
        artifact = json.loads((directory / 'artifact.json').read_text())
        receipt = json.loads((directory / 'verification.json').read_text())
        run = json.loads((directory / 'run.json').read_text())
        jobs = json.loads((directory / 'jobs.json').read_text())
        self.assertEqual(run['id'], receipt['run_id'])
        self.assertEqual(run['head_sha'], receipt['audit_commit'])
        self.assertEqual(run['html_url'], receipt['url'])
        self.assertEqual((run['status'], run['conclusion']), ('completed', 'success'))
        self.assertEqual((receipt['workflow_final_status'], receipt['workflow_final_conclusion']), ('completed', 'success'))
        self.assertEqual(run['path'], '.github/workflows/solana-nonce-value-review.yml')
        self.assertEqual(jobs['total_count'], 1)
        self.assertEqual(len(jobs['jobs']), 1)
        job = jobs['jobs'][0]
        self.assertEqual((job['run_id'], job['head_sha']), (run['id'], run['head_sha']))
        self.assertEqual((job['status'], job['conclusion']), ('completed', 'success'))
        self.assertGreater(len(job['steps']), 0)
        self.assertTrue(all((s['status'], s['conclusion']) == ('completed', 'success') for s in job['steps']))
        self.assertEqual(artifact['workflow_run']['id'], run['id'])
        self.assertEqual(artifact['workflow_run']['head_sha'], run['head_sha'])
        self.assertEqual(artifact['size_in_bytes'], (directory / 'artifact.zip').stat().st_size)
        self.assertEqual('sha256:' + sha((directory / 'artifact.zip').read_bytes()), artifact['digest'])
        with zipfile.ZipFile(directory / 'artifact.zip') as z:
            result = json.loads(z.read('result.json'))
            self.assertEqual(sha(z.read('result.json')), receipt['result_sha256'])
            self.assertEqual(result['driver_sha256'], sha((ROOT / 'scripts/solana-nonce-value-review.py').read_bytes()))
            self.assertEqual(result['fixture_sha256'], sha((ROOT / result['fixture']).read_bytes()))
            for name, digest in result['helper_sha256'].items():
                self.assertEqual(digest, sha((ROOT / 'scripts' / name).read_bytes()))
            self.assertEqual((result['baseline_commit'], result['retest_commit']), (driver.BEFORE, driver.AFTER))
            self.assertEqual([s['totals'] for s in result['stages']], receipt['totals'])
            self.assertEqual(receipt['totals'], [dict(passed=4, skipped=0, failed=2), dict(passed=58, skipped=0, failed=0)])
            self.assertEqual(result['duration_seconds'], receipt['duration_seconds'])
            for f in result['files']:
                self.assertEqual(sha(z.read(f['path'])), f['sha256'])
            for stage in result['stages']:
                self.assertEqual((stage['build_exit_code'], stage['runtime_network']), (0, 'denied'))
                self.assertEqual(len({c['selector'] for c in stage['cases']}), sum(stage['totals'].values()))
                for case in stage['cases']:
                    self.assertEqual(sha(z.read(case['log'])), case['log_sha256'])
            with tempfile.TemporaryDirectory() as temp:
                out = Path(temp)
                for case in result['stages'][0]['cases']:
                    p = out / case['log']; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(case['log']))
                driver.validate_baseline(result['stages'][0]['cases'], out)
            for case in result['stages'][1]['cases']:
                self.assertEqual((case['status'], case['exit_code']), ('passed', 0))
                self.assertIn('Executed 1 test, with 0 failures', z.read(case['log']).decode())
