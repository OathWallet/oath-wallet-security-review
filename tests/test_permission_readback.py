import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('permission_readback',Path(__file__).resolve().parents[1]/'scripts/permission-readback.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PermissionReadbackClassificationTests(unittest.TestCase):
    def transcript(self,result='passed',failure=''):
        name=f'-[OathDatabaseTests.PermissionReadbackIdempotencyTests {m.CASES[0]}]'
        return f"Test Case '{name}' started.\n{failure}\nTest Case '{name}' {result} (0.02 seconds).\n"
    def testRequiresOneRealMatchingTestAndNoUnrelatedErrors(self):
        text=self.transcript();self.assertEqual(m.outcome(text,0,m.CASES[0]),'passed')
        for bad in ['',text+text,text.replace(m.CASES[0],m.CASES[2]),self.transcript('skipped'),self.transcript(failure='file:1: error: unrelated')]:self.assertEqual(m.outcome(bad,0,m.CASES[0]),'failed')
        self.assertEqual(m.outcome(text,1,m.CASES[0]),'failed')
    def testRequiresExactContradictionAssertionInsteadOfAnyFailure(self):
        line='file.swift:56: error: test : XCTAssertEqual failed: (Optional("removed")) is not equal to (Optional("active")) - Duplicate readback must preserve the verified batch result'
        text=self.transcript('failed',line);self.assertEqual(m.outcome(text,1,m.CASES[0]),'contradiction-reproduced')
        for bad in [text.replace('XCTAssertEqual failed','unexpected throw'),text.replace('Duplicate readback','Different check'),text+'\nfile:2: error: unrelated',text.replace('active','pending')]:self.assertEqual(m.outcome(bad,1,m.CASES[0]),'failed')
        self.assertEqual(m.outcome(text,0,m.CASES[0]),'failed')
