#!/usr/bin/env python3
"""Run explicitly reviewed offline diagnostic modes in fresh host processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ('ArcTests', 'testOptionalLabelReportingThroughActualArcBatchAndOutbox', 'OATH_ARC_LABEL_OUTBOX_TEST'),
    ('EVMBroadcastRecoveryTests', 'testReceiptLookupFailureRetainsPrivacyFilteredDiagnostics', 'OATH_EVM_RECOVERY_DIAGNOSTICS'),
    ('EVMDuplicateBroadcastTests', 'testReconciledDuplicateIsSilentButUnverifiedDuplicateReportsItsCause', 'OATH_EVM_DUPLICATE_DIAGNOSTICS'),
    ('SendFeeFundingTests', 'testExpectedFeeValidationKeepsSendBlockedWithoutUploadingAppErrors', 'OATH_FEE_VALIDATION_DIAGNOSTICS_TEST'),
    ('SendQuoteExpiryTests', 'testExpiredQuoteIsNotUploadedButProviderExpiryAndLookalikesRemain', 'OATH_QUOTE_EXPIRY_DIAGNOSTICS_TEST'),
    ('XrplFailureCauseTests', 'testSendAndValidatedFailureCodesSurviveSharedPrivacyFiltering', 'OATH_XRPL_FAILURE_CAUSE_TEST'),
    ('XrplSendPreparationTests', 'testAccountRequirementsKeepQuotesBlockedWithoutHidingRealFailures', 'OATH_XRPL_PREPARATION_DIAGNOSTICS_TEST'),
)
TRACE_CASES = (('DiagnosticTraceTests', 'testRecordCapturesContextBeforeDetachedUpload', 'OATH_TRACE_OUTBOX_TEST'),)
SANDBOX = '(version 1) (allow default) (deny network*)'


def environment(inherited, flag=None):
    allowed = {'HOME', 'PATH', 'TMPDIR', 'DEVELOPER_DIR', 'SDKROOT', 'LANG', 'LC_ALL', 'CI'}
    result = {k: v for k, v in inherited.items() if k in allowed}
    if flag is not None:
        if flag not in {item[2] for item in CASES + TRACE_CASES}:
            raise ValueError('Unreviewed diagnostic mode')
        result[flag] = '1'
    return result


def outcome(text, code, cls, method, package='OathAnkr'):
    events = re.findall(r"^Test Case '([^']+)' (started|passed|skipped|failed)(?:\.| \()", text, re.M)
    names = {f'-[{package}Tests.{cls} {method}]', f'{cls}.{method}'}
    if code != 0 or len(events) != 2 or any(name not in names for name, _ in events):
        return 'failed'
    if events[0][1] != 'started' or events[1][1] not in {'passed', 'skipped'}:
        return 'failed'
    return events[1][1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--package', choices=['OathAnkr', 'OathDiagnostics'], default='OathAnkr')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    source, out, scratch = args.source.resolve(), args.output.resolve(), args.scratch.resolve()
    sha = require_source_state(source, json.loads((ROOT/'scope/source.json').read_text())['reviewed_commit'])
    if not Path('/usr/bin/sandbox-exec').is_file():
        raise RuntimeError('macOS host with sandbox-exec is required; no unconfined fallback')
    out.mkdir(parents=True, exist_ok=True)
    env = environment(os.environ)
    package = source/'Packages'/args.package
    cases = CASES if args.package == 'OathAnkr' else TRACE_CASES
    resolved = package/'Package.resolved'
    pins = resolved.read_bytes() if resolved.exists() else None
    prefix = ['--package-path', str(package), '--build-system', 'native', '--scratch-path', str(scratch)]
    started = time.monotonic()

    def command_log(name, command, command_env=env, timeout=120):
        log = out/(name+'.log')
        begin = time.monotonic()
        with log.open('w') as stream:
            code, timed_out = logged_command(command, stream=stream, env=command_env, timeout=timeout)
        text = log.read_text(errors='replace')
        for path, placeholder in [(str(source), '<SOURCE>'), (str(scratch), '<SCRATCH>'), (str(out), '<OUTPUT>'), (str(Path.home()), '<HOME>')]:
            text = text.replace(path, placeholder)
        log.write_text(text)
        return dict(exit_code=code, timed_out=timed_out, duration_seconds=round(time.monotonic()-begin, 3),
                    log=log.name, log_sha256=digest(log)), text

    toolchain = {tool: subprocess.check_output(cmd, env=env, text=True).strip()
                 for tool, cmd in [('xcode', ['xcodebuild', '-version']), ('swift', ['swift', '--version'])]}
    # Refuse to run even the fixture tests if this host does not enforce the
    # requested network boundary. A refused connection is not a denied socket.
    probe = '''import errno, socket
try:
    with socket.socket() as sock:
        sock.settimeout(1)
        sock.connect(("127.0.0.1", 9))
except OSError as error:
    if error.errno not in (errno.EPERM, errno.EACCES):
        raise
    print("NETWORK_DENIED")
else:
    raise RuntimeError("Network boundary not enforced")
'''
    guard, guard_text = command_log('network-guard', ['/usr/bin/sandbox-exec', '-p', SANDBOX, sys.executable, '-c', probe])
    if guard['exit_code'] != 0 or guard_text.strip() != 'NETWORK_DENIED':
        raise RuntimeError('Network boundary control failed; tests were not started')
    build, _ = command_log('build', ['swift', 'build', *prefix, '--force-resolved-versions', '--build-tests', '--jobs', '4'], timeout=900)
    results = []
    binary_hash = None
    if build['exit_code'] == 0:
        listed = subprocess.check_output(['swift', 'test', *prefix, 'list', '--skip-build', '--disable-swift-testing'], env=env, text=True).splitlines()
        selectors = [f'{args.package}Tests.{cls}/{method}' for cls, method, _ in cases]
        if any(listed.count(selector) != 1 for selector in selectors):
            raise RuntimeError('Required diagnostic test absent or duplicated in actual discovery')
        binary_dir = Path(subprocess.check_output(['swift', 'build', *prefix, '--show-bin-path'], env=env, text=True).strip())
        bundles = list(binary_dir.glob('*.xctest'))
        if len(bundles) != 1:
            raise RuntimeError('Expected exactly one host XCTest bundle')
        bundle = bundles[0]
        binary_hash = digest(bundle/'Contents/MacOS'/bundle.stem)
        for cls, method, flag in cases:
            selector = f'{args.package}Tests.{cls}/{method}'
            runs = {}
            for mode, expected, test_env in [('control', 'skipped', env), ('enabled', 'passed', environment(os.environ, flag))]:
                command = ['/usr/bin/sandbox-exec', '-p', SANDBOX, '/usr/bin/xcrun', 'xctest', '-XCTest', selector, str(bundle)]
                run, text = command_log(cls+'-'+mode, command, test_env)
                run.update(status=outcome(text, run['exit_code'], cls, method, args.package), expected=expected)
                runs[mode] = run
            results.append(dict(selector=selector, flag=flag, source_sha256=digest(package/'Tests'/(args.package+'Tests')/(cls+'.swift')), **runs))
    require_source_state(source, sha)
    if (resolved.read_bytes() if resolved.exists() else None) != pins:
        raise RuntimeError('Package dependency pins changed')
    success = build['exit_code'] == 0 and len(results) == len(cases) and all(r[mode]['status'] == expected for r in results for mode, expected in [('control','skipped'),('enabled','passed')])
    result = dict(check='diagnostic-modes' if args.package == 'OathAnkr' else 'diagnostic-trace-mode', package=args.package, source_commit=sha, status='passed' if success else 'failed',
        duration_seconds=round(time.monotonic()-started, 3), toolchain=toolchain, network_guard=guard, build=build, cases=results,
        tests_passed=sum(r['enabled']['status']=='passed' for r in results),
        controls_skipped=sum(r['control']['status']=='skipped' for r in results),
        package_resolved_sha256=hashlib.sha256(pins).hexdigest() if pins is not None else None, test_binary_sha256=binary_hash,
        sandbox_profile=SANDBOX, runtime_scope='macOS host; separate fresh XCTest processes; network denied during test execution; synthetic fixtures and in-memory diagnostic sinks; package build may download public dependencies')
    (out/'diagnostic-modes.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
