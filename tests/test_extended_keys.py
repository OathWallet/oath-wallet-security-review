from pathlib import Path
import importlib.util,sys,struct,unittest
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'));mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod);return mod
class ExtendedKeyEvidenceTests(unittest.TestCase):
    def test_preexisting_failure_requires_exact_substitution_assertion(self):
        module=load('extended-key-import');suite='OathBitcoinTests.ExtendedKeyWireTests';case=module.NETWORKS[0]
        case='test'+case+'RejectsPublicPointInPrivateEnvelope';name=f'-[{suite} {case}]'
        event=f"Test Case '{name}' started.\n";error=f"file:20: error: {name} : failed - {module.REJECTION[case]}\n";end=f"Test Case '{name}' failed (0.1 seconds)."
        self.assertEqual(module.verdict(suite,case,event+error+end,1,True),'reproduced')
        for raw in (event+end,event+error+error+end,(event+error+end).replace('Public point','Other data')):
            self.assertEqual(module.verdict(suite,case,raw,1,True),'failed')
    def test_build_version_is_read_from_command(self):
        mod=load('bdk-object-versions')
        mach=struct.pack('<IiiIIIII',0xfeedfacf,0x100000c,0,1,1,24,0,0)
        cmd=struct.pack('<IIIIII',0x32,24,2,15<<16,18<<16|5<<8,0)
        self.assertEqual(mod.metadata(mach+cmd),((2,'15.0.0','18.5.0'),))
        with self.assertRaises(ValueError):mod.metadata(mach+cmd[:12])

class LinkBoundaryTests(unittest.TestCase):
    def test_export_parser_preserves_full_name_and_rejects_ambiguous_line(self):
        mod=load('bdk-linked-exports')
        self.assertEqual(mod.marked_names([' 0x000ABCD0  _ffi_bdkffi_rust_future_cancel_f32\n','  0x00  _other\n']),{'_ffi_bdkffi_rust_future_cancel_f32'})
        with self.assertRaises(ValueError):mod.marked_names(['bad prefix _uniffi_bdkffi_example'])

    def test_vector_fixture_rejects_unpinned_source(self):
        with self.assertRaisesRegex(ValueError,'Unexpected published BIP32 document'):load('bip32-import-vectors').fixture(b'invalid document')
