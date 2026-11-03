#!/usr/bin/env python3
"""Explicitly opted-in synthetic rendering of a pinned production privacy cover."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from source_state import require_source_state

PIN = 'c7acd23bb139864a40273f405d18b479589d2b20'
SOURCE = 'OathAtmosphere/Security/OathAppSwitcherPrivacy.swift'
DIGEST = '82dd4d5e8ce0094fd83958c51a7e4986c73115dadcf2a6fcbc2aafe98dbed48a'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('work', type=Path)
    parser.add_argument('--run-simulator', action='store_true')
    args = parser.parse_args()
    if not args.run_simulator:
        parser.error('Simulator execution requires explicit --run-simulator')
    require_source_state(args.source, PIN)
    data = (args.source / SOURCE).read_bytes()
    if hashlib.sha256(data).hexdigest() != DIGEST:
        raise ValueError('Production cover hash differs from the reviewed input')
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).resolve().parents[1] / 'fixtures/privacy-cover'
    harness = work / 'Harness'
    sources = harness / 'Sources'
    sources.mkdir(parents=True)
    shutil.copyfile(fixture / 'project.yml', harness / 'project.yml')
    shutil.copyfile(fixture / 'Main.swift', sources / 'Main.swift')
    (sources / 'OathAppSwitcherPrivacy.swift').write_bytes(data)
    devices = work / 'devices'
    devices.mkdir()
    captures = work / 'captures'
    captures.mkdir()

    def run(argv, name, cwd=None, timeout=120):
        with (work / (name + '.log')).open('ab') as log:
            result = subprocess.run([str(x) for x in argv], cwd=cwd,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=timeout)
            log.write(result.stdout)
        result.check_returncode()
        return result.stdout.decode().strip()

    run(['xcodegen', 'generate'], 'generate', cwd=harness)
    run(['xcodebuild', 'build', '-project', harness / 'PrivacyCoverProbe.xcodeproj',
         '-scheme', 'PrivacyCoverProbe', '-configuration', 'Debug',
         '-destination', 'generic/platform=iOS Simulator', '-derivedDataPath', work / 'build',
         'CODE_SIGNING_ALLOWED=NO'], 'build', timeout=900)
    sim = ['xcrun', 'simctl', '--set', devices]
    device = run(sim + ['create', 'Oath synthetic privacy probe',
                       'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro',
                       'com.apple.CoreSimulator.SimRuntime.iOS-27-0'], 'create')
    try:
        run(sim + ['boot', device], 'boot')
        run(sim + ['bootstatus', device, '-b'], 'bootstatus', timeout=300)
        app = work / 'build/Build/Products/Debug-iphonesimulator/PrivacyCoverProbe.app'
        run(sim + ['install', device, app], 'install')
        run(sim + ['launch', device, 'org.oath.audit.privacyprobe'], 'launch')
        container = Path(run(sim + ['get_app_container', device, 'org.oath.audit.privacyprobe', 'data'], 'container'))
        docs = container / 'Documents'
        deadline = time.monotonic() + 30
        while not (docs / 'result.txt').exists():
            if time.monotonic() >= deadline:
                raise TimeoutError('Probe did not finish its captures')
            time.sleep(0.25)
        if (docs / 'result.txt').read_text() != 'completed':
            raise ValueError('Unexpected completion marker')
        for name in ('uncovered.png', 'covered-light.png', 'covered-dark.png', 'result.txt'):
            shutil.copyfile(docs / name, captures / name)
        run(sim + ['io', device, 'screenshot', captures / 'compositor-dark.png'], 'compositor')
        run(['swift', fixture / 'OCR.swift', captures], 'ocr', timeout=120)
        result = dict(source_commit=PIN, source_sha256=DIGEST, runtime='iOS 27.0',
                      device_type='iPhone 17 Pro', synthetic_only=True,
                      scope='Settled cover rendering, not app-switcher snapshot timing',
                      files={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in captures.iterdir() if p.is_file()})
        (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    finally:
        try:
            run(sim + ['shutdown', device], 'shutdown')
        finally:
            run(sim + ['delete', device], 'delete')


if __name__ == '__main__':
    main()
