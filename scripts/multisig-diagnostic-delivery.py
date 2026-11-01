#!/usr/bin/env python3
"""Delay only the fixture consumer; execute the shipped test assertions with a real outbox."""
import argparse,hashlib,io,json,os,re,subprocess,tarfile,tempfile,time
from pathlib import Path
from bounded_process import logged_command
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
BASE='5fce630e522fa25dae81658bdeaa6737897dc1b2'
SUITES=['Bitcoin','BitcoinCash','Dogecoin','Litecoin']
CASE='testSigningFailureReportsOnlySafeCodeAndOperationContext'
def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--expected-commit');p.add_argument('--output',type=Path,required=True);p.add_argument('--scratch',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();pin=require_source_state(source,a.expected_commit or json.loads((ROOT/'scope/source.json').read_bytes())['reviewed_commit'])
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);rows=[];start=time.monotonic();setup=[]
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','SDKROOT','DEVELOPER_DIR','TMPDIR','LANG','LC_ALL','CI')}
    for phase,rev in [('before',BASE),('after',pin)]:
        tree=subprocess.check_output(['git','-C',source,'archive',rev,'Packages/OathBitcoin','Packages/OathDiagnostics','Packages/OathSecp256k1'])
        with tempfile.TemporaryDirectory(prefix='oath-utxo-delivery-') as t:
            with tarfile.open(fileobj=io.BytesIO(tree)) as archive:archive.extractall(t,filter='data')
            pkg=Path(t)/'Packages/OathBitcoin';d=pkg/'Tests/OathBitcoinTests'
            files=[d/(s+'MultisigDiagnosticsTests.swift') for s in SUITES] if phase=='before' else [d/'MultisigSigningDiagnosticCapture.swift']
            for f in files:
                text=f.read_text();needle='func upload(_ events: [DiagnosticEvent]) async throws {'
                assert text.count(needle)==1
                amended=text.replace(needle,needle+'\n        try await Task.sleep(for: .seconds(2))\n        ')
                f.write_text(amended);setup.append(dict(phase=phase,path=f.name,original_sha256=hashlib.sha256(text.encode()).hexdigest(),instrumented_sha256=hashlib.sha256(amended.encode()).hexdigest()))
            prefix=['swift','build','--package-path',str(pkg),'--build-system','native','--scratch-path',str(a.scratch.resolve()/phase),'--force-resolved-versions']
            with (out/(phase+'-build.log')).open('w') as stream:
                code,timed=logged_command(prefix+['--build-tests','--jobs','4'],stream=stream,env=env,timeout=600)
            if code or timed:raise ValueError('Fixture build failed: '+phase)
            for pkgname,required in {'bdk-swift':'55284dc4e767c301c7926c412daad241c0667106','swift-secp256k1':'e70a10e036a55fffea31568f0af92d69b6d449cd'}.items():
                assert subprocess.check_output(['git','-C',a.scratch.resolve()/phase/'checkouts'/pkgname,'rev-parse','HEAD'],text=True).strip()==required
            binary=Path(subprocess.check_output(prefix+['--show-bin-path'],env=env,text=True).strip());bundle,=list(binary.glob('*.xctest'))
            for s in SUITES:
                suite='OathBitcoinTests.'+s+'MultisigDiagnosticsTests';name=f'-[{suite} {CASE}]';f=out/(phase+'-'+s+'.log')
                with f.open('w') as stream:
                    code,timed=logged_command(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',suite+'/'+CASE,str(bundle)],stream=stream,env=env,timeout=35)
                raw=f.read_text();errors=[l.split(': error: ',1)[-1] for l in raw.splitlines() if ': error:' in l];events=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",raw,re.M)
                wanted='failed' if phase=='before' else 'passed'
                ok=not timed and events==[(name,'started'),(name,wanted)] and (code==0 and not errors if phase=='after' else code==1 and errors==[name+' : XCTUnwrap failed: expected non-nil value of type "DiagnosticEvent"'])
                rows.append(dict(phase=phase,source_commit=rev,suite=suite,case=CASE,exit_code=code,expected_outcome_observed=ok,timed_out=timed,log=f.name,log_sha256=hashlib.sha256(f.read_bytes()).hexdigest()));print(phase,s,ok,flush=True)
    ok=len(rows)==8 and all(r['expected_outcome_observed'] for r in rows)
    result=dict(check='multisig-diagnostic-delivery',status='passed' if ok else 'failed',source_commit=pin,baseline_commit=BASE,executions=rows,instrumentation=setup,duration_seconds=round(time.monotonic()-start,2),scope='Only each test transport receives the two-second delay; each production library and actual test assertion is unchanged. Network denied during all eight XCTest executions.')
    f=out/'multisig-diagnostic-delivery.log';f.write_text(json.dumps(result,indent=2)+'\n');result.update(log=f.name,log_sha256=hashlib.sha256(f.read_bytes()).hexdigest());(out/'multisig-diagnostic-delivery.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
