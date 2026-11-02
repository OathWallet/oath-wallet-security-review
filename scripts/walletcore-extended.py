#!/usr/bin/env python3
"""Retest an extended-key repair using full production HDWallet translation units.

Requires the documented native Core build with one of the two pinned repair sets.
This runner compiles both before/after translation units with identical flags;
all other code comes from those complete, locally built Core static libraries.
"""
import argparse,hashlib,json,os,shlex,subprocess,tempfile,time
from pathlib import Path
from bounded_process import logged_command
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
PIN='d40d24a63d92619167903369308bf0e2f7eb3a59'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('source',type=Path,help='Clean pinned upstream checkout')
 p.add_argument('prepared',type=Path,help='Native build checkout with the selected repair set')
 p.add_argument('--app-source',type=Path,required=True);p.add_argument('--app-commit',required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--boost',type=Path,required=True)
 p.add_argument('--repair-set',choices=['api-only','all-eight'],default='api-only')
 p.add_argument('--full-suite',action='store_true',help='Also relink and run the complete upstream C++ suite with the repaired translation unit')
 a=p.parse_args();source=a.source.resolve();prepared=a.prepared.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 require_source_state(source,PIN);require_source_state(a.app_source,a.app_commit)
 patch_dir=ROOT/'patches'
 api_patch=patch_dir/'walletcore-4.8.4-api-repairs.patch'
 library_patch=api_patch if a.repair_set=='api-only' else patch_dir/'walletcore-4.8.4-combined-eight.patch'
 expected=library_patch.read_bytes()
 head=subprocess.check_output(['git','-C',str(prepared),'rev-parse','HEAD'],text=True).strip()
 diff=lambda:subprocess.check_output(['git','-C',str(prepared),'diff','HEAD','--binary'])
 if head!=PIN or diff()!=expected:raise ValueError('Prepared source must contain exactly the selected repair set')
 if subprocess.check_output(['git','-C',str(prepared),'ls-files','--others','--exclude-standard']).strip():raise ValueError('Unexpected source inputs')
 patch=ROOT/'patches/walletcore-4.8.4-extended-key-kind.patch';fixture=ROOT/'tests/UpstreamExtendedKeyKind.cpp'
 input_hashes={f:hashlib.sha256(f.read_bytes()).hexdigest() for f in [patch,fixture]}
 libraries=[prepared/p for p in ['build/native-core/libTrustWalletCore.a','build/native-core/trezor-crypto/libTrezorCrypto.a','rust/target/release/libwallet_core_rs.a','build/native-core/libprotobuf.a']]
 hashes={str(f.relative_to(prepared)):hashlib.sha256(f.read_bytes()).hexdigest() for f in libraries}
 env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR']};commands=[];cases=[];started=time.monotonic()
 def run(command,name,required=True,cwd=None,timeout=180):
  with (out/(name+'.log')).open('w') as log:code,timedout=logged_command(command,stream=log,timeout=timeout,cwd=cwd,env=env)
  commands.append(dict(name=name,command=command,exit_code=code,timed_out=timedout));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  if required and code:raise RuntimeError(name+' failed; evidence retained')
  return code,timedout
 flags=['clang++','-std=c++20','-O2','-DNDEBUG','-I',str(prepared/'src'),'-I',str(prepared/'include'),'-I',str(prepared/'trezor-crypto/include'),'-I',str(a.boost),'-I',str(prepared/'build/local/include')]
 with tempfile.TemporaryDirectory(prefix='oath-extended-key-') as directory:
  work=Path(directory);(work/'src').mkdir();file=work/'src/HDWallet.cpp'
  file.write_bytes((source/'src/HDWallet.cpp').read_bytes())
  run(['git','apply','--include=src/HDWallet.cpp',str(api_patch)],'prepare-before',cwd=work)
  stages=json.loads((ROOT/'evidence/core-native/extended-repro-full/result.json').read_bytes())['cases']
  stage_hashes={row['stage']:row['source_sha256'] for row in stages}
  for stage in ['before','after']:
   if stage=='after':run(['git','apply',str(patch)],'apply',cwd=work)
   obj=work/(stage+'.o');binary=work/stage;source_hash=hashlib.sha256(file.read_bytes()).hexdigest()
   if source_hash!=stage_hashes[stage]:raise ValueError('Extended-key source mismatch for '+stage)
   prepared_stage='after' if a.repair_set=='all-eight' else 'before'
   if stage==prepared_stage and file.read_bytes()!=(prepared/'src/HDWallet.cpp').read_bytes():
    raise ValueError('Tested translation unit differs from the selected library source')
   run(flags+['-c',str(file),'-o',str(obj)],stage+'-compile')
   run(flags+[str(fixture),str(obj)]+[str(f) for f in libraries]+['-o',str(binary)],stage+'-link')
   code,timedout=run([str(binary)],stage,required=False);log=(out/(stage+'.log')).read_text();summary='EXTENDED_KEY_CHECKS total=94 public_rejected='+('9 failures=21' if stage=='before' else '30 failures=0')
   cases.append(dict(stage=stage,exit_code=code,timed_out=timedout,summary=log.strip().splitlines()[-1],source_sha256=source_hash,expected_outcome_observed=code==(1 if stage=='before' else 0) and not timedout and log.strip().endswith(summary)))
  suite=None
  if a.full_suite:
   # Upstream computes its fixture root from the executable's directory depth.
   binary=prepared/'build/tests/tests-extended-fixed';binary.parent.mkdir(parents=True,exist_ok=True)
   link=shlex.split((prepared/'build/native-core/tests/CMakeFiles/tests.dir/link.txt').read_text())
   link.insert(link.index('-o'),str(obj));link[link.index('-o')+1]=str(binary)
   run(link,'full-suite-link',cwd=prepared/'build/native-core/tests')
   env['TEST_TMPDIR']=str(work/'test-temp');Path(env['TEST_TMPDIR']).mkdir()
   report=out/'full-suite.json'
   code,timedout=run([str(binary),'--gtest_output=json:'+str(report)],'full-suite',required=False,cwd=prepared,timeout=1800)
   data=json.loads(report.read_text())
   suite={k:data[k] for k in ['tests','failures','disabled','errors','time']}
   suite.update(exit_code=code,timed_out=timedout,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())
   if code or timedout or suite['tests']!=2363 or any(suite[k] for k in ['failures','disabled','errors']):raise RuntimeError('Complete upstream suite did not pass; evidence retained')
 if diff()!=expected:raise ValueError('Prepared source changed during execution')
 for f in libraries:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=hashes[str(f.relative_to(prepared))]:raise ValueError('Native library changed during execution')
 for f,expected_hash in input_hashes.items():
  if hashlib.sha256(f.read_bytes()).hexdigest()!=expected_hash:raise ValueError('Patch or fixture changed during execution')
 require_source_state(source,PIN);require_source_state(a.app_source,a.app_commit)
 result=dict(check='upstream-extended-key-kind',source_commit=a.app_commit,upstream_commit=PIN,status='passed' if all(c['expected_outcome_observed'] for c in cases) else 'failed',cases=cases,
             compiler=subprocess.check_output(['clang++','--version'],text=True),duration_seconds=round(time.monotonic()-started,3),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),base_patch_sha256=hashlib.sha256(expected).hexdigest(),repair_set=a.repair_set,library_hashes=hashes,log_sha256=hashlib.sha256((out/'after.log').read_bytes()).hexdigest(),
             limitations=['Full production HDWallet translation units; complete native dependencies, no substituted implementations.','Native host test; doesn’t execute an Apple framework or application.','No Oath application call to this C++ API established.','No App Store or historical binary equivalence proof.'])
 result['full_upstream_suite']=suite
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=cases,full_upstream_suite=suite)));return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
