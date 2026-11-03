#!/usr/bin/env python3
"""Run bounded, explicit host checks. Never enable live-chain tests or deployment."""
import argparse, hashlib, json, os, platform, re, signal, subprocess, time, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ['OathDiagnostics', 'OathCloudBackup', 'OathDatabase', 'OathBitcoin', 'OathAnkr', 'OathAezeed', 'OathWalletHandoff', 'OathTokenImages', 'OathExchangeRates']
SDK_MODES = ['walletconnect-sdk', 'walletconnect-verify']
APP_MODES = {'app-updates':'Tools/CheckAppUpdates.py', 'token-lookup':'Tools/CheckTokenLookup.py'}
SCANNER_MODES = {'scanner': [], 'wallet-links': ['--links'], 'scanner-lifecycle': ['--performance']}
RECOVERY_MODES = {'aezeed': 'aezeed', 'electrum': 'Electrum'}
MODES = [*RECOVERY_MODES, 'private-keys', 'envelope', 'security', 'authentication', 'protected-startup', 'lifecycle', 'walletconnect',
         'evm-send', 'solana-send', 'tron-send', 'xrpl-send', 'stellar-send',
         'aptos-send', 'sui-send', 'near-send', 'ton-send', 'thorchain-send', 'arc-send', 'permission-batch', 'cloud-restore']

def restore_case_count(text):
    matches = re.findall(r'^Passed (\d+) cloud-restore integration checks \(local synthetic backups; no live iCloud\)\.$', text, re.MULTILINE)
    return int(matches[0]) if len(matches) == 1 and int(matches[0]) >= 140 else None

def private_key_case_count(text):
    matches = re.findall(r'^Passed ([1-9][0-9]*) HD private-key browser/vault host checks\. Synthetic seed adapter; real public descriptors, leaf-key derivation, database and authorization\. No user data, network, simulator or device used\.$', text, re.MULTILINE)
    # The pinned baseline fixture completes 305 assertions. A smaller summary
    # must not silently certify a reduced run after harness changes.
    return int(matches[0]) if len(matches) == 1 and int(matches[0]) >= 305 else None

def recovery_case_count(mode, text):
    pattern = rf'^Passed ([1-9][0-9]*) {RECOVERY_MODES[mode]} host integration checks'
    pattern += r' across 5 formats:' if mode == 'electrum' else ':'
    matches = re.findall(pattern, text, re.MULTILINE)
    minimum = 30 if mode == 'aezeed' else 201
    return int(matches[0]) if len(matches) == 1 and int(matches[0]) >= minimum else None

def scanner_case_count(mode, text):
    """Require the harness's final assertion summary, not just a successful build."""
    patterns = {
        'scanner': r'^Passed (\d+) scanner checks; (\d+) real CoreImage/Vision QR round trips; (\d+) chains;',
        'wallet-links': r'^Wallet link checks passed: (\d+)$',
        'scanner-lifecycle': r'^Scanner concurrency/lifecycle: (\d+) checks passed$',
    }
    matches = re.findall(patterns[mode], text, re.MULTILINE)
    if len(matches) != 1:
        return None
    if mode == 'scanner':
        cases, images, chains = map(int, matches[0])
        return cases if cases > 0 and images > 0 and chains > 0 else None
    return int(matches[0]) or None

