#!/usr/bin/env python3
"""Compile complete scanner state production code and bounded negative controls; no camera."""
import argparse, hashlib, json, os, re, subprocess, time
from pathlib import Path
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
PATH='OathAtmosphere/Scanner/OathScannerCaptureState.swift'
MUTATIONS={
 'accept-without-phase':('guard phase == .scanning else { return false }','// test mutation: accept in any phase'),
 'deliver-after-cancel':('if stillPresented, let destination {','if let destination {'),
 'retain-payload':('        pending = nil\n        if stillPresented','        // test mutation: retain payload\n        if stillPresented'),
 'duplicate-claim':('guard active, !delivered else { return nil }','guard active else { return nil }'),
 'stale-generation':('generation &+= 1','// test mutation: do not invalidate generation')}
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['source','scratch','output']: p.add_argument(n,type=Path)
 a=p.parse_args(); source,scratch,out=[getattr(a,n).resolve() for n in ['source','scratch','output']]
 require_source_state(source,PIN)
 if scratch.exists() or out.exists(): raise ValueError('Fresh scratch/output required')
 scratch.mkdir(parents=True);out.mkdir(parents=True);start=time.monotonic()
 env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
 def command(cmd,log,timeout=120):
  with log.open('wb') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  return r.returncode
 for cmd,name in [(['xcodebuild','-version'],'xcode.log'),(['swift','--version'],'swift.log'),(['python3','--version'],'python.log')]:
  if command(cmd,out/name):raise ValueError('Toolchain discovery failed')
 raw=(source/PATH).read_bytes();fixture=ROOT/'fixtures/scanner-state/Checks.swift';rows=[]
 for stage in ['baseline',*MUTATIONS]:
  work=scratch/stage;work.mkdir();dest=out/stage;dest.mkdir();body=raw.decode()
  if stage in MUTATIONS:
   old,new=MUTATIONS[stage]
   if body.count(old)!=1:raise ValueError('Mutation anchor mismatch')
   body=body.replace(old,new)
  model=work/'State.swift';model.write_text(body);(dest/'State.swift').write_text(body);binary=work/'checks'
  if command(['xcrun','swiftc','-swift-version','6','-parse-as-library',str(fixture),str(model),'-o',str(binary)],dest/'build.log'):raise ValueError('Build failed; retained log')
  code=command(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(binary)],dest/'run.log')
  log=(dest/'run.log').read_text();cases=re.findall(r'^(PASS|FAIL): ([a-z-]+)(?:: (.*))?$',log,re.M)
  if [x[1] for x in cases]!=['exhaustive-handoff','payload-lifetime','concurrent-claims','generation-invalidation','idempotent-start']:raise ValueError('Missing result groups')
  expected_failures={
   'baseline':[], 'accept-without-phase':['exhaustive-handoff'],
   'deliver-after-cancel':['exhaustive-handoff','payload-lifetime'],
   'retain-payload':['exhaustive-handoff','payload-lifetime'],
   'duplicate-claim':['concurrent-claims','idempotent-start'],
   'stale-generation':['concurrent-claims','generation-invalidation']}
  if [x[1] for x in cases if x[0]=='FAIL']!=expected_failures[stage]:raise ValueError('Negative control failed outside expected groups')
  failed=sum(x[0]=='FAIL' for x in cases)
  if code!=int(failed>0) or (stage=='baseline' and failed) or (stage!='baseline' and not failed):raise ValueError('Unexpected result')
  rows.append({'stage':stage,'passed':5-failed,'failed':failed,'exit_code':code,'cases':[{'status':s.lower(),'name':n,'detail':d} for s,n,d in cases],'production_sha256':sha(raw),'compiled_sha256':sha(body.encode()),'fixture_sha256':sha(fixture.read_bytes()),'executable_sha256':sha(binary.read_bytes()),'runtime_network':'denied','files':[{'path':str(f.relative_to(out)),'sha256':sha(f.read_bytes())} for f in sorted(dest.iterdir())]})
  print(stage,5-failed,'passed',failed,'failed',flush=True)
 # Retest the independent pre-existing production handoff fixture without edits.
 binary=scratch/'existing-handoff';tool=source/'Tools/CheckScannerHandoff.swift'
 if command(['xcrun','swiftc','-swift-version','6','-parse-as-library',str(tool),str(source/PATH),'-o',str(binary)],out/'existing-build.log'):raise ValueError('Existing fixture build failed')
 code=command(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(binary)],out/'existing-run.log')
 match=re.search(r'^Passed (\d+) scanner handoff checks across all six result routes; no simulator/device used\.$',(out/'existing-run.log').read_text(),re.M)
 if code or not match:raise ValueError('Existing handoff fixture failed')
 require_source_state(source,PIN)
 r={'source_commit':PIN,'production_path':PATH,'production_sha256':sha(raw),'driver_sha256':sha(Path(__file__).read_bytes()),'duration_seconds':round(time.monotonic()-start,3),'stages':rows,'existing_handoff':{'checks':int(match[1]),'exit_code':code,'fixture_sha256':sha(tool.read_bytes()),'executable_sha256':sha(binary.read_bytes())},'files':[{'path':f.name,'sha256':sha(f.read_bytes())} for f in sorted(out.iterdir()) if f.is_file()]}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 print('existing-handoff',match[1],'passed',flush=True)
if __name__=='__main__':main()
