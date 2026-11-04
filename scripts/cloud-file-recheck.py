#!/usr/bin/env python3
"""Fresh historical/current backup-file race replay plus pristine current package tests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from isolated_tests import classify
from source_state import require_source_state
ROOT=Path(__file__).resolve().parents[1]
BASE='c7acd23bb139864a40273f405d18b479589d2b20'
PIN='c2ff488a7c7a647b2e6ab03aa1768f5735928e7e'
PKG=Path('Packages/OathCloudBackup')
WRITER=PKG/'Sources/OathCloudBackup/CloudDrive.swift'
CASES=[('CloudFileRaceTests','testCachedMetadataDoesNotAuthorizeAReplacementSymlink'),('CloudFilePublishTests','testDanglingLinkAtBackupNameIsPreservedAsAConflict'),('BackupFileBoundaryTests','testExclusiveCreatorWinsAtPublicationBoundary')]
HOOK='if url.lastPathComponent == "audit-interleaving.oathbackup" { try Data([19, 23]).write(to: url, options: .withoutOverwriting) }'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['source','scratch','output']:p.add_argument(n,type=Path)
    a=p.parse_args();source,scratch,out=[getattr(a,n).resolve() for n in ['source','scratch','output']]
    require_source_state(source,PIN)
    if scratch.exists() or out.exists():raise ValueError('Fresh scratch/output required')
    scratch.mkdir(parents=True);out.mkdir(parents=True);start=time.monotonic()
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    def run(cmd,path,timeout=900):
        with path.open('wb') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        if r.returncode:raise RuntimeError(str(path)+' failed; log retained')
    for cmd,name in [(['xcodebuild','-version'],'xcode-version.log'),(['swift','--version'],'swift-version.log'),(['python3','--version'],'python-version.log')]:run(cmd,out/name)
    reports=[]
    for stage,pin,instrument in [('before',BASE,True),('after',PIN,True),('current-package',PIN,False)]:
        work=scratch/stage;work.mkdir();copy=work/'source';dest=out/stage;dest.mkdir()
        run(['git','clone','--shared','--no-checkout',str(source),str(copy)],dest/'clone.log')
        run(['git','-C',str(copy),'checkout','--detach',pin],dest/'checkout.log')
        require_source_state(copy,pin)
        originals={};fixtures={};writer_original=(copy/WRITER).read_bytes()
        if instrument:
            for name in ['CloudFileRaceTests.swift','CloudFilePublishTests.swift','BackupFileBoundaryTests.swift']:
                path=copy/PKG/'Tests/OathCloudBackupTests'/name
                originals[path]=path.read_bytes() if path.exists() else None
                body=(ROOT/'fixtures/backup-file-identity'/name).read_bytes() if name=='BackupFileBoundaryTests.swift' else subprocess.check_output(['git','-C',str(source),'show',PIN+':'+str(PKG/'Tests/OathCloudBackupTests'/name)])
                path.write_bytes(body);fixtures[name]=sha(body)
            text=writer_original.decode();anchor='try encrypted.write(to: url, options: .atomic)' if stage=='before' else 'let status = renamex_np(ready.path, url.path, UInt32(RENAME_EXCL))'
            if text.count(anchor)!=1:raise ValueError('Publication anchor mismatch')
            (copy/WRITER).write_text(text.replace(anchor,HOOK+'\n                    '+anchor))
            (dest/'instrumentation.patch').write_bytes(subprocess.check_output(['git','-C',str(copy),'diff','--',str(WRITER)]))
        prefix=['--package-path',str(copy/PKG),'--build-system','native','--scratch-path',str(work/'build')]
        try:
            run(['swift','build',*prefix,'--build-tests','--jobs','4'],dest/'build.log')
            binpath=Path(subprocess.check_output(['swift','build',*prefix,'--show-bin-path'],text=True,env=env).strip());bundle=binpath/'OathCloudBackupPackageTests.xctest'
            selections=['OathCloudBackupTests.'+suite+'/'+method for suite,method in CASES]
            if not instrument:
                run(['swift','test',*prefix,'list','--skip-build','--disable-swift-testing'],dest/'discovery.log')
                selections=[s for s in (dest/'discovery.log').read_text().splitlines() if re.fullmatch(r'OathCloudBackupTests\.\w+/\w+',s)]
                if not selections or len(selections)!=len(set(selections)):raise ValueError('Empty or duplicate XCTest discovery')
            rows=[]
            for i,sel in enumerate(selections):
                r=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',sel,str(bundle)],env=env,capture_output=True,timeout=120)
                raw=r.stdout+r.stderr;log=dest/(str(i).zfill(3)+'.log');log.write_bytes(raw)
                status=classify(raw.decode(errors='replace'),r.returncode)
                errors=raw.count(b': error: ')
                rows.append({'selector':sel,'status':status,'exit_code':r.returncode,'assertion_errors':errors,'log':log.name,'log_sha256':sha(raw)})
                expected=2 if stage=='before' else 0
                if r.returncode!=int(expected>0) or errors!=expected or status!=('failed' if expected else 'passed'):raise ValueError('Unexpected result '+stage+'/'+sel+'; original log retained')
                if stage=='before':
                    needles=[['XCTAssertNotEqual failed','XCTAssertNil failed'],['XCTAssertThrowsError failed','XCTAssertEqual failed'],['XCTAssertThrowsError failed','Earlier complete file must survive']][i]
                    if not all(n.encode() in raw for n in needles):raise ValueError('Unrelated historical failure')
            swift_testing=None
            if not instrument:
                run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','swift','test',*prefix,'--skip-build','--disable-xctest','--xunit-output',str(dest/'swift-testing.xml')],dest/'swift-testing.log')
                text=(dest/'swift-testing.log').read_text()
                if 'Test run with 1 test in 0 suites passed' not in text:raise ValueError('Expected one Swift Testing reset barrier test')
                swift_testing={'tests':1,'status':'passed','log':'swift-testing.log','log_sha256':sha((dest/'swift-testing.log').read_bytes())}
            result={'source_commit':pin,'stage':stage,'instrumented':instrument,'original_writer_sha256':sha(writer_original),'compiled_writer_sha256':sha((copy/WRITER).read_bytes()),'fixtures':fixtures,'methods':rows,'swift_testing':swift_testing,'test_executable_sha256':sha((bundle/'Contents/MacOS'/bundle.stem).read_bytes()),'runtime_network':'denied by sandbox-exec'}
        finally:
            (copy/WRITER).write_bytes(writer_original)
            for path,body in originals.items():
                if body is None:path.unlink()
                else:path.write_bytes(body)
        require_source_state(copy,pin)
        result['tracked_source_restored']=True
        result['files']=[{'path':f.name,'sha256':sha(f.read_bytes())} for f in sorted(dest.iterdir()) if f.is_file()]
        (dest/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        reports.append({'stage':stage,'report':stage+'/result.json','sha256':sha((dest/'result.json').read_bytes()),'xctest_methods':len(rows),'swift_testing_tests':1 if swift_testing else 0})
        print(stage,len(rows),'XCTest methods; Swift Testing',1 if swift_testing else 0,flush=True)
    require_source_state(source,PIN)
    report={'source_commit':PIN,'historical_commit':BASE,'driver_sha256':sha(Path(__file__).read_bytes()),'boundary_fixture_sha256':sha((ROOT/'fixtures/backup-file-identity/BackupFileBoundaryTests.swift').read_bytes()),'duration_seconds':round(time.monotonic()-start,3),'reports':reports,'files':[{'path':f.name,'sha256':sha(f.read_bytes())} for f in sorted(out.iterdir()) if f.is_file()]}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
