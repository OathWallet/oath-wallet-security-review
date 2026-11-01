import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from advisory_gate import evaluate

class AdvisoryGateTests(unittest.TestCase):
    def setUp(self):
        self.inventory={'source_commit':'commit','go_mod_sha256':'mod','go_sum_sha256':'sum','module_graph':{'example':'v1'},
                        'targets':[{'target':t,'packages':[{'import_path':'example/used'}]} for t in ['mac','ios','sim']]}
        self.advisory={'id':'GO-TEST','affected':[{'package':{'name':'example'},'ecosystem_specific':{'imports':[{'path':'example/unused'}]}}]}
        self.scan={'results':[{'packages':[{'package':{'name':'example','version':'1'},'vulnerabilities':[self.advisory]}]}]}
    def run_gate(self,scan=None,inventory=None,exit_code=1):
        return evaluate(self.scan if scan is None else scan,self.inventory if inventory is None else inventory,exit_code,'commit','mod','sum')
    def test_preserves_raw_failure_with_exact_uncompiled_disposition(self):
        r=self.run_gate();self.assertEqual(r['gate_status'],'passed');self.assertEqual(r['raw_scanner_exit_code'],1)
        self.assertEqual(r['raw_advisory_occurrences'],1);self.assertEqual(r['advisories'][0]['id'],'GO-TEST');self.assertFalse(r['binary_clearance'])
    def test_compiled_advisory_blocks(self):
        self.inventory['targets'][2]['packages'].append({'import_path':'example/unused'})
        self.assertEqual(self.run_gate()['gate_status'],'failed')
    def test_unknown_metadata_blocks(self):
        self.advisory['affected']=[];self.assertEqual(self.run_gate()['gate_status'],'failed')
    def test_execution_error_is_not_vulnerability_exit(self):
        for status in [2,124,-9]:
            with self.assertRaises(ValueError):self.run_gate(exit_code=status)
    def test_report_and_exit_disagreement_rejected(self):
        with self.assertRaises(ValueError):self.run_gate(exit_code=0)
        with self.assertRaises(ValueError):self.run_gate(scan={'results':[]})
    def test_absent_or_malformed_report_rejected(self):
        for report in [{},{'results':None},{'results':[{}]},{'results':[{'packages':[{}]}]}]:
            with self.assertRaises(ValueError):self.run_gate(scan=report)
    def test_wrong_commit_rejected(self):
        self.inventory['source_commit']='other'
        with self.assertRaises(ValueError):self.run_gate()
    def test_changed_dependency_locks_rejected(self):
        for key in ['go_mod_sha256','go_sum_sha256']:
            inventory=copy.deepcopy(self.inventory);inventory[key]='changed'
            with self.assertRaises(ValueError):self.run_gate(inventory=inventory)
    def test_clean_report_still_requires_all_targets(self):
        result=self.run_gate(scan={'results':[]},exit_code=0);self.assertEqual(result['gate_status'],'passed')
        self.inventory['targets'].pop()
        with self.assertRaises(ValueError):self.run_gate(scan={'results':[]},exit_code=0)
    def test_changed_module_version_rejected(self):
        self.inventory['module_graph']['example']='v2'
        with self.assertRaises(ValueError):self.run_gate()

if __name__=='__main__':unittest.main()
