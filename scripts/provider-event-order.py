#!/usr/bin/env python3
"""Control arrival order in the test consumer, leaving the app, transport calls, filters and assertions intact."""
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
BASE='a13a88cb67fe9fa73c1a0bbb222a474b195e25eb'
REPAIR='5f92dc2a87334c0b4942dea1f6a47ad92770f4a3'
CASES=['OathAnkrTests.TokenDiscoveryArtworkTests/testArtworkDiagnosticsPreserveFailureAndCorrelationWithoutBodyOrContract','OathAnkrTests.TonReadRecoveryDiagnosticsTests/testOriginalTLSAndRecoveryReportsRemainPrivacyFiltered']
INJECT='''func upload(_ batch: [DiagnosticEvent]) async throws {
        let held = batch.filter { $0.context["http_status"] == "401" || ($0.operation == "ton_read" && $0.context["attempt"] == "1") }
        let heldIDs = Set(held.map(\\.id))
        try await deliver(batch.filter { !heldIDs.contains($0.id) })
        if !held.isEmpty {
            Task {
                try await Task.sleep(for: .milliseconds(2500))
                try await self.deliver(held)
            }
        }
    }
    private '''
def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--scratch',type=Path,required=True);a=ap.parse_args()
    src=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    for rev in (BASE,REPAIR):subprocess.run(['git','-C',src,'cat-file','-e',rev+'^{commit}'],check=True)
    runs=[];edits=[];env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','SDKROOT','DEVELOPER_DIR','LANG','LC_ALL','CI')}
    for rel,rev in [('before',BASE),('after',REPAIR)]:
        with tempfile.TemporaryDirectory(prefix='oath-reordered-events-') as t:
            work=Path(t)/'app';subprocess.run(['git','clone','--quiet','--local','--no-checkout',src,work],check=True)
            subprocess.run(['git','-C',work,'checkout','-q','--detach',rev],check=True);require_source_state(work,rev)
            tests=work/'Packages/OathAnkr/Tests/OathAnkrTests'
            for filename,actor in ([('TokenDiscoveryArtworkTests.swift','ArtworkDiagnosticsCapture'),('TonReadRecoveryTests.swift','TonReadReports')] if rel=='before' else [('CorrelatedDiagnosticTestCapture.swift','CorrelatedDiagnosticTestCapture')]):
                f=tests/filename;s=f.read_text();start=s.index('actor '+actor+': DiagnosticTransport');i=s.index('func upload(',start)
                patched=s[:i]+INJECT+s[i:].replace('func upload(', 'func deliver(',1);f.write_text(patched)
                edits.append(dict(phase=rel,path=filename,source_sha256=hashlib.sha256(s.encode()).hexdigest(),instrumented_sha256=hashlib.sha256(patched.encode()).hexdigest()))
            pkg=work/'Packages/OathAnkr';scratch=a.scratch.resolve()/rel;prefix=['swift','build','--package-path',str(pkg),'--build-system','native','--scratch-path',str(scratch),'--force-resolved-versions']
            with (out/(rel+'-build.log')).open('w') as stream:subprocess.run(prefix+['--build-tests','--jobs','4'],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=900,check=True)
            bundles=list(Path(subprocess.check_output(prefix+['--show-bin-path'],env=env,text=True).strip()).glob('*.xctest'));assert len(bundles)==1
            for select in CASES:
                name='-['+select.replace('/',' ')+']';f=out/(rel+'-'+select.split('/')[1]+'.log')
                with f.open('w') as stream:p=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',select,bundles[0]],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=40)
                raw=f.read_text();errs=[x.split(': error: ',1)[-1] for x in raw.splitlines() if ': error:' in x];events=re.findall(r"^Test Case '([^']+)' (started|passed|failed|skipped)",raw,re.M)
                ok=(p.returncode==1 and errs==[name+' : XCTAssertTrue failed'] and events==[(name,'started'),(name,'failed')]) if rel=='before' else (p.returncode==0 and not errs and events==[(name,'started'),(name,'passed')])
                runs.append(dict(phase=rel,source_commit=rev,case=select,expected_outcome_observed=ok,exit_code=p.returncode,log=f.name,log_sha256=hashlib.sha256(f.read_bytes()).hexdigest()));print(rel,select,ok,flush=True)
    status='passed' if len(runs)==4 and all(x['expected_outcome_observed'] for x in runs) else 'failed'
    r=dict(check='provider-event-order',source_commit=REPAIR,status=status,baseline_commit=BASE,executions=runs,fixture_edits=edits,scope='Delay only the secondary HTTP 401 / TON boundary event at the isolated synthetic consumer. The original assertions and all production files are unmodified. Two offline cases per revision.')
    log=out/'provider-event-order.log';log.write_text(json.dumps(r,indent=2)+'\n');r.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());(out/'provider-event-order.json').write_text(json.dumps(r,indent=2)+'\n')
    return int(status!='passed')
if __name__=='__main__':raise SystemExit(main())
