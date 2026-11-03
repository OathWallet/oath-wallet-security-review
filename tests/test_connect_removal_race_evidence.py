import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/'evidence/5.0.1-build103/connect-removal-race'
read=lambda p:json.loads((ROOT/p).read_text())
class RemovalRaceEvidence(unittest.TestCase):
    def test_manifest_binds_published_and_expanded_bytes(self):
        m=read('manifest.json')
        self.assertGreater(len(m['files']),2500)
        for entry in m['files']:
            data=(ROOT/entry['path']).read_bytes()
            self.assertEqual(len(data),entry['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),entry['sha256'],entry['path'])
            if entry['path'].endswith('.gz'):data=gzip.decompress(data)
            self.assertEqual(hashlib.sha256(data).hexdigest(),entry['uncompressed_sha256'],entry['path'])
            if not entry['sanitized']:self.assertEqual(entry['original_sha256'],entry['uncompressed_sha256'])
    def test_same_fixture_exposes_race_then_passes(self):
        before,after,recovery=[read(p+'/result.json') for p in ['before','after','recovery']]
        self.assertEqual(before['fixture_sha256'],after['fixture_sha256'])
        self.assertEqual([c['name'] for c in before['cases']],[c['name'] for c in after['cases']])
        for r,passed,failed,code in [(before,19,4,1),(after,23,0,0),(recovery,30,0,0)]:
            self.assertEqual(sum(c['status']=='pass' for c in r['cases']),passed)
            self.assertEqual(sum(c['status']=='fail' for c in r['cases']),failed)
            self.assertEqual(r['exit_code'],code)
            self.assertEqual(r['runtime_network'],'denied')
        self.assertEqual(after['source_commit'],read('manifest.json')['after'])
        self.assertEqual(recovery['source_commit'],after['source_commit'])
    def test_final_gates_and_explicit_skips(self):
        m=read('manifest.json')
        for name in ['OathDatabase','OathDiagnostics','public','diagnostics-coverage','build']:
            result=read('validation/'+name+'.json')
            self.assertEqual(result['source_commit'],m['after']);self.assertEqual(result['status'],'passed')
        for package,expected in [('OathDatabase',{'passed':748,'skipped':72}),('OathDiagnostics',{'passed':119,'skipped':2})]:
            self.assertEqual(dict(Counter(x['status'] for x in read('validation/'+package+'-cases.json'))),expected)
        self.assertEqual(read('validation/gitleaks.json'),[])
    def test_failed_attempts_are_retained(self):
        for folder,name in [('initial-validation','testUpgradePreservesExistingWalletAndCreatesEmptyFence'),('previous-pin','testLaggingDiscoveryWithoutProviderFailureRemainsIncomplete')]:
            cases=read('attempts/'+folder+'/OathDatabase-cases.json')
            failed=[c for c in cases if c['status']=='failed']
            self.assertEqual(len(failed),1);self.assertTrue(failed[0]['selector'].endswith('/'+name))
        isolated=read('attempts/aptos-isolated/OathDatabase-cases.json')
        self.assertEqual(len(isolated),1);self.assertEqual(isolated[0]['status'],'passed')
        scanner=read('attempts/scanner-path/summary.json')
        self.assertEqual(scanner['normalized_unmatched'],[])
    def test_broad_host_checks_keep_their_original_pin(self):
        m=read('manifest.json');binding=read('source-binding.json')['production_equivalence']
        self.assertEqual(binding['to'],m['after'])
        self.assertEqual(binding['changed_files'],['Packages/OathDatabase/Tests/OathDatabaseTests/AptosLedgerTests.swift'])
        for check in ['lifecycle','authentication','protected-startup']:
            result=m['checks'][check]
            self.assertEqual(result['source_commit'],binding['from']);self.assertEqual(result['status'],'passed')
