#!/usr/bin/env python3
"""Host-only macOS XCTest isolation with explicit skipped-test evidence."""
import argparse, concurrent.futures, hashlib, json, re, subprocess, time
import xml.etree.ElementTree as ET
from pathlib import Path


def classify(output, exit_code):
    # Do not accept an empty selection as a pass. Swift's parallel xUnit output
    # omits XCTSkip on this toolchain, so retain each real XCTest process log.
    started = re.findall(r"^Test Case '.+' started\.$", output, re.M)
    skipped = re.findall(r"^Test Case '.+' skipped \(", output, re.M)
    passed = re.findall(r"^Test Case '.+' passed \(", output, re.M)
    if exit_code != 0 or len(started) != 1:
        return 'failed'
    if len(skipped) == 1 and not passed:
        return 'skipped'
    if len(passed) == 1 and not skipped:
        return 'passed'
    return 'failed'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('package')
    p.add_argument('scratch', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--skip-build', action='store_true')
    p.add_argument('--filter')
    a = p.parse_args()
    source, out = a.source.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prefix = ['--package-path', str(source/'Packages'/a.package), '--build-system', 'native', '--scratch-path', str(a.scratch.resolve())]
    if not a.skip_build:
        subprocess.run(['swift', 'build', *prefix, '--build-tests', '--jobs', '4'], check=True)
    listed = subprocess.check_output(['swift', 'test', *prefix, 'list', '--skip-build', '--disable-swift-testing'], text=True)
    selectors = [x for x in listed.splitlines() if x.strip()]
    if any(not re.fullmatch(r'[\w.]+/\w+', x) for x in selectors):
        raise SystemExit('Unexpected test selector listing; refusing incomplete discovery')
    if a.filter:
        selectors = [s for s in selectors if re.search(a.filter, s)]
        if not selectors: raise SystemExit('Empty requested test selection')
    results = []
    if selectors:
        binary_dir = Path(subprocess.check_output(['swift', 'build', *prefix, '--show-bin-path'], text=True).strip())
        bundles = list(binary_dir.glob('*.xctest'))
        if len(bundles) != 1: raise SystemExit('Expected exactly one package test bundle')
        logs = out/(a.package+'-cases'); logs.mkdir(exist_ok=True)
        def run(case):
            started = time.monotonic()
            command = ['xcrun', 'xctest', '-XCTest', case, str(bundles[0])]
            try:
                r = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
                text, code = r.stdout, r.returncode
            except subprocess.TimeoutExpired as e:
                text = (e.stdout or b'').decode(errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or '')
                text += '\nAUDIT TEST TIMEOUT\n'; code = -1
            text = text.replace(str(source), '<SOURCE>')
            log = logs/(hashlib.sha256(case.encode()).hexdigest()[:16]+'.log')
            log.write_text(text)
            return dict(selector=case, status=classify(text, code), exit_code=code,
                        duration_seconds=round(time.monotonic()-started, 3),
                        log=str(log.relative_to(out)), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(run, selectors))
    suite = ET.Element('testsuite', name=a.package, tests=str(len(results)),
                       failures=str(sum(r['status']=='failed' for r in results)),
                       skipped=str(sum(r['status']=='skipped' for r in results)))
    for r in results:
        cls, name = r['selector'].split('/',1)
        el=ET.SubElement(suite,'testcase',classname=cls,name=name,time=str(r['duration_seconds']))
        if r['status']=='skipped': ET.SubElement(el,'skipped',message='XCTSkip; see retained process log')
        if r['status']=='failed': ET.SubElement(el,'failure',message='Test failed, timed out or selected no case; see process log')
    ET.ElementTree(suite).write(out/(a.package+'.xml'), encoding='utf-8', xml_declaration=True)
    (out/(a.package+'-cases.json')).write_text(json.dumps(results,indent=2)+'\n')
    print(f"XCTest: {len(results)} selected; {sum(r['status']=='passed' for r in results)} passed; {sum(r['status']=='skipped' for r in results)} skipped; {sum(r['status']=='failed' for r in results)} failed",flush=True)
    # Swift Testing has a separate runner. Preserve its own summary and XML,
    # rather than assuming the XCTest list covers it.
    command=['swift','test',*prefix,'--skip-build','--disable-xctest','--xunit-output',str(out/(a.package+'-swift-testing.xml'))]
    if a.filter: command += ['--filter', a.filter]
    r = subprocess.run(command, stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=600)
    (out/(a.package+'-swift-testing.log')).write_text(r.stdout.replace(str(source),'<SOURCE>'))
    print(r.stdout,flush=True)
    swift_count = max([int(n) for n in re.findall(r'Test run with (\d+) tests?', r.stdout)] or [0])
    empty = not results and swift_count == 0
    if empty: print('No XCTest or Swift Testing cases executed; refusing an empty pass', flush=True)
    raise SystemExit(1 if r.returncode or empty or any(x['status']=='failed' for x in results) else 0)

if __name__=='__main__': main()
