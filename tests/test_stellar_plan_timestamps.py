import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '152e094f85f196479d2ab08856eaf3b0264cd6c1'
AFTER = '814596f8bb25a2c32ea25bba1fb036aee3303ca6'
def sha(raw): return hashlib.sha256(raw).hexdigest()

class StellarPlanTimestampEvidence(unittest.TestCase):
    def test_paired_crashes_and_adjacent_results(self):
        root = ROOT / 'evidence/5.0.2-build104/stellar-plan-timestamps'
        with zipfile.ZipFile(root / 'runs.zip') as z:
            files = json.loads(z.read('CHECKSUMS.json'))
            self.assertEqual(set(z.namelist()), {f['path'] for f in files} | {'CHECKSUMS.json'})
            for f in files: self.assertEqual(sha(z.read(f['path'])), f['sha256'])
            for mode,pin,codes in [('before',BEFORE,[0,-5,-5,0,-5,0]),('after',AFTER,[0]*6)]:
                r = json.loads(z.read(mode + '/result.json'))
                self.assertEqual(r['source_commit'],pin)
                self.assertEqual([t['exit_code'] for t in r['methods']],codes)
                self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/stellar-plan-timestamps.py').read_bytes()))
                self.assertEqual(r['overlay_sha256'],sha((ROOT/'fixtures/stellar-plan-timestamps/StellarPlanTimestampTests.swift').read_bytes()))
                for f in r['production']: self.assertEqual(f['source_sha256'],f['executed_sha256'])
                for t in r['methods']:
                    log = z.read(mode + '/' + t['log'])
                    self.assertEqual(sha(log), t['log_sha256'])
                    if t['exit_code'] == 0:
                        self.assertEqual(t['status'],'passed');self.assertIn(b'Executed 1 test',log)
                for f in r['files']: self.assertEqual(sha(z.read(mode + '/' + f['path'])),f['sha256'])
            r = json.loads(z.read('adjacent/result.json'))
            self.assertEqual(r['source_commit'],AFTER);self.assertEqual(r['passed'],40)
            self.assertEqual(r['script_sha256'],sha((ROOT/'scripts/xdr-scale-regressions.py').read_bytes()))
            self.assertEqual(r['isolation_driver_sha256'],sha((ROOT/'scripts/isolated_tests.py').read_bytes()))
            for f in r['files']: self.assertEqual(sha(z.read('adjacent/' + f['path'])),f['sha256'])
            rows = json.loads(z.read('adjacent/OathAnkr-cases.json'))
            self.assertEqual(len(rows),40);self.assertEqual(len({r['selector'] for r in rows}),40)
            for row in rows:
                self.assertEqual(row['status'],'passed');self.assertEqual(row['exit_code'],0)
                self.assertNotIn('/testLive',row['selector'])
                self.assertEqual(sha(z.read('adjacent/'+row['log'])),row['log_sha256'])

    def test_scope_is_partial_and_hash_bound(self):
        rows=json.loads((ROOT/'evidence/5.0.2-build104/stellar-plan-timestamps/source-binding.json').read_text())['files']
        inv={r['path']:r for r in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
        self.assertEqual(len(rows),5)
        for r in rows:
            self.assertTrue(r['baseline_identical']);self.assertEqual(r['status'],'partially-reviewed')
            self.assertEqual(r['sha256'],inv[r['path']]['sha256'])
            self.assertIn('review/STELLAR-PLAN-TIMESTAMPS.md',inv[r['path']]['evidence'])

    def test_workflow_pins_and_network_boundary(self):
        text=(ROOT/'.github/workflows/stellar-plan-timestamps.yml').read_text()
        self.assertIn(BEFORE,text);self.assertIn(AFTER,text);self.assertIn('contents: read',text)
        self.assertNotIn('pull_request',text);self.assertNotIn('secrets.',text)
        for name in ['stellar-plan-timestamps.py','xdr-scale-regressions.py']:
            source=(ROOT/'scripts'/name).read_text()
            self.assertIn('(deny network*)',source);self.assertIn('require_source_state',source)
            self.assertIn("'--build-tests'",source)

    def test_validation_and_merge_are_bound_to_repair(self):
        root=ROOT/'evidence/5.0.2-build104/stellar-plan-timestamps'
        m=json.loads((root/'manifest.json').read_text())
        self.assertEqual(m['before_commit'],BEFORE);self.assertEqual(m['repair_commit'],AFTER)
        for f in m['files']:self.assertEqual(sha((root/f['path']).read_bytes()),f['sha256'])
        binding=json.loads((root/'validation/merge-binding.json').read_text())
        self.assertEqual(binding['repair_commit'],AFTER);self.assertTrue(binding['complete_trees_equal'])
        self.assertEqual(binding['merge_commit'],m['merge_commit'])
        self.assertEqual(json.loads((root/'validation/ios-build-result.json').read_text())['exit_code'],0)
        self.assertIn('** BUILD SUCCEEDED **',(root/'validation/ios-build.log').read_text())
        self.assertEqual(json.loads((root/'validation/diagnostics-result.json').read_text())['exit_code'],0)
        self.assertIn('Executed 121 tests, with 2 tests skipped and 0 failures',(root/'validation/diagnostics-tests.log').read_text())

    def test_rejected_harness_attempts_and_distinct_final_executables(self):
        root = ROOT/'evidence/5.0.2-build104/stellar-plan-timestamps'
        attempts=json.loads((root/'attempts.json').read_text())
        self.assertEqual(sha((root/'attempts.zip').read_bytes()),attempts['archive_sha256'])
        with zipfile.ZipFile(root/'attempts.zip') as z:
            for f in json.loads(z.read('CHECKSUMS.json')):
                self.assertEqual(sha(z.read(f['path'])),f['sha256'])
            before=json.loads(z.read('initial-baseline-results/result.json'))
            stale=json.loads(z.read('stale-cache-after-results/result.json'))
            self.assertEqual(before['test_executable_sha256'],stale['test_executable_sha256'])
        with zipfile.ZipFile(root/'runs.zip') as z:
            before=json.loads(z.read('before/result.json'))
            after=json.loads(z.read('after/result.json'))
            self.assertNotEqual(before['test_executable_sha256'],after['test_executable_sha256'])
        driver=(ROOT/'scripts/stellar-plan-timestamps.py').read_text()
        self.assertNotIn('--build-cache',driver)
        self.assertIn("if cache.exists():raise ValueError('Fresh build directory required')",driver)

    def test_previous_hosted_archives_match_github_receipts_and_reports(self):
        specs=[('hosted-history-restart',41731731469,'bee44ceb985abb233bd0c3219cbe0330130a84d8'),('hosted-sui-signing',41734504160,'4635634074ba3f87c633b69e6d4eb2930e921446')]
        for folder,run_id,head in specs:
            root=ROOT/'evidence/5.0.2-build104'/folder
            run=json.loads((root/'run.json').read_text())
            receipt=json.loads((root/'artifact.json').read_text())
            verified=json.loads((root/'verification.json').read_text())
            self.assertEqual(run['id'],run_id);self.assertEqual(run['head_sha'],head)
            self.assertEqual(run['conclusion'],'success')
            self.assertEqual(receipt['digest'],'sha256:'+sha((root/'artifact.zip').read_bytes()))
            self.assertEqual(verified['run_id'],run_id)
            with zipfile.ZipFile(root/'artifact.zip') as z:
                for r in verified['reports']:
                    raw=z.read(r['report']);self.assertEqual(sha(raw),r['sha256'])
                    body=json.loads(raw);self.assertEqual(body['source_commit'],r['source_commit'])
                    self.assertEqual([t['exit_code'] for t in body['methods']],r['exit_codes'])
                    prefix=r['report'].rsplit('/',1)[0]+'/'
                    for item in body['files']:
                        self.assertEqual(sha(z.read(prefix+item['path'])),item['sha256'])
                    for item in body['methods']:
                        self.assertEqual(sha(z.read(prefix+item['log'])),item['log_sha256'])
