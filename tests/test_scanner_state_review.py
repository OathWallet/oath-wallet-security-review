import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/5.0.2-build104/scanner-state'
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
def sha(b):return hashlib.sha256(b).hexdigest()
class ScannerStateEvidence(unittest.TestCase):
 def archive(self):
  z=zipfile.ZipFile(E/'runs.zip');self.addCleanup(z.close)
  c=json.loads(z.read('CHECKSUMS.json'))
  self.assertEqual(set(z.namelist()),{f['path'] for f in c}|{'CHECKSUMS.json'})
  for f in c:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
  r=json.loads(z.read('result.json'));self.assertEqual(r['source_commit'],PIN)
  self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/scanner-state-review.py').read_bytes()))
  for f in r['files']+[f for row in r['stages'] for f in row['files']]:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
  return z,r
 def test_expected_negative_controls(self):
  z,r=self.archive()
  expected={'baseline':[],'accept-without-phase':['exhaustive-handoff'],'deliver-after-cancel':['exhaustive-handoff','payload-lifetime'],'retain-payload':['exhaustive-handoff','payload-lifetime'],'duplicate-claim':['concurrent-claims','idempotent-start'],'stale-generation':['concurrent-claims','generation-invalidation']}
  self.assertEqual([s['stage'] for s in r['stages']],list(expected))
  self.assertEqual(len({s['executable_sha256'] for s in r['stages']}),6)
  for s in r['stages']:
   self.assertEqual(s['runtime_network'],'denied')
   self.assertEqual(s['fixture_sha256'],sha((ROOT/'fixtures/scanner-state/Checks.swift').read_bytes()))
   self.assertEqual([c['name'] for c in s['cases'] if c['status']=='fail'],expected[s['stage']])
   self.assertEqual((s['passed'],s['failed'],s['exit_code']),(5-len(expected[s['stage']]),len(expected[s['stage']]),int(bool(expected[s['stage']]))))
   log=z.read(s['stage']+'/run.log').decode()
   self.assertEqual([(v.lower(),n,d) for v,n,d in re.findall(r'^(PASS|FAIL): ([a-z-]+)(?:: (.*))?$',log,re.M)],[(c['status'],c['name'],c['detail']) for c in s['cases']])
 def test_complete_production_file_and_exact_mutations(self):
  z,r=self.archive();base=z.read('baseline/State.swift')
  self.assertEqual(sha(base),r['production_sha256'])
  sys.path.insert(0,str(ROOT/'scripts'))
  try:
   spec=importlib.util.spec_from_file_location('scanner_review',ROOT/'scripts/scanner-state-review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  finally:sys.path.pop(0)
  for stage,(old,new) in m.MUTATIONS.items():self.assertEqual(z.read(stage+'/State.swift').decode(),base.decode().replace(old,new))
  log=z.read('baseline/run.log').decode()
  self.assertIn('137256 transition prefixes through depth 6, 274512 return/phase comparisons',log)
  self.assertIn('6400 concurrent claim attempts across 100 activations',log)
  self.assertEqual((r['existing_handoff']['checks'],r['existing_handoff']['exit_code']),(106,0))
 def test_source_read_binding(self):
  b=json.loads((E/'source-binding.json').read_text());self.assertEqual(b['reviewed_commit'],PIN)
  inv={f['path']:f for f in json.loads((ROOT/'scope/inventory.json').read_text())['files']}
  self.assertEqual(len(b['files']),4)
  for f in b['files']:
   self.assertEqual(f['sha256'],inv[f['path']]['sha256']);self.assertTrue(f['baseline_identical'])
   self.assertEqual(f['status'],inv[f['path']]['status']);self.assertEqual(f['read_ranges'][0][0],1)
   self.assertIn('review/SCANNER-STATE-BOUNDARIES.md',inv[f['path']]['evidence'])
 def test_manifest_and_no_completion_claim(self):
  m=json.loads((E/'manifest.json').read_text());self.assertEqual(m['source_commit'],PIN)
  for f in m['files']:self.assertEqual(sha((E/f['path']).read_bytes()),f['sha256'])
  for key in ['application_changed','new_confirmed_defect','whole_wallet_complete','new_ios_build_performed']:self.assertFalse(m[key])
  report=(ROOT/'review/SCANNER-STATE-BOUNDARIES.md').read_text()
  for phrase in ['whole-wallet audit remains incomplete','not independent certification','not discovered production defects','No new generic']:
   self.assertIn(phrase,report)
 def test_workflow_and_network_boundaries(self):
  w=(ROOT/'.github/workflows/scanner-state-review.yml').read_text()
  self.assertIn(PIN,w);self.assertIn('contents: read',w);self.assertIn('test_scanner_state_review.py',w)
  self.assertNotIn('secrets.',w);self.assertNotIn('pull_request',w)
  for action in re.findall(r'uses: ([^\s]+)',w):self.assertRegex(action,r'@[a-f0-9]{40}$')
  s=(ROOT/'scripts/scanner-state-review.py').read_text()
  for phrase in ['Fresh scratch/output required','(deny network*)','require_source_state(source,PIN)','Negative control failed outside expected groups']:
   self.assertIn(phrase,s)
 def test_hosted_backup_receipt(self):
  p=ROOT/'evidence/5.0.2-build104/hosted-backup-settings'
  a=json.loads((p/'artifact.json').read_text());run=json.loads((p/'run.json').read_text())
  self.assertEqual((run['id'],run['head_sha'],run['conclusion']),(41754349979,'2c1753979e98c1c9708ad126e2402b1799c3c492','success'))
  self.assertEqual(a['digest'],'sha256:'+sha((p/'artifact.zip').read_bytes()))
  with zipfile.ZipFile(p/'artifact.zip') as z:
   r=json.loads(z.read('result.json'));self.assertEqual(r['source_commit'],PIN)
   self.assertEqual(r['driver_sha256'],sha((ROOT/'scripts/backup-settings-review.py').read_bytes()))
   for f in r['files']+[f for row in r['stages'] for f in row['files']]:self.assertEqual(sha(z.read(f['path'])),f['sha256'])
   self.assertEqual([(s['passed'],s['failed'],s['exit_code']) for s in r['stages']],[(52,0,0),(40,12,1)])
   self.assertEqual(r['all_wallet_model']['passed'],15)
 def test_original_attempt_retained(self):
  with zipfile.ZipFile(E/'attempt1.zip') as z:
   for f in json.loads(z.read('CHECKSUMS.json')):self.assertEqual(sha(z.read(f['path'])),f['sha256'])
   r=json.loads(z.read('result.json'))
   self.assertEqual((r['stages'][0]['passed'],r['stages'][0]['failed']),(5,0))
