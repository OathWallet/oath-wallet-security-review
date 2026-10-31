#!/usr/bin/env python3
"""Run bounded, explicit host checks. Never enable live-chain tests or deployment."""
import argparse, hashlib, json, os, platform, re, signal, subprocess, time, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ['OathDiagnostics', 'OathCloudBackup', 'OathDatabase', 'OathBitcoin', 'OathAnkr', 'OathAezeed', 'OathWalletHandoff']
MODES = ['envelope', 'security', 'authentication', 'protected-startup', 'lifecycle', 'walletconnect',
         'evm-send', 'solana-send', 'tron-send', 'xrpl-send', 'stellar-send',
         'aptos-send', 'sui-send', 'near-send', 'ton-send', 'thorchain-send', 'arc-send', 'permission-batch']

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('check', choices=PACKAGES + MODES + ['public', 'diagnostics-coverage', 'clipboard', 'build'])
    p.add_argument('--output', type=Path, default=ROOT/'evidence/local')
    a = p.parse_args()
    source, out = a.source.resolve(), a.output.resolve()
    pin = json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit']
    sha = require_source_state(source, pin)
    out.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.gettempdir())/'oath-security-review-builds'/sha/a.check
    # Deliberately do not inherit OATH_* flags, provider credentials or release secrets.
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    env['OATH_VALIDATION_SCRATCH'] = str(scratch)
    if a.check in PACKAGES:
        command = ['python3',str(ROOT/'scripts/isolated_tests.py'),str(source),a.check,str(scratch)+'-native',str(out)]
    elif a.check in MODES:
        command = ['python3','Tools/CheckMultiWallet.py','--'+a.check]
    elif a.check == 'build':
        subprocess.run(['sh','Tools/PreparePublicBuild.sh'],cwd=source,env=env,check=True)
        command = ['xcodebuild','-project','OathAtmosphere.xcodeproj','-scheme','OathAtmosphere','-configuration','Release','-destination','generic/platform=iOS','-derivedDataPath',str(scratch),'CODE_SIGNING_ALLOWED=NO','build']
    else:
        command = ['python3',{'public':'Tools/ValidatePublicRelease.py','diagnostics-coverage':'Tools/CheckDiagnosticsCoverage.py','clipboard':'Tools/CheckClipboard.py'}[a.check]]
        if a.check == 'public': command += ['--scan']
    start = time.time()
    log = out/(a.check+'.log')
    code, timed_out = -1, False
    with log.open('w') as stream:
        process = subprocess.Popen(command,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            code = process.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    text = log.read_text(errors='replace').replace('\x00', '<NUL>').replace(str(source), '<SOURCE>').replace(str(ROOT), '<AUDIT>')
    text = text.replace(str(scratch), '<SCRATCH>').replace(os.path.expanduser('~'), '<HOME>')
    log.write_text(text)
    summaries = [line for line in text.splitlines() if re.search(r'XCTest:|Executed \d+ tests|Test run with|checks passed|Passed \d+|BUILD (SUCCEEDED|FAILED)|skipped',line)]
    result = dict(check=a.check,source_commit=sha,command=command,status='passed' if code==0 else 'failed',exit_code=code,
                  timed_out=timed_out,duration_seconds=round(time.time()-start,2),platform=platform.platform(),
                  summaries=summaries,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                  runtime_scope='host' if a.check!='build' else 'compile-only',live_network_tests_enabled=False)
    if a.check in PACKAGES:
        xml = out/(a.check+'.xml')
        if xml.exists():
            tree = ET.parse(xml)
            cases = list(tree.iter('testcase'))
            result['xunit'] = dict(tests=len(cases), failures=sum(c.find('failure') is not None for c in cases),
                                   errors=sum(c.find('error') is not None for c in cases),
                                   skipped=sum(c.find('skipped') is not None for c in cases),
                                   sha256=hashlib.sha256(xml.read_bytes()).hexdigest())
        else:
            result['xunit'] = {'available': False}
        swift_log = out/(a.check+'-swift-testing.log')
        if swift_log.exists():
            swift_text = swift_log.read_text(errors='replace')
            result['swift_testing'] = dict(log_sha256=hashlib.sha256(swift_log.read_bytes()).hexdigest(), summaries=[line for line in swift_text.splitlines() if 'Test run with' in line or 'skipped' in line])
    # Commands are normalized for publication and still reconstructible from the README.
    result['command']=[s.replace(str(source),'<SOURCE>').replace(str(scratch),'<SCRATCH>').replace(str(ROOT),'<AUDIT>') for s in command]
    (out/(a.check+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(a.check, result['status'], result['duration_seconds'], 'seconds', flush=True)
    raise SystemExit(0 if code == 0 else 1)

if __name__ == '__main__': main()
