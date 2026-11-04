#!/usr/bin/env python3
"""Exercise unchanged production backup models with controlled host-only boundaries."""
import argparse,hashlib,json,os,re,subprocess,time
from pathlib import Path
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
MODEL='OathAtmosphere/Home/OathCloudBackupSection.swift'
MARKER='@MainActor @Observable final class OathCloudBackupModel {'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['source','scratch','output']:p.add_argument(n,type=Path)
 a=p.parse_args();source,scratch,out=[getattr(a,n).resolve() for n in ['source','scratch','output']]
 require_source_state(source,PIN)
 if scratch.exists() or out.exists():raise ValueError('Fresh scratch/output required')
 scratch.mkdir(parents=True);out.mkdir(parents=True);start=time.monotonic()
 env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
 raw=(source/MODEL).read_bytes();text=raw.decode();assert text.count(MARKER)==1
 extracted='import Foundation\nimport Observation\n'+MARKER+text.split(MARKER)[1]
 # Same-file extension exposes only a task handle for completion barriers. No production statement is changed.
 accessor='\nextension OathCloudBackupModel { var reviewTask: Task<Void, Never>? { work } }\n'
 def command(cmd,log,timeout=180):
  with log.open('wb') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  return r.returncode
 for cmd,name in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['python3','--version'],'python-version.log')]:
  assert command(cmd,out/name)==0
 rows=[]
 for stage in ['baseline','mutation']:
  work=scratch/stage;work.mkdir();dest=out/stage;dest.mkdir()
  body=extracted
  if stage=='mutation':
   guard='guard operationID == operation else { return }';assert body.count(guard)==1
   body=body.replace(guard,'// Deliberate test mutation: remove finish ownership guard.')
  compiled=body+accessor
  (work/'Model.swift').write_text(compiled);(dest/'Model.swift').write_text(compiled)
  fixture=ROOT/'fixtures/backup-settings/Checks.swift';binary=work/'checks'
  code=command(['xcrun','swiftc','-swift-version','6','-parse-as-library',str(fixture),str(work/'Model.swift'),'-o',str(binary)],dest/'build.log')
  if code:raise ValueError('Fixture build failed; retained log')
  code=command(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(binary)],dest/'run.log',30)
  log=(dest/'run.log').read_text();cases=re.findall(r'^(PASS|FAIL): (.+)$',log,re.M)
  expected=[]
  for op in ['create','disable','retry']:
   for outcome in ['success','failure']:
    for suffix in ['preserves newer progress','preserves newer task','preserves newer error state','new service entered once','current completion finishes','current completion succeeds']:
     fail=stage=='mutation' and suffix in ['preserves newer progress','preserves newer task']
     expected.append(('FAIL' if fail else 'PASS',f'stale {op} {outcome}: {suffix}'))
  for op in ['create','disable','retry']:
   for outcome in ['success','failure']:
    for suffix in ['reports current result','finishes task']:expected.append(('PASS',f'current {op} {outcome}: {suffix}'))
  expected += [('PASS',s) for s in ['duplicate: keeps original operation','duplicate: does not start second create','cancel: clears presentation immediately','cancel: late failure stays invisible']]
  fails=12 if stage=='mutation' else 0
  if cases!=expected or code!=int(fails>0) or log.splitlines().count(f'Backup settings checks: {52-fails} passed, {fails} failed')!=1:raise ValueError('Unexpected model result; original log retained')
  rows.append({'stage':stage,'source_commit':PIN,'production_path':MODEL,'production_sha256':sha(raw),'extracted_body_sha256':sha(extracted.encode()),'compiled_model_sha256':sha(compiled.encode()),'fixture_sha256':sha(fixture.read_bytes()),'executable_sha256':sha(binary.read_bytes()),'exit_code':code,'passed':52-fails,'failed':fails,'cases':[{'status':s.lower(),'name':n} for s,n in cases],'runtime_network':'denied','files':[{'path':str(f.relative_to(out)),'sha256':sha(f.read_bytes())} for f in sorted(dest.iterdir()) if f.is_file()]})
  print(stage,52-fails,'passed',fails,'failed',flush=True)
 code=command(['python3',str(source/'Tools/CheckBackupPresentation.py')],out/'all-wallet-model.log')
 log=(out/'all-wallet-model.log').read_text()
 if code or 'Backup presentation checks: 15 passed, 0 failed' not in log or len(re.findall(r'^PASS: ',log,re.M))!=15:raise ValueError('Existing all-wallet model failed')
 require_source_state(source,PIN)
 report={'source_commit':PIN,'driver_sha256':sha(Path(__file__).read_bytes()),'duration_seconds':round(time.monotonic()-start,3),'stages':rows,'all_wallet_model':{'passed':15,'failed':0,'exit_code':code,'production_sha256':sha((source/'OathAtmosphere/Home/OathAllWalletBackupPage.swift').read_bytes()),'tool_hashes':{n:sha((source/n).read_bytes()) for n in ['Tools/CheckBackupPresentation.py','Tools/CheckBackupPresentation.swift']},'log':'all-wallet-model.log','log_sha256':sha((out/'all-wallet-model.log').read_bytes())},'files':[{'path':f.name,'sha256':sha(f.read_bytes())} for f in sorted(out.iterdir()) if f.is_file()]}
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print('all-wallet-model 15 passed',flush=True)
if __name__=='__main__':main()
