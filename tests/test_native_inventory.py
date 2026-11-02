from pathlib import Path
import runpy
import unittest

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/bdk-native-ledger.py'))
ledger = MODULE['ledger']

class NativeInputEvidence(unittest.TestCase):
    def setUp(self):
        self.files = [{'path':p, 'role':'registry','sha256':'a'*64,'bytes':1} for p in MODULE['MANUAL']]
        self.inputs = [x['path'] for x in self.files]
        self.trace = {'lock_sha256':'pin','registry_archives':{},'files': self.files,
                      'objects':[{'source':self.inputs[0],'inputs':self.inputs}]}
        self.rust = {'lock_sha256':'pin','files':[]}

    def test_prior_same_file_counted_once(self):
        self.rust['files'].append(self.files[0])
        result=ledger(self.trace,self.rust)
        self.assertEqual(len(result['files']),len(self.files)-1)
        self.assertTrue(all(r['included_by_objects']==1 for r in result['files']))

    def test_rejects_disagreeing_hashes(self):
        self.rust['files']=[dict(self.files[0],sha256='b'*64)]
        with self.assertRaisesRegex(ValueError,'Prior input hash differs'):
            ledger(self.trace,self.rust)

    def test_rejects_duplicate_source_record(self):
        self.trace['files']=self.files+[self.files[0]]
        with self.assertRaisesRegex(ValueError,'Duplicate compiler input'):
            ledger(self.trace,self.rust)

    def test_missing_compiler_dependency(self):
        self.inputs.append('absent-private.h')
        with self.assertRaisesRegex(ValueError,'missing inputs'):
            ledger(self.trace,self.rust)

    def test_wrong_source_lock(self):
        self.rust['lock_sha256']='different'
        with self.assertRaisesRegex(ValueError,'locks differ'):
            ledger(self.trace,self.rust)
