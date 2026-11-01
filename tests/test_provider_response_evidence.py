import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS/(name+'.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

boundary = module('provider-response-budget')
index = module('transport-inputs')

class ResponseEvidenceTests(unittest.TestCase):
    def test_only_accept_expected_failure_once(self):
        name = '-[Suite attack]'
        start = f"Test Case '{name}' started.\n"
        end = f"Test Case '{name}' failed (0.1 seconds).\n"
        error = f"Fixture.swift:5: error: {name} : failed - exceeded limit\n"
        check = lambda text: boundary.verdict('Suite', {'attack':'exceeded limit'}, text, 1, 'attack', True)
        self.assertEqual(check(start+error+end),'reproduced')
        for wrong in (start+error+error+end,start+end,start+error.replace('exceeded limit','other')+end,error+end):
            self.assertEqual(check(wrong),'failed')

    def test_empty_or_skipped_cannot_be_passing_control(self):
        case='-[S control]'
        for raw in ('',f"Test Case '{case}' started.\nTest Case '{case}' skipped"):
            self.assertEqual(boundary.verdict('S',{'control':None},raw,0,'control',False),'failed')

    def test_multiline_wrapper_and_socket_are_candidates(self):
        result=index.matches('let b = try await session.bytes(\n for: req)\nlet fd = socket(2,0,0)')
        self.assertEqual(result,[{'line':1,'kind':'urlsession-task-or-stream'},{'line':3,'kind':'socket-api'}])

class ReleaseFrameworkTests(unittest.TestCase):
    def test_sections_point_to_file_bytes(self):
        import hashlib,struct,tempfile
        framework=module('release-frameworks')
        header=struct.pack('<IiiIIIII',0xfeedfacf,0x0100000c,0,6,2,176,0,0)
        uuid=struct.pack('<II16s',0x1b,24,bytes(range(16)))
        seg=bytearray(152);struct.pack_into('<II',seg,0,0x19,152);struct.pack_into('<I',seg,64,1)
        struct.pack_into('<16s16sQQI',seg,72,b'__text',b'__TEXT',0,4,208)
        struct.pack_into('<I',seg,136,0x80000000)
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/'test'
            file.write_bytes(header+uuid+seg+b'abcd')
            self.assertEqual(framework.inspect(file)['executable_sections']['__TEXT.__text'],{'bytes':4,'sha256':hashlib.sha256(b'abcd').hexdigest()})
            file.write_bytes(header+uuid+seg+b'abc')
            with self.assertRaisesRegex(ValueError,'Invalid executable section'):framework.inspect(file)

    def test_rejects_another_architecture(self):
        import struct,tempfile
        framework=module('release-frameworks')
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/'test';file.write_bytes(struct.pack('<IiiIIIII',0xfeedfacf,0x01000007,0,6,0,0,0,0))
            with self.assertRaisesRegex(ValueError,'arm64'):framework.inspect(file)
