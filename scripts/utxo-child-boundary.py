#!/usr/bin/env python3
"""Replay the final normal child at four wallet interfaces, with identical test inputs."""
import re
from package_corpus import run

CASES = {
    'testFinalNormalChildMatchesIndependentBIP44ScriptsAndExports': 'BitcoinKeysTests',
    'testFinalNormalChildStillRejectsHardenedAndFixedKeys': 'BitcoinKeysTests',
    'testFinalNormalChildSignsInputAndChange': 'BitcoinSendTests',
    'testFinalNormalChildElectrumLeafExport': 'ElectrumMnemonicTests',
    'testFinalNormalChildMultisigInputAndChange': 'BitcoinMultisigTests',
}
SUITES = {key: 'OathBitcoinTests.'+name for key,name in CASES.items()}

def verdict(text, code, case, before):
    name = f'-[{SUITES[case]} {case}]'
    events = re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)", text, re.M)
    errors = [line.split(': error: ',1)[1] for line in text.splitlines() if ': error: ' in line]
    if before and case != 'testFinalNormalChildStillRejectsHardenedAndFixedKeys':
        expected = [name+' : failed: caught error: "invalidAddress"']
        if CASES[case] in ('ElectrumMnemonicTests','BitcoinKeysTests'):
            expected.insert(0,name+' : XCTUnwrap failed: threw error "invalidAddress"')
        return 'reproduced' if code==1 and events==[(name,'started'),(name,'failed')] and errors==expected else 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    raise SystemExit(run(check='utxo-child-boundary',base='3c657667fb7091b9162a8d808f51e0c450bf1dc7',suite=None,
        cases=CASES,case_suites=SUITES,outcome=verdict,package='OathBitcoin',local_dependencies=('OathDiagnostics','OathSecp256k1'),
        pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
        scope='Explicit final normal child, finite fixed-key and hardened controls, single-key and multisig signing, Electrum leaf export, independent four-chain P2PKH scripts. One synthetic transaction at a time, network denied. Gap discovery policy is separate.'))
