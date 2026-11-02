#!/usr/bin/env python3
"""Reproduce recovery classification failures and verify the same inputs after correction."""
import argparse
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import tarfile
import tempfile
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
BASE='f8ea1b460be251e70f9b07a820d373012a506cce'
MANUAL_BASE='f6f86f003e998dc112f85e1c7c8f56a72ee8c13b'
MANUAL=['paste-url','paste-json','paste-address']
FAILURES=['stale-electrum','stale-aezeed','qr-url','qr-json','qr-address','dual-choice']
PINS={'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'}
DENY=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)']
def sha(data):return hashlib.sha256(data).hexdigest()
def cp(source,destination):destination.write_bytes(source.read_bytes())
def fixture(source,work):
    gen=work/'generator';gen.mkdir();bridge=source/'Tools/AezeedBridge'
    for name in ('go.mod','go.sum'):cp(bridge/name,gen/name)
    cp(ROOT/'fixtures/recovery-routing/dual.go',gen/'main.go')
    env=dict(os.environ,GOTOOLCHAIN='local',GOWORK='off')
    assert 'go1.26.5' in subprocess.check_output(['go','version'],env=env,text=True)
    subprocess.run(['go','build','-mod=readonly','-o','oracle','.'],cwd=gen,env=env,check=True)
    subprocess.run(['go','mod','verify'],cwd=gen,env=env,check=True)
    dual=json.loads(subprocess.check_output([*DENY,gen/'oracle'],cwd=gen))
    triple=json.loads(subprocess.check_output([*DENY,gen/'oracle','all-formats'],cwd=gen))
    assert triple['iteration']==50579 and len({triple[k] for k in ('bip39_address','aezeed_address','electrum_address')})==3
    (work/'three.json').write_text(json.dumps(triple))
    wanted=json.loads((source/'Tools/Fixtures/RecoveryFormatOverlap.json').read_bytes())
    dictionary=(source/'OathApp/Resources/BIP39/bip39_english.txt').read_text().splitlines()
    assert [dictionary.index(w) for w in dual['words'].split()]==wanted['wordIndices'] and dual['iteration']==285
    assert [dual['aezeed_address'],dual['bip39_address']]==[wanted['bitcoinAezeed'],wanted['bitcoinBIP39']] and dual['aezeed_address']!=dual['bip39_address']
    prefix=lambda s:hmac.digest(b'Seed version',s.lower().encode(),'sha512').hex().startswith('01')
    b58=runpy.run_path(str(ROOT/'scripts/utxo-recovery-vectors.py'))['b58']
    payloads={}
    for k,make in [('url',lambda i:'https://example.invalid/recovery-check/'+str(i)),('json',lambda i:json.dumps({'example':i},separators=(',',':'))),('address',lambda i:b58(bytes(1)+hashlib.sha256(b'oath-qr-public-example'+i.to_bytes(4,'big')).digest()[:20]))]:
        payloads[k]=next(make(i) for i in range(50000) if prefix(make(i)))
    electrum=json.loads((source/'Packages/OathBitcoin/Tests/OathBitcoinTests/Fixtures/electrum-reference.json').read_bytes())
    aezeed=json.loads((source/'Packages/OathAezeed/Tests/OathAezeedTests/Fixtures/lnd-production.json').read_bytes())
    payloads.update(dual=dual['words'],bip39=' '.join(['abandon']*11+['about']),electrum=next(x['phrase'] for x in electrum if x['kind']=='segwit' and not x['password']),aezeed=aezeed[0]['phrase'])
    f=work/'synthetic.json';f.write_text(json.dumps(payloads,sort_keys=True));return f,wanted

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--expected-commit');p.add_argument('--scratch',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();src=a.source.resolve();cfg=json.loads((ROOT/'scope/source.json').read_bytes());pin=require_source_state(src,a.expected_commit or cfg['reviewed_commit'])
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);records=[];scratch=a.scratch.resolve()
    with tempfile.TemporaryDirectory(prefix='oath-import-tests-') as t:
        w=Path(t);f,expected=fixture(src,w);fixture_hash=sha(f.read_bytes())
        for phase,revision in [('before',BASE),('manual-before',MANUAL_BASE),('after',pin)]:
            dest=w/phase;dest.mkdir()
            names=['Packages/'+x for x in ['OathBitcoin','OathAezeed','OathDiagnostics','OathSecp256k1']]+['OathAtmosphere/Import/OathMnemonicValidator.swift','OathAtmosphere/Import/OathRecoveryPhraseDraft.swift','Tools/CheckRecoveryImportRouting.swift','Tools/CheckMnemonicImport.swift','OathApp/Resources/BIP39','Tools/Fixtures/BIP39Vectors.json','Tools/Fixtures/BIP39AdditionalVectors.json']
            blob=subprocess.check_output(['git','-C',src,'archive',revision,*names])
            with tarfile.open(fileobj=io.BytesIO(blob)) as tar:tar.extractall(dest,filter='data')
            target=dest/'Sources/MnemonicAudit';target.mkdir(parents=True)
            for name in ('OathMnemonicValidator.swift','OathRecoveryPhraseDraft.swift'):cp(dest/'OathAtmosphere/Import'/name,target/name)
            runner=dest/'Tools/CheckRecoveryImportRouting.swift'
            original_probe=subprocess.check_output(['git','-C',src,'show',BASE+':Tools/CheckRecoveryImportRouting.swift'])
            manual_probe=subprocess.check_output(['git','-C',src,'show',MANUAL_BASE+':Tools/CheckRecoveryImportRouting.swift'])
            if runner.read_bytes()!=(original_probe if phase=='before' else manual_probe):
                raise ValueError('Case runner changed beyond the two pinned probe revisions')
            (target/runner.name).write_bytes(manual_probe if phase=='manual-before' else original_probe)
            cp(dest/'Packages/OathBitcoin/Package.resolved',dest/'Package.resolved')
            (dest/'Package.swift').write_text('// swift-tools-version: 6.1\nimport PackageDescription\nlet package = Package(name:"MnemonicAudit",platforms:[.macOS("15.5")],dependencies:[.package(path:"Packages/OathBitcoin"),.package(path:"Packages/OathAezeed")],targets:[.executableTarget(name:"MnemonicAudit",dependencies:["OathBitcoin","OathAezeed"])])\n')
            cmd=['swift','build','--package-path',str(dest),'--scratch-path',str(scratch/phase),'--build-system','native','--force-resolved-versions']
            def build(log):
                with (out/log).open('w') as fp:subprocess.run(cmd+['--product','MnemonicAudit','--jobs','4'],stdout=fp,stderr=subprocess.STDOUT,check=True,timeout=600)
            build(phase+'-build.log')
            for name,r in PINS.items():assert subprocess.check_output(['git','-C',scratch/phase/'checkouts'/name,'rev-parse','HEAD'],text=True).strip()==r
            binary=Path(subprocess.check_output(cmd+['--show-bin-path'],text=True).strip())/'MnemonicAudit'
            def execute(cases,expected_failures):
                for case in cases:
                    result=subprocess.run([*DENY,binary,dest/'OathApp/Resources/BIP39',f,case],cwd=dest,capture_output=True,text=True,timeout=40)
                    failed=case in expected_failures
                    if result.returncode!=(1 if failed else 0) or result.stdout.strip()!=case+(' failed' if failed else ' passed'):
                        raise ValueError('Unexpected process outcome: '+phase+' '+case)
                    # Retain only reviewed fixed test output. Stderr must have no unexpected diagnostics or input material.
                    if result.stderr.strip():raise ValueError('Unexpected stderr: '+phase+' '+case)
                    records.append(dict(phase=phase,case=case,source_commit=revision,status='reproduced' if failed else 'passed',exit_code=result.returncode))
            if phase=='manual-before':
                execute(MANUAL+['legacy-hex'],MANUAL)
            else:
                execute(FAILURES+['recognized-formats'],FAILURES if phase=='before' else [])
            if phase=='after':
                (target/runner.name).write_bytes(manual_probe);build('manual-repaired-build.log')
                execute(MANUAL+['legacy-hex'],[])
                (target/runner.name).unlink();cp(dest/'Tools/CheckMnemonicImport.swift',target/'CheckMnemonicImport.swift')
                build('existing-suite-build.log')
                result=subprocess.run([*DENY,binary,dest/'OathApp/Resources/BIP39'],cwd=dest,capture_output=True,text=True,check=True,timeout=120)
                assert result.stdout.strip()=='Passed 1667 host mnemonic/import checks across 260 independent vectors, 10 word lists, and all 5 supported lengths.' and not result.stderr.strip()
                (target/'CheckMnemonicImport.swift').unlink();cp(ROOT/'fixtures/recovery-routing/ThreeFormats.swift',target/'ThreeFormats.swift')
                build('three-format-build.log')
                triple=subprocess.run([*DENY,binary,dest/'OathApp/Resources/BIP39',w/'three.json'],cwd=dest,capture_output=True,text=True,check=True,timeout=40)
                assert triple.stdout.strip()=='All three format routes, two native derivations, composition and reset passed' and not triple.stderr.strip()
    result=dict(check='recovery-routing',source_commit=pin,baseline_commit=BASE,status='passed',executions=records,existing_suite_checks=1667,existing_suite_vectors=260,
        three_format_routes_verified=True,three_format_native_addresses_verified=2,manual_probe_baseline=MANUAL_BASE,case_runner_sha256=sha(original_probe),manual_probe_sha256=sha(manual_probe),input_set_sha256=fixture_hash,expected_receive_addresses={k:v for k,v in expected.items() if k!='wordIndices'},
        scope='Shared unmodified import/draft code on both revisions. Each case executed with network denied. The independent LND fixture is valid under both aezeed and BIP39. This run checks import routing, separate from the encrypted vault integration and camera UI.')
    require_source_state(src,pin);log=out/'recovery-routing.log';log.write_text(json.dumps(result,indent=2)+'\n');result.update(log=log.name,log_sha256=sha(log.read_bytes()));(out/'recovery-routing.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Nine reproduced, eleven after-cases passed, 1667 existing checks passed')
if __name__=='__main__':main()
