#!/usr/bin/env python3
"""Run serialization mutations against the actual clean OathCloudBackup package."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from bounded_process import logged_command
from source_state import require_source_state

ROOT=Path(__file__).resolve().parents[1]
MARKER='MULTISIG_RECOVERY_OK families=11 checks=197 scope=serialization'

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('source',type=Path)
    p.add_argument('--commit',required=True); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); source=a.source.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    require_source_state(source,a.commit); started=time.monotonic()
    fixture=ROOT/'tests/MultisigRecoveryBoundary.swift'
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    with tempfile.TemporaryDirectory(prefix='oath-multisig-recovery-') as temp:
        work=Path(temp); (work/'Sources/Probe').mkdir(parents=True)
        package=json.dumps(str(source/'Packages/OathCloudBackup'))
        manifest='// swift-tools-version: 6.0\nimport PackageDescription\n'
        manifest+='let package = Package(name: "Probe", platforms: [.macOS(.v14)], dependencies: [.package(path: '+package+')], targets: [.executableTarget(name: "Probe", dependencies: [.product(name: "OathCloudBackup", package: "OathCloudBackup")])])\n'
        (work/'Package.swift').write_text(manifest); shutil.copyfile(fixture,work/'Sources/Probe/Probe.swift')
        command=['swift','run','--package-path',str(work),'Probe']
        with (out/'run.log').open('w') as log: code,timeout=logged_command(command,stream=log,timeout=300,env=env)
        text=(out/'run.log').read_text()
        passed=code==0 and not timeout and text.splitlines().count(MARKER)==1
    require_source_state(source,a.commit)
    inputs=[p for p in (source/'Packages/OathCloudBackup/Sources/OathCloudBackup').glob('*.swift') if not p.name.startswith('._')]
    result=dict(check='multisig-recovery',source_commit=a.commit,status='passed' if passed else 'failed',
                exit_code=code,timed_out=timeout,assertion_count=197 if passed else None,
                duration_seconds=round(time.monotonic()-started,3),command=command,
                compiler=subprocess.check_output(['swift','--version'],text=True),
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                log_sha256=hashlib.sha256((out/'run.log').read_bytes()).hexdigest(),
                source_hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                runtime_scope='macOS host; production package; serialization only, not cryptographic identity or live-chain validation')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(MARKER if passed else 'Multisig recovery boundary FAILED; inspect logs')
    return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())
