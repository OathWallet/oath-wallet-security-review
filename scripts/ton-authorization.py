#!/usr/bin/env python3
"""Exercise delayed TON signing authorization with the existing host adapters."""
import argparse, hashlib, json, os, re, tempfile, time
from pathlib import Path
from source_state import require_source_state
from bounded_process import logged_command

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    sha = require_source_state(source,json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    out.mkdir(parents=True,exist_ok=True)
    fixture = (ROOT/'tests/TonAuthorizationBoundary.swift').read_bytes()
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    env['OATH_VALIDATION_SCRATCH'] = str(args.scratch.resolve())
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oath-ton-authorization-') as temporary:
        work=Path(temporary);(work/'Tools').mkdir()
        for name in ['Packages','OathAtmosphere','OathApp','Vendor']:
            (work/name).symlink_to(source/name,target_is_directory=True)
        for file in (source/'Tools').iterdir():
            if file.name.startswith('._'): continue
            target = work/'Tools'/file.name
            if file.name == 'CheckMultiWallet.py':
                harness=file.read_text()
                marker='    environment = dict(os.environ,'
                assert harness.count(marker)==1
                harness=harness.replace(marker,'''    pins = json.loads((root / "Packages/OathDatabase/Package.resolved").read_text())["pins"]
    (work / "Package.resolved").write_text(json.dumps({"version": 2, "pins": pins}))
'''+marker)
                command='subprocess.run(["swift", "run", "--build-system", "native",'
                assert harness.count(command)==1
                harness=harness.replace(command,'subprocess.run(["swift", "run", "--force-resolved-versions", "--build-system", "native",')
                target.write_text(harness)
            elif file.name == 'CheckTonSendAuthorization.swift': target.write_bytes(fixture)
            else: target.symlink_to(file,target_is_directory=file.is_dir())
        log=out/'ton-authorization.log'
        with log.open('w') as stream:
            code,timed_out=logged_command(['python3',str(work/'Tools/CheckMultiWallet.py'),'--ton-send'],env=env,stream=stream,timeout=900)
        text=log.read_text(errors='replace').replace(str(work),'<HARNESS>').replace(str(source),'<SOURCE>').replace(str(args.scratch.resolve()),'<SCRATCH>').replace(os.path.expanduser('~'),'<HOME>')
        text=re.sub(r'/private/var/folders/[^/]+/[^/]+/T/oath-multiwallet-[^/\s]+','<GENERATED-HARNESS>',text)
        log.write_text(text)
    require_source_state(source,sha)
    pins=(source/'Packages/OathDatabase/Package.resolved').read_bytes()
    (out/'Package.resolved').write_bytes(pins)
    summaries=re.findall(r'^TON authorization review: (\d+) checks passed\.',text,re.M)
    passed=code==0 and summaries==['19']
    result=dict(check='ton-authorization',source_commit=sha,status='passed' if passed else 'failed',exit_code=code,timed_out=timed_out,
        assertions=int(summaries[0]) if len(summaries)==1 else None,duration_seconds=round(time.monotonic()-started,2),
        fixture_sha256=hashlib.sha256(fixture).hexdigest(),dependency_lock_sha256=hashlib.sha256(pins).hexdigest(),log='ton-authorization.log',log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        runtime_scope='macOS host; production vault, journal and imported-key TON signer; original synthetic biometric/HD/network adapters; no device or blockchain')
    (out/'ton-authorization.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if passed else 1)

if __name__=='__main__':main()
