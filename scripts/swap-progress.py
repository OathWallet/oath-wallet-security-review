#!/usr/bin/env python3
"""Reproduce EVM swap destination identity against the production progress decoder."""
import argparse, hashlib, json, os, re, subprocess, time
from pathlib import Path
from bounded_process import logged_command
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
BEFORE='8fa6ee3bf99caf78ab71997b5642e323cccb95da'
FIXTURE='Packages/OathAnkr/Tests/OathAnkrTests/ThorchainSwapDestinationTests.swift'
CASES=['testPolygonNativeAndTokenPayoutsMatchChecksumVariants','testOtherSupportedEVMChainsPreserveCaseInsensitiveMatching','testMatchingNeverIgnoresDifferentAddressesChainsAssetsOrInboundIDs']

def outcome(text,code,method):
    names={f'-[OathAnkrTests.ThorchainSwapDestinationTests {method}]',f'ThorchainSwapDestinationTests.{method}'}
    events=re.findall(r"^Test Case '([^']+)' (started|passed|failed|skipped)(?:\.| \()",text,re.M)
    if len(events)!=2 or any(n not in names for n,_ in events) or events[0][1]!='started':return 'failed'
    errors=[x for x in text.splitlines() if ': error:' in x]
    if code==0 and events[1][1]=='passed' and not errors:return 'passed'
    if code!=0 and events[1][1]=='failed' and len(errors)==4 and all('XCTAssertEqual failed' in e and 'Polygon checksum variants must identify the same payout destination' in e and 'nil' in e and 'CDCD' in e for e in errors):return 'destination-mismatch-reproduced'
    return 'failed'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--before',action='store_true');p.add_argument('--expected-commit');a=p.parse_args()
    source,out,scratch=a.source.resolve(),a.output.resolve(),a.scratch.resolve()
    expected=BEFORE if a.before else a.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit']
    if a.before and a.expected_commit and a.expected_commit!=BEFORE:p.error('Before revision is fixed')
    sha=require_source_state(source,expected);out.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    start=time.monotonic()
    def run(name,cmd,timeout):
        began=time.monotonic();log=out/(name+'.log')
        with log.open('w') as f:code,timed_out=logged_command(cmd,stream=f,env=env,timeout=timeout)
        text=log.read_text(errors='replace')
        for old,new in [(str(source),'<SOURCE>'),(str(scratch),'<SCRATCH>'),(str(out),'<OUTPUT>'),(str(Path.home()),'<HOME>')]:text=text.replace(old,new)
        log.write_text(text)
        return dict(exit_code=code,timed_out=timed_out,duration_seconds=round(time.monotonic()-began,3),log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()),text
    swift,_=run('swift-version',['xcrun','swift','--version'],30);xcode,_=run('xcode-version',['xcodebuild','-version'],30)
    prefix=['--package-path',str(source/'Packages/OathAnkr'),'--build-system','native','--scratch-path',str(scratch)]
    build,_=run('build',['swift','build',*prefix,'--force-resolved-versions','--build-tests','--jobs','4'],900)
    runs=[];binary_hash=None
    if build['exit_code']==0 and not build['timed_out']:
        directory=Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],env=env,text=True).strip())
        bundles=list(directory.glob('*.xctest'))
        if len(bundles)!=1:raise RuntimeError('Expected one networking test bundle')
        binary=bundles[0]/'Contents/MacOS/OathAnkrPackageTests';binary_hash=hashlib.sha256(binary.read_bytes()).hexdigest()
        for repetition in range(3):
            for index,method in enumerate(CASES):
                selector='OathAnkrTests.ThorchainSwapDestinationTests/'+method
                row,text=run(f'run-{repetition+1}-{index+1}',['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',selector,str(bundles[0])],120)
                row.update(selector=selector,status=outcome(text,row['exit_code'],method),expected='destination-mismatch-reproduced' if a.before and index==0 else 'passed');runs.append(row)
    require_source_state(source,sha)
    ok=swift['exit_code']==0 and xcode['exit_code']==0 and len(runs)==9 and all(r['status']==r['expected'] and not r['timed_out'] for r in runs)
    result=dict(check='swap-progress',source_commit=sha,phase='before' if a.before else 'after',status=('expected-failure' if a.before else 'passed') if ok else 'failed',build=build,runs=runs,toolchain={'swift':swift,'xcode':xcode},fixture_sha256=hashlib.sha256((source/FIXTURE).read_bytes()).hexdigest(),test_binary_sha256=binary_hash,duration_seconds=round(time.monotonic()-start,3),runtime_scope='macOS host; production swap progress decoder and synthetic observations; test processes deny network',limitation='No provider, UI, simulator, physical device, blockchain broadcast or App Store execution. Synthetic provider observations enter the production progress decoder.')
    log=out/'swap-progress.log';log.write_text(json.dumps(result,indent=2)+'\n');result.update(log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());(out/'swap-progress.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['phase'],result['status'],len(runs),'case processes');raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
