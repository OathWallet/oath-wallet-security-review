#!/usr/bin/env python3
"""Reproduce private version/key-data mismatches and check authenticated recovery."""
import re
import sys
from package_corpus import run

BASE='7a737d938422d2a6d50ae3143bbca27bd95a87c2'
NETWORKS=['Bitcoin','BitcoinCash','Dogecoin','Litecoin']
REJECTION={f'test{network}RejectsPublicPointInPrivateEnvelope':'Public point accepted as private key material' for network in NETWORKS}
REJECTION['testAlternatePrivateVersionsRejectMalformedMarker']='Alternate private version accepted a nonzero marker'
CONTROLS=['testCanonicalPrivateEnvelopesRetainOriginalScalar','testPublicVersionCannotBeImportedAsPrivate']
RECOVERY=['testRecoveryRestoresEachOriginalScript','testRecoveryRefusesMismatchedStoredScalar','testRecoveryRefusesPublicAndWrongNetworkVersions']

def verdict(suite,case,text,code,before):
    name=f'-[{suite} {case}]'
    events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
    errors=[s.split(': error: ',1)[-1] for s in text.splitlines() if ': error:' in s]
    if before and case in REJECTION:
        return 'reproduced' if code==1 and events==[(name,'started'),(name,'failed')] and errors==[name+' : failed - '+REJECTION[case]] else 'failed'
    return 'passed' if code==0 and not errors and events==[(name,'started'),(name,'passed')] else 'failed'

if __name__=='__main__':
    if len(sys.argv)<2 or sys.argv[1] not in ('import','recovery'):raise SystemExit('Choose import or recovery')
    recovery=sys.argv.pop(1)=='recovery';suite='OathBitcoinTests.'+('StoredExtendedKeyRecoveryTests' if recovery else 'ExtendedKeyWireTests')
    raise SystemExit(run(check='utxo-key-'+('recovery' if recovery else 'import'),base=BASE if not recovery else '5fce630e522fa25dae81658bdeaa6737897dc1b2',
        suite=suite,cases=RECOVERY if recovery else list(REJECTION)+CONTROLS,outcome=lambda text,code,case,before:verdict(suite,case,text,code,before),
        compare=not recovery,package='OathBitcoin',local_dependencies=('OathDiagnostics','OathSecp256k1'),
        pins={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'},
        scope='Synthetic public point and chain codes. Each fixture runs in a network-denied XCTest process. The four-network recovery control compares derived scripts and leaf exports with independent BIP44 vectors.'))
