import importlib.util
import sys
import unittest
from pathlib import Path

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
def load(name):
    spec=importlib.util.spec_from_file_location(name,scripts/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
proof=load('bitcoin-connect-signature')
core=load('bitcoin-connect-core-proof')
from bitcoin_core_regtest import classify

class SignatureEvidenceTests(unittest.TestCase):
    def test_admission_reproduction_requires_the_expected_failure(self):
        case=proof.PEER[0];name=f'-[{proof.SUITE} {case}]'
        t=f"Test Case '{name}' started.\nf: error: {name} : XCTAssertFalse failed - Foreign signature was returned for a different transaction\nTest Case '{name}' failed (0.02 seconds)."
        self.assertEqual(proof.outcome(t,1,case,True),'expected-signature-failure')
        for bad in [t.replace('Foreign','unrelated'),t+'\nf: error: extra',t.replace('started','skipped')]:
            self.assertEqual(proof.outcome(bad,1,case,True),'failed')
        self.assertEqual(proof.outcome(t,1,case,False),'failed')

    def test_regtest_selection_requires_single_real_pass(self):
        suite,case='Example','testOne';name=f'-[OathBitcoinTests.{suite} {case}]'
        t=f"Test Case '{name}' started.\nTest Case '{name}' passed (0.1 seconds)."
        self.assertTrue(classify(t,0,suite,case))
        for text in ['',t+'\n'+t,t.replace('passed','skipped'),t+'\nf: error: injected']:
            self.assertFalse(classify(text,0,suite,case))

    def test_chain_confirmation_requires_all_four_and_no_public_peers(self):
        row=dict(status='passed',blocks=109,peers=0,network_active=False,chain='regtest')
        text='\n'.join('Bitcoin Core accepted and mined WalletConnect '+t for t in ['84','86','44','49'])
        self.assertTrue(core.accepted(row,text,False))
        for bad in [{**row,'blocks':108},{**row,'peers':1},{**row,'network_active':True},{**row,'chain':'main'}]:
            self.assertFalse(core.accepted(bad,text,False))
        self.assertFalse(core.accepted(row,text.replace('86','84'),False))

    def test_core_baseline_needs_both_specific_node_rejections_and_controls(self):
        name=f'-[OathBitcoinTests.{core.SUITE} {core.CASE}]'
        row=dict(blocks=107,network_active=False,peers=0,chain='regtest',exit_code=1)
        lines=[
            f"Test Case '{name}' started.",
            f"f: error: {name} : failed - Bitcoin Core rejected wallet signatures for 84,86",
            f"Test Case '{name}' failed (2 seconds).",
            'Rejected by Core: 86, mempool-script-verify-flag-failed (Invalid Schnorr signature)',
            'Rejected by Core: 84, mempool-script-verify-flag-failed (Signature must be zero for failed CHECK(MULTI)SIG operation)',
            'Bitcoin Core accepted and mined WalletConnect 49','Bitcoin Core accepted and mined WalletConnect 44',
        ]
        text='\n'.join(lines)
        self.assertTrue(core.accepted(row,text,True))
        for bad in [text.replace('Invalid Schnorr signature','unavailable'),text.replace('49','44'),text+'\nf: error: unexpected']:
            self.assertFalse(core.accepted(row,bad,True))