def sdk_case_counts(text):
    """Use individual XCTest outcomes, not the separate empty Swift Testing run."""
    # SwiftPM can write this exact stderr warning in the middle of a buffered
    # XCTest stdout line. Remove only that known diagnostic, including its
    # newline, to reconstruct the original case line. Keep the raw log intact.
    text = text.replace("warning: '--build-system native' has been deprecated and will be removed in a future release; please report an issue at https://github.com/swiftlang/swift-package-manager/issues if you are unable to adopt the default build system.\n", "")
    states = re.findall(r"^Test Case .+ (passed|skipped|failed) \(", text, re.MULTILINE)
    return {state: states.count(state) for state in ['passed', 'skipped', 'failed']}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('check', choices=PACKAGES + list(APP_MODES) + MODES + SDK_MODES + list(SCANNER_MODES) + ['public', 'diagnostics-coverage', 'clipboard', 'build'])
    p.add_argument('--output', type=Path, default=ROOT/'evidence/local')
    p.add_argument('--expected-commit', help='Exact clean candidate commit; does not change the published review target')
    p.add_argument('--scratch', type=Path, help='Explicit isolated build directory to reuse; source pin/cleanliness checks still apply')
    a = p.parse_args()
    source, out = a.source.resolve(), a.output.resolve()
    pin = a.expected_commit or json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit']
    sha = require_source_state(source, pin)
    out.mkdir(parents=True, exist_ok=True)
    scratch = a.scratch.absolute() if a.scratch else Path(tempfile.gettempdir())/'oath-security-review-builds'/sha/a.check
    # Deliberately do not inherit OATH_* flags, provider credentials or release secrets.
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','SDKROOT','LANG','LC_ALL','CI']}
    env['OATH_VALIDATION_SCRATCH'] = str(scratch)
    if a.check in PACKAGES:
        command = ['python3',str(ROOT/'scripts/isolated_tests.py'),str(source),a.check,str(scratch)+'-native',str(out)]
    elif a.check in APP_MODES:
        command = ['python3', APP_MODES[a.check]]
    elif a.check in SCANNER_MODES:
        command = ['python3', 'Tools/CheckScanner.py'] + SCANNER_MODES[a.check]
    elif a.check in SDK_MODES:
        command = ['python3','Tools/CheckWalletConnectSDK.py','--build-system','native']
        if a.check == 'walletconnect-verify':
            # This enables only a URLProtocol fixture in its own process, never
            # a production relay or the unrelated opt-in live test flags.
            env['OATH_VERIFY_ABSENCE_TEST'] = '1'
            command += ['--filter','VerifyAbsenceTests']
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
    sdk_cases = sdk_case_counts(text) if a.check in SDK_MODES or a.check == 'token-lookup' else None
    scanner_cases = scanner_case_count(a.check, text) if a.check in SCANNER_MODES else None
    restore_cases = restore_case_count(text) if a.check == 'cloud-restore' else None
    recovery_cases = recovery_case_count(a.check, text) if a.check in RECOVERY_MODES else None
    private_key_cases = private_key_case_count(text) if a.check == 'private-keys' else None
    if a.check == 'private-keys' and private_key_cases is None:
        code = code or 1
    if a.check in RECOVERY_MODES and recovery_cases is None:
        code = code or 1
    if a.check == 'cloud-restore' and restore_cases is None:
        code = code or 1
    if a.check in SCANNER_MODES and scanner_cases is None:
        code = code or 1
    app_update_counts = re.findall(r'^Passed (\d+) app update checks: actual bundle metadata,',text,re.M) if a.check == 'app-updates' else []
    if a.check == 'app-updates' and (len(app_update_counts)!=1 or int(app_update_counts[0]) < 20):
        code = code or 1
    if sdk_cases is not None:
        minimum = 56 if a.check == 'walletconnect-sdk' else (10 if a.check == 'token-lookup' else 1)
        if sdk_cases['passed'] < minimum or sdk_cases['failed']:
            code = code or 1
    summaries = [line for line in text.splitlines() if re.search(r'XCTest:|Executed \d+ tests|Test run with|checks passed|Passed \d+|BUILD (SUCCEEDED|FAILED)|skipped',line)]
    result = dict(check=a.check,source_commit=sha,command=command,status='passed' if code==0 else 'failed',exit_code=code,
                  timed_out=timed_out,duration_seconds=round(time.time()-start,2),platform=platform.platform(),
                  summaries=summaries,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                  runtime_scope='host' if a.check!='build' else 'compile-only',live_network_tests_enabled=False)
    if a.check in RECOVERY_MODES:
        result['assertion_count'] = recovery_cases
        result['runtime_scope'] = 'macOS host, encrypted vault, shipped Bitcoin descriptor builder and local database, host BIP39 seed adapter'
    if a.check == 'private-keys':
        result['assertion_count'] = private_key_cases
        result['runtime_scope'] = 'macOS host; production vault, SQL and Bitcoin-family leaf WIF derivation; substituted application key/export engine with synthetic HD seed; does not execute OathPrivateKeyExport.swift, UIKit or OS authentication'
    if app_update_counts: result['assertion_count'] = int(app_update_counts[0])
    if sdk_cases is not None: result['xctest_cases'] = sdk_cases
    if a.check == 'cloud-restore':
        result['assertion_count'] = restore_cases
        result['runtime_scope'] = 'macOS host; production restoration/encryption/SQL; substituted Wallet Core derivation; no live iCloud'
    if a.check in SCANNER_MODES:
        result['assertion_count'] = scanner_cases
        result['runtime_scope'] = 'macOS host; synthetic QR images, no camera, simulator, device or live-chain request'
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
    if code != 0:
        # Preserve a bounded sanitized failure excerpt in the Actions log even
        # when a transient artifact-host failure prevents upload.
        print('\n'.join(text.splitlines()[-60:]), flush=True)
    raise SystemExit(0 if code == 0 else 1)

if __name__ == '__main__': main()
