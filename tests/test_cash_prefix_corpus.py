from pathlib import Path
import importlib.util
import sys
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))

def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class UTXOAuditEvidenceTests(unittest.TestCase):
    def test_compact_size_boundaries(self):
        compact=load('cash-token-prefixes').compact
        self.assertEqual([compact(n).hex() for n in (252,253,65535,65536,2**32-1,2**32)],
                         ['fc','fdfd00','fdffff','fe00000100','feffffffff','ff0000000001000000'])

    def test_partial_alias_result_is_rejected(self):
        checker=load('utxo-input-bytes');case=checker.CASES[0]
        text=f"Test Case '-[OathBitcoinTests.BitcoinSendOptionsTests {case}]' started.\n"
        text+='XCTAssertThrowsError failed: did not throw an error - litecoin\nExecuted 1 test, with 2 failures'
        with self.assertRaises(ValueError): checker.classify(case,True,1,text)

    def test_empty_or_unrelated_crash_cannot_reproduce_slice(self):
        checker=load('utxo-input-bytes')
        for text in ('','Unrelated test started.','Build failed'):
            with self.assertRaises(ValueError): checker.classify(checker.CASES[1],True,-5,text)

    def test_passing_control_requires_the_named_case(self):
        checker=load('utxo-input-bytes');case=checker.CASES[2]
        text=f"Test Case '-[OathBitcoinTests.BitcoinSendOptionsTests {case}]' started.\n"
        with self.assertRaises(ValueError): checker.classify(case,False,0,text+'Executed 1 test, with 0 failures')

class CompilerTraceCoverageTests(unittest.TestCase):
    def setUp(self):
        self.verifier=load('compiled-coverage')
        self.app={'source_commit':'pin','files':[{'path':'App.swift','sha256':'abc','status':'outstanding'}]}
        self.trace={'source_commit':'pin','check':'release-inputs','status':'passed','files':[{'path':'application/App.swift','sha256':'abc','targets':['App']}]}
        self.empty={'files':[]}

    def test_successful_build_preserves_outstanding_status(self):
        rows=self.verifier.join(self.trace,self.app,self.empty,self.empty)
        self.assertTrue(rows[0]['additional_review'])
        self.assertEqual(rows[0]['review_status'],'outstanding')

    def test_refuses_changed_bytes_or_source_identity(self):
        for field,value in [('sha256','wrong'),('path','package/unknown.swift')]:
            data=dict(self.trace,files=[dict(self.trace['files'][0],**{field:value})])
            with self.assertRaises(ValueError):
                self.verifier.join(data,self.app,self.empty,self.empty)
        with self.assertRaises(ValueError):
            self.verifier.join(dict(self.trace,source_commit='other'),self.app,self.empty,self.empty)

class FrameworkReferenceTests(unittest.TestCase):
    def test_original_binary_digest_comes_from_the_pinned_archive(self):
        import hashlib
        import plistlib
        import tempfile
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);pkg=root/'Packages/WalletCore';pkg.mkdir(parents=True)
            archive=root/'WalletCore.xcframework.zip'
            meta=plistlib.dumps({'AvailableLibraries':[{'SupportedPlatform':'ios','SupportedArchitectures':['arm64'],
                    'LibraryIdentifier':'ios-arm64','LibraryPath':'WalletCore.framework'}]})
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('WalletCore.xcframework/Info.plist',meta)
                z.writestr('WalletCore.xcframework/ios-arm64/WalletCore.framework/WalletCore',b'fixture')
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest=pkg/'Package.swift'
            manifest.write_text(f'.binaryTarget(name: "WalletCore", url: "https://example.invalid/archive", checksum: "{digest}")')
            verifier=load('release-frameworks')
            info,proof=verifier.archived_slice_metadata(root,'WalletCore',archive)
            self.assertEqual(info,meta)
            self.assertEqual(proof['device_sha256'],hashlib.sha256(b'fixture').hexdigest())
            manifest.write_text(manifest.read_text().replace(digest,'a'*64))
            with self.assertRaisesRegex(ValueError,'does not match'):
                verifier.archived_slice_metadata(root,'WalletCore',archive)
