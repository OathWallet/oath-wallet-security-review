import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from test_solana_stake_authority_review import ROOT, driver, sha


class HostedSolanaStakeAuthorityEvidence(unittest.TestCase):
    def test_hosted_reproduction_and_build_are_bound_to_exact_sources(self):
        directory = ROOT / 'evidence/5.0.3-build105/hosted-solana-stake-authority'
        receipt = json.loads((directory / 'verification.json').read_text())
        run = json.loads((directory / 'run.json').read_text())
        jobs = json.loads((directory / 'jobs.json').read_text())
        self.assertEqual(run['id'], receipt['run_id'])
        self.assertEqual(run['head_sha'], receipt['audit_commit'])
        self.assertEqual(run['html_url'], receipt['url'])
        self.assertEqual((run['status'], run['conclusion']), ('completed', 'success'))
        self.assertEqual(run['path'], '.github/workflows/solana-stake-authority-review.yml')
        self.assertEqual(jobs['total_count'], 2)
        self.assertEqual({j['name'] for j in jobs['jobs']}, {'host', 'generic-ios'})
        for job in jobs['jobs']:
            self.assertEqual((job['run_id'], job['head_sha']), (run['id'], run['head_sha']))
            self.assertEqual((job['status'], job['conclusion']), ('completed', 'success'))
            self.assertTrue(job['steps'])
            self.assertTrue(all((s['status'], s['conclusion']) == ('completed', 'success') for s in job['steps']))
        archives = {}
        for kind in ['host', 'ios']:
            artifact = json.loads((directory / (kind + '-artifact.json')).read_text())
            raw = directory / (kind + '.zip')
            self.assertEqual(artifact['workflow_run']['id'], run['id'])
            self.assertEqual(artifact['workflow_run']['head_sha'], run['head_sha'])
            self.assertEqual(artifact['size_in_bytes'], raw.stat().st_size)
            self.assertEqual('sha256:' + sha(raw.read_bytes()), artifact['digest'])
            archives[kind] = zipfile.ZipFile(raw)
            self.addCleanup(archives[kind].close)
        z = archives['host']
        result = json.loads(z.read('result.json'))
        self.assertEqual(sha(z.read('result.json')), receipt['host_result_sha256'])
        self.assertEqual(result['baseline_commit'], driver.BEFORE)
        self.assertEqual(result['fix_commit'], driver.AFTER)
        self.assertEqual(result['retest_commit'], driver.AFTER)
        self.assertEqual(result['driver_sha256'], sha((ROOT / 'scripts/solana-stake-authority-review.py').read_bytes()))
        self.assertEqual(result['fixture_sha256'], sha((ROOT / result['fixture']).read_bytes()))
        self.assertEqual(result['corpus_sha256'], sha((ROOT / result['corpus']).read_bytes()))
        for name, digest in result['helper_sha256'].items():
            self.assertEqual(digest, sha((ROOT / 'scripts' / name).read_bytes()))
        self.assertEqual([s['totals'] for s in result['stages']], receipt['totals'])
        self.assertEqual(receipt['totals'], [dict(passed=2, skipped=0, failed=7), dict(passed=67, skipped=0, failed=0)])
        self.assertEqual(result['duration_seconds'], receipt['host_duration_seconds'])
        for f in result['files']:
            self.assertEqual(sha(z.read(f['path'])), f['sha256'])
        self.assertEqual([s['source_commit'] for s in result['stages']], [driver.BEFORE, driver.AFTER])
        self.assertEqual(len({s['executable_sha256'] for s in result['stages']}), 2)
        for stage in result['stages']:
            self.assertEqual((stage['build_exit_code'], stage['runtime_network']), (0, 'denied'))
            self.assertEqual(stage['fixture_sha256'], result['fixture_sha256'])
            self.assertEqual(sha(z.read(stage['stage'] + '/Package.resolved')), stage['dependency_lock_sha256'])
            manifest = {f['path']: f['sha256'] for f in json.loads(z.read(stage['stage'] + '/source-manifest.json'))}
            self.assertEqual(manifest[driver.TARGET], result['fixture_sha256'])
            self.assertEqual(manifest[driver.CORPUS_TARGET], result['corpus_sha256'])
            for case in stage['cases']:
                self.assertEqual(sha(z.read(case['log'])), case['log_sha256'])
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for c in result['stages'][0]['cases']:
                p = out / c['log']; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(c['log']))
            driver.validate_baseline(result['stages'][0]['cases'], out)
        after = result['stages'][1]['cases']
        self.assertEqual(len({c['selector'] for c in after}), 67)
        self.assertEqual(sum(c['selector'].startswith(driver.CASE_PREFIX) for c in after), 9)
        for case in after:
            self.assertEqual((case['status'], case['exit_code']), ('passed', 0))
            self.assertEqual(driver.classify(z.read(case['log']).decode(), case['exit_code']), 'passed')
            self.assertIn('Executed 1 test, with 0 failures', z.read(case['log']).decode())
        ios = archives['ios']
        build = json.loads(ios.read('build.json'))
        self.assertEqual(sha(ios.read('build.json')), receipt['ios_result_sha256'])
        self.assertEqual(build['source_commit'], driver.AFTER)
        self.assertEqual((build['check'], build['status'], build['exit_code']), ('build', 'passed', 0))
        self.assertEqual(build['runtime_scope'], 'compile-only')
        self.assertFalse(build['live_network_tests_enabled'])
        self.assertIn('generic/platform=iOS', build['command'])
        self.assertIn('CODE_SIGNING_ALLOWED=NO', build['command'])
        self.assertEqual(sha(ios.read('build.log')), build['log_sha256'])
        self.assertIn('** BUILD SUCCEEDED **', ios.read('build.log').decode())
        self.assertIn('Xcode 27.1', z.read('xcode.log').decode())
        self.assertIn('/Applications/Xcode_27.1.app/', ios.read('build.log').decode())
        self.assertIn('iPhoneOS27.1.sdk', ios.read('build.log').decode())
        # The workflow piped stdout, but toolchain.sh writes its own file outside
        # this artifact directory. Preserve the empty capture and disclose it.
        self.assertEqual(ios.read('toolchain.log'), b'')
        self.assertIn('empty', receipt['ios_toolchain_capture_limitation'])
