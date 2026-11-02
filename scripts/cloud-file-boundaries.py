#!/usr/bin/env python3
"""Reproduce backup selection and publication errors in temporary directories."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from bounded_process import logged_command
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
BASE='c7acd23bb139864a40273f405d18b479589d2b20'
FIX='dd16c594baf46299d489ce67737aa5fb101c5ae4'
PKG=Path('Packages/OathCloudBackup')
DEST=PKG/'Tests/OathCloudBackupTests'
WRITER=PKG/'Sources/OathCloudBackup/CloudDrive.swift'
CASES=[
    ('CloudFileRaceTests','testCachedMetadataDoesNotAuthorizeAReplacementSymlink',2),
    ('CloudFilePublishTests','testDanglingLinkAtBackupNameIsPreservedAsAConflict',2),
    ('BackupFileBoundaryTests','testExclusiveCreatorWinsAtPublicationBoundary',2),
]
sha=lambda data:hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','scratch','output'): parser.add_argument(name,type=Path)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in {'HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL'}}
    results=[]
    with tempfile.TemporaryDirectory(prefix='backup-file-replay-') as tmp:
        for stage,rev in [('before',BASE),('after',FIX)]:
            app=Path(tmp)/stage
            subprocess.run(['git','clone','--quiet','--local','--no-checkout',args.repo.resolve(),app],check=True)
            subprocess.run(['git','-C',app,'checkout','--quiet','--detach',rev],check=True)
            require_source_state(app,rev)
            fixtures={}
            for name in ['CloudFileRaceTests.swift','CloudFilePublishTests.swift']:
                path=DEST/name
                body=subprocess.check_output(['git','-C',app,'show',f'{FIX}:{path}'])
                if stage=='before': (app/path).write_bytes(body)
                if (app/path).read_bytes()!=body: raise ValueError('Fixture mismatch')
                fixtures[name]=sha(body)
            boundary=ROOT/'fixtures/backup-file-identity/BackupFileBoundaryTests.swift'
            (app/DEST/boundary.name).write_bytes(boundary.read_bytes());fixtures[boundary.name]=sha(boundary.read_bytes())
            source=(app/WRITER).read_text()
            anchor='try encrypted.write(to: url, options: .atomic)' if stage=='before' else 'let status = renamex_np(ready.path, url.path, UInt32(RENAME_EXCL))'
            if source.count(anchor)!=1: raise ValueError('Unexpected writer source')
            # Model a noncooperating creator after the absence check and before publication.
            hook='if url.lastPathComponent == "audit-interleaving.oathbackup" { try Data([19, 23]).write(to: url, options: .withoutOverwriting) }'
            (app/WRITER).write_text(source.replace(anchor,hook+'\n                    '+anchor))
            build=['swift','build','--package-path',str(app/PKG),'--scratch-path',str(args.scratch.resolve()),'--build-system','native']
            log=Path(tmp)/(stage+'-build.log')
            with log.open('w') as stream:code,timed=logged_command(build+['--build-tests','--jobs','4'],stream=stream,timeout=600,env=env)
            if code or timed: raise ValueError(log.read_text()[-1500:])
            b=Path(subprocess.check_output(build+['--show-bin-path'],env=env,text=True).strip())/'OathCloudBackupPackageTests.xctest'
            for suite,case,before_failures in CASES:
                selector=f'OathCloudBackupTests.{suite}/{case}'
                run=['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)','xcrun','xctest','-XCTest',selector,str(b)]
                f=Path(tmp)/(stage+'-'+case+'.log')
                with f.open('w') as stream:code,timed=logged_command(run,stream=stream,timeout=60,env=env)
                text=f.read_text()
                expected=before_failures if stage=='before' else 0
                ended='failed' if expected else 'passed'
                observed=re.findall(r"^Test Case '([^']+)' (started|failed|passed|skipped)",text,re.M)
                name=f'-[OathCloudBackupTests.{suite} {case}]'
                if timed or code!=int(expected>0) or observed!=[(name,'started'),(name,ended)] or text.count(': error: ')!=expected:
                    raise ValueError(f'Unexpected {stage}/{selector}: '+text[-1400:])
                errors=[line.split(': error: ',1)[1] for line in text.splitlines() if ': error: ' in line]
                if stage=='before' and not all(any(needle in e for e in errors) for needle in {
                    CASES[0][1]:['XCTAssertNotEqual failed','XCTAssertNil failed'],
                    CASES[1][1]:['XCTAssertThrowsError failed','XCTAssertEqual failed'],
                    CASES[2][1]:['XCTAssertThrowsError failed','Earlier complete file must survive']}[case]):
                    raise ValueError('Unrelated failure: '+selector)
                results.append(dict(stage=stage,source_commit=rev,case=selector,exit_code=code,failures=errors,
                                    raw_log_sha256=sha(f.read_bytes()),fixtures=fixtures,
                                    original_writer_sha256=sha(source.encode()),instrumented_writer_sha256=sha((app/WRITER).read_bytes())))
                print(stage,case,ended,flush=True)
                (out/'result.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
