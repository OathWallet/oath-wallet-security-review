import json
import unittest
import zipfile
from test_late_authentication_review import ROOT, E, driver, sha


class HostedLateAuthentication(unittest.TestCase):
    def test_terminal_run_and_complete_production_results(self):
        d = ROOT / 'evidence/5.0.3-build105/hosted-late-authentication'
        run = json.loads((d / 'run.json').read_text())
        jobs = json.loads((d / 'jobs.json').read_text())
        artifact = json.loads((d / 'artifact.json').read_text())
        self.assertEqual(run['id'], 42458592481)
        self.assertEqual(run['head_sha'], '3052916984831b5e62427b06007cc55f3fdf9855')
        self.assertEqual((run['status'], run['conclusion']), ('completed', 'success'))
        self.assertEqual(run['path'], '.github/workflows/late-authentication-review.yml')
        self.assertEqual(jobs['total_count'], 1)
        for job in jobs['jobs']:
            self.assertEqual((job['run_id'], job['head_sha']), (run['id'], run['head_sha']))
            self.assertEqual(job['conclusion'], 'success')
            self.assertTrue(job['steps'])
            self.assertTrue(all(s['conclusion'] == 'success' for s in job['steps']))
        raw = (d / 'host.zip').read_bytes()
        self.assertEqual(artifact['name'], 'late-authentication-review-evidence')
        self.assertEqual(artifact['size_in_bytes'], len(raw))
        self.assertEqual(artifact['digest'], 'sha256:' + sha(raw))
        self.assertEqual(artifact['workflow_run']['id'], run['id'])
        self.assertEqual(artifact['workflow_run']['head_sha'], run['head_sha'])

        with zipfile.ZipFile(d / 'host.zip') as z, zipfile.ZipFile(E / 'runs.zip') as local:
            manifests = []
            results = []
            for stage, mutant in [('production', False), ('mutation', True)]:
                result = json.loads(z.read(stage + '/result.json'))
                original = json.loads(local.read(stage + '/result.json'))
                results.append(result)
                for field in ['source_commit', 'source_sha256', 'compiled_vault_sha256',
                              'fixture_sha256', 'script_sha256', 'harness_original_sha256',
                              'harness_executed_sha256', 'deliberate_mutation', 'exit_code',
                              'cases', 'runtime_network', 'scope']:
                    self.assertEqual(result[field], original[field], field)
                self.assertEqual(result['source_commit'], driver.COMMIT)
                self.assertEqual(result['fixture_sha256'], sha((ROOT / 'fixtures/late-authentication/Checks.swift').read_bytes()))
                self.assertEqual(result['script_sha256'], sha((ROOT / 'scripts/late-authentication-review.py').read_bytes()))
                log = z.read(stage + '/checks.log')
                self.assertEqual(sha(log), result['log_sha256'])
                cases = driver.validate(result['exit_code'], log.decode(), mutant)
                self.assertEqual(result['cases'], [dict(name=n, status=s.lower()) for s, n in cases])
                self.assertEqual(len(cases), 66)
                self.assertEqual(result['runtime_network'], 'denied')
                self.assertEqual(sha(z.read(stage + '/Package.resolved')), result['dependency_lock_sha256'])
                self.assertEqual(json.loads(z.read(stage + '/Package.resolved'))['pins'],
                                 json.loads(local.read(stage + '/Package.resolved'))['pins'])
                self.assertEqual(sha(z.read(stage + '/executed-harness.py')), result['harness_executed_sha256'])
                self.assertEqual(z.read(stage + '/executable.sha256').decode().strip(), result['executable_sha256'])
                self.assertRegex(result['executable_sha256'], r'^[0-9a-f]{64}$')
                manifest = json.loads(z.read(stage + '/generated-manifest.json'))
                manifests.append({f['path']: f['sha256'] for f in manifest})
                self.assertEqual(manifest, json.loads(local.read(stage + '/generated-manifest.json')))
                for file in manifest:
                    self.assertEqual(sha(z.read(stage + '/generated-host/' + file['path'])), file['sha256'])
                self.assertEqual(manifests[-1]['Sources/OathWalletVault.swift'], result['compiled_vault_sha256'])
                self.assertEqual(manifests[-1]['Sources/CheckWalletConnectAuthorization.swift'], result['fixture_sha256'])
                self.assertIn('Xcode 27.1', z.read(stage + '/xcode.log').decode())
                self.assertIn('Python 3.14.7', z.read(stage + '/python.log').decode())
                self.assertGreater(result['duration_seconds'], 0)
            self.assertEqual(results[0]['source_sha256'], results[0]['compiled_vault_sha256'])
            self.assertNotEqual(results[1]['source_sha256'], results[1]['compiled_vault_sha256'])
            self.assertEqual(set(manifests[0]), set(manifests[1]))
            self.assertEqual([p for p in manifests[0] if manifests[0][p] != manifests[1][p]],
                             ['Sources/OathWalletVault.swift'])
            self.assertNotEqual(results[0]['executable_sha256'], results[1]['executable_sha256'])
