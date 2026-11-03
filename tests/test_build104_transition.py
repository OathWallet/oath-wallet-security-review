import hashlib
import json
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((R/name).read_text())
class Build104Transition(unittest.TestCase):
    def test_current_target_and_historical_pin_remain_distinct(self):
        now=read('scope/source.json');old=read('scope/history/5.0.1-build103/source.json')
        self.assertEqual((now['version'],now['build'],now['release_channel']),('5.0.2','104','prerelease'))
        self.assertEqual((old['version'],old['build']),('5.0.1','103'))
        self.assertNotEqual(now['reviewed_commit'],old['reviewed_commit'])
        self.assertFalse(now['app_store_upload_performed'])
    def test_inherited_decisions_require_identical_bytes(self):
        old=read('scope/history/5.0.1-build103/dispositions.json');new=read('review/dispositions.json')
        for name,value in new.items():self.assertEqual(value,old[name],name)
        ledger={x['path']:x for x in read('scope/inventory.json')['files']}
        for name,value in new.items():self.assertEqual(value['sha256'],ledger[name]['sha256'])
        transition=read('evidence/5.0.2-build104/target-transition.json')
        for row in transition['changed_dispositions']:
            self.assertNotIn(row['path'],new)
            self.assertNotEqual(row['previous']['sha256'],row['current_sha256'])
    def test_compiler_trace_matches_current_target_and_scoped_hashes(self):
        p='evidence/5.0.2-build104/compiler/'
        trace=read(p+'release-inputs.json');coverage=read(p+'dispositions.json')
        self.assertEqual(trace['source_commit'],read('scope/source.json')['reviewed_commit'])
        self.assertEqual(coverage['trace_manifest_sha256'],hashlib.sha256((R/(p+'release-inputs.json')).read_bytes()).hexdigest())
        self.assertEqual(len(trace['files']),coverage['input_count'])
        self.assertEqual({x['path']:x['sha256'] for x in trace['files']},{x['path']:x['sha256'] for x in coverage['files']})
    def test_historical_findings_retain_original_source_pins(self):
        old=read('scope/history/5.0.1-build103/findings.json');now=read('findings/index.json')
        current_by_id={item['id']:item for item in now}
        self.assertEqual(len(current_by_id),len(now), 'Finding IDs must be unique')
        self.assertTrue({item['id'] for item in old}.issubset(current_by_id))
        for before in old:
            after=current_by_id[before['id']]
            self.assertEqual({k:v for k,v in after.items() if k!='current_target'},before)
            self.assertEqual(after['current_target']['commit'],read('scope/source.json')['reviewed_commit'])
