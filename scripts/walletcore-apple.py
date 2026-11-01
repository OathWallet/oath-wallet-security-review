#!/usr/bin/env python3
"""Build unsigned repaired Core Apple archives from pinned public inputs.

Start with the documented native preparation. Output must be a new directory;
this script never writes into the supplied Core/native/runtime source trees.
It compiles generic targets and never boots a simulator or accesses a device.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
CORE = 'd40d24a63d92619167903369308bf0e2f7eb3a59'
GENERATOR = '7e2c5f3cbbeea68e004915e3a8961e20bd11d824'
RUNTIME = 'd72aed98f8253ec1aa9ea1141e28150f408cf17f'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inventory(root):
    return [dict(path=str(p.relative_to(root)), sha256=digest(p), bytes=p.stat().st_size)
            for p in sorted(root.rglob('*')) if p.is_file() and not p.name.startswith('._')]

def archive_tree(source, destination, prefix):
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in sorted(source.rglob('*')):
            if p.is_symlink():
                raise ValueError('Unexpected framework symlink: '+str(p))
            if p.name.startswith('._') or p.is_dir():
                continue
            entry = zipfile.ZipInfo(prefix+'/'+str(p.relative_to(source)), (2026,1,1,0,0,0))
            entry.create_system = 3
            entry.external_attr = (p.stat().st_mode & 0xFFFF) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, p.read_bytes())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source','native','generator','runtime','rustup-home','cargo-home','output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--repair-set', choices=['seven', 'eight'], default='seven')
    a = parser.parse_args()
    source, native, generator, runtime, rustup, cargo, output = [p.resolve() for p in [a.source,a.native,a.generator,a.runtime,a.rustup_home,a.cargo_home,a.output]]
    require_source_state(source, CORE)
    require_source_state(generator, GENERATOR)
    require_source_state(runtime, RUNTIME)
    patch = ROOT/('patches/walletcore-4.8.4-combined-'+a.repair_set+'.patch')
    expected = patch.read_bytes()
    def check_native():
        if subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip() != CORE:
            raise ValueError('Wrong native source revision')
        if subprocess.check_output(['git','-C',str(native),'diff','HEAD','--binary']) != expected:
            raise ValueError('Native source must have exactly the selected repair set')
        if subprocess.check_output(['git','-C',str(native),'ls-files','--others','--exclude-standard']).strip():
            raise ValueError('Unexpected native source inputs')
    check_native()
    generated = json.loads((ROOT/'scope/walletcore-generated-inputs.json').read_text())['files']
    for row in generated:
        if digest(native/row['path']) != row['sha256']:
            raise ValueError('Generated input differs: '+row['path'])
    if output.exists():
        raise ValueError('Output must be a new disposable directory')
    output.mkdir(parents=True)
    logs = output/'evidence'; logs.mkdir()
    commands = []
    env = {k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL','DEVELOPER_DIR','USER','LOGNAME']}
    env.update(RUSTUP_HOME=str(rustup),CARGO_HOME=str(cargo),CARGO_BUILD_JOBS='4',RUSTFLAGS='-Zlocation-detail=none')
    env['PATH'] = str(cargo/'bin')+os.pathsep+env.get('PATH','/usr/bin:/bin')
    env['CARGO_TARGET_DIR'] = str(output/'rust-target')
    def run(command, name, cwd=None, timeout=3600):
        started = time.monotonic()
        log = logs/(name+'.log')
        with log.open('w') as stream:
            code, expired = logged_command(command,stream=stream,timeout=timeout,cwd=cwd,env=env)
        commands.append(dict(name=name,command=command,exit_code=code,timed_out=expired,duration_seconds=round(time.monotonic()-started,3),log_sha256=digest(log)))
        (logs/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        print(name,code,flush=True)
        if code or expired:
            raise RuntimeError(name+' failed; evidence retained')
        return log.read_text()
    versions = {}
    for command,name,required in [(['xcodebuild','-version'],'xcode','Xcode 27.0'),(['xcodegen','--version'],'xcodegen','2.45.4'),([str(native/'build/local/bin/protoc'),'--version'],'protoc','libprotoc 3.20.3'),([str(cargo/'bin/cargo'),'+nightly-2025-12-11','--version'],'cargo','cargo')]:
        value = run(command,'version-'+name,timeout=60)
        if required not in value:
            raise ValueError('Unexpected '+name+' toolchain')
        versions[name] = value.strip()
    work = output/'source'
    run(['git','clone','--no-hardlinks','--no-checkout',str(source),str(work)],'clone',timeout=180)
    run(['git','checkout','--detach',CORE],'checkout',cwd=work,timeout=180)
    run(['git','apply',str(patch)],'apply',cwd=work,timeout=60)
    shutil.copytree(native/'build/local',work/'build/local',ignore=shutil.ignore_patterns('._*'))
    prefix_inventory = inventory(work/'build/local')
    (logs/'native-prefix-inputs.json').write_text(json.dumps(prefix_inventory,indent=2)+'\n')
    for row in generated:
        target = work/row['path']; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(native/row['path'],target)
    # Build the pinned Swift generator in the disposable output, not its checkout.
    run(['swift','build','--package-path',str(generator),'--scratch-path',str(output/'generator-build'),'-c','release','--product','protoc-gen-swift','--jobs','4'],'swift-generator',timeout=900)
    plugin = output/'generator-build/release/protoc-gen-swift'
    swift_out = work/'swift/Sources/Generated/Protobuf'; swift_out.mkdir(parents=True,exist_ok=True)
    protos = sorted((work/'src/proto').glob('*.proto'))
    run([str(work/'build/local/bin/protoc'),'-I'+str(work/'build/local/include'),'-I'+str(work/'src/proto'),'--plugin=protoc-gen-swift='+str(plugin),'--swift_out='+str(swift_out),'--swift_opt=Visibility=Public']+[str(p) for p in protos],'swift-protobuf',timeout=180)
    for p in swift_out.glob('*.swift'):
        p.write_text(p.read_text().replace('import SwiftProtobuf','import WalletCoreSwiftProtobuf').replace('SwiftProtobuf.','WalletCoreSwiftProtobuf.'))
    (logs/'swift-generated-inputs.json').write_text(json.dumps(inventory(swift_out),indent=2)+'\n')
    run([str(cargo/'bin/rustup'),'component','add','rust-src','--toolchain','nightly-2025-12-11'],'rust-src',timeout=600)
    run([str(cargo/'bin/cargo'),'+nightly-2025-12-11','build','--locked','-Z','build-std=std,panic_abort','--target','aarch64-apple-ios','--target','aarch64-apple-ios-sim','--target','x86_64-apple-ios','--release','--lib'],'rust-apple',cwd=work/'rust',timeout=1800)
    sim_library = output/'rust-simulator.a'
    run(['lipo','-create',str(output/'rust-target/aarch64-apple-ios-sim/release/libwallet_core_rs.a'),str(output/'rust-target/x86_64-apple-ios/release/libwallet_core_rs.a'),'-output',str(sim_library)],'rust-lipo',timeout=60)
    run(['xcodebuild','-create-xcframework','-library',str(output/'rust-target/aarch64-apple-ios/release/libwallet_core_rs.a'),'-library',str(sim_library),'-output',str(work/'swift/WalletCoreRs.xcframework')],'rust-xcframework',timeout=180)
    spec = json.loads(run(['xcodegen','dump','--spec',str(work/'swift/project.yml'),'--type','json'],'upstream-project',cwd=work/'swift',timeout=60))
    spec['name'] = 'OathReviewedWalletCore'
    target = spec['targets']['WalletCore']
    target.pop('postCompileScripts',None)
    target['dependencies'].append({'target':'WalletCoreSwiftProtobuf'})
    spec['targets']['WalletCoreSwiftProtobuf'] = dict(type='framework',platform='iOS',deploymentTarget='15.0',sources=[dict(path=str(runtime/'Sources/SwiftProtobuf'),includes=['**/*.swift'])],dependencies=[dict(target='WalletCoreSwiftProtobufResources')],settings=dict(PRODUCT_MODULE_NAME='WalletCoreSwiftProtobuf',SWIFT_VERSION='5.0',BUILD_LIBRARY_FOR_DISTRIBUTION=True,SKIP_INSTALL=False,GENERATE_INFOPLIST_FILE=True),scheme={})
    spec['targets']['WalletCoreSwiftProtobufResources'] = dict(type='bundle',platform='iOS',deploymentTarget='15.0',sources=[dict(path=str(runtime/'Sources/SwiftProtobuf/PrivacyInfo.xcprivacy'),buildPhase='resources')],settings=dict(PRODUCT_NAME='WalletCoreSwiftProtobuf',GENERATE_INFOPLIST_FILE=True))
    project = logs/'apple-project.json';project.write_text(json.dumps(spec,indent=2)+'\n')
    run(['xcodegen','generate','--spec',str(project),'--project-root',str(work/'swift'),'--project',str(work/'swift')],'generate-project',timeout=60)
    for variant,destination,platform in [('ios','generic/platform=iOS','iphoneos'),('simulator','generic/platform=iOS Simulator','iphonesimulator')]:
        derived = output/('build-'+variant); archive = output/(variant+'.xcarchive')
        run(['xcodebuild','archive','-project',str(work/'swift/OathReviewedWalletCore.xcodeproj'),'-scheme','WalletCore','-configuration','Release','-destination',destination,'-archivePath',str(archive),'-derivedDataPath',str(derived),'-jobs','4','CODE_SIGNING_ALLOWED=NO','SKIP_INSTALL=NO','IPHONEOS_DEPLOYMENT_TARGET=15.0'],'archive-'+variant,cwd=work,timeout=3600)
        frameworks = archive/'Products/Library/Frameworks'
        shutil.copyfile(work/'swift/PrivacyInfo.xcprivacy',frameworks/'WalletCore.framework/PrivacyInfo.xcprivacy')
        resource = derived/('Build/Intermediates.noindex/ArchiveIntermediates/WalletCore/IntermediateBuildFilesPath/UninstalledProducts/'+platform+'/WalletCoreSwiftProtobuf.bundle')
        if digest(resource/'PrivacyInfo.xcprivacy') != digest(runtime/'Sources/SwiftProtobuf/PrivacyInfo.xcprivacy'):
            raise ValueError('Privacy resource mismatch')
        shutil.copytree(resource,frameworks/'WalletCoreSwiftProtobuf.framework/WalletCoreSwiftProtobuf.bundle')
    products = output/'artifacts';products.mkdir()
    for name in ['WalletCore','WalletCoreSwiftProtobuf']:
        command = ['xcodebuild','-create-xcframework']
        for variant in ['ios','simulator']:
            archive = output/(variant+'.xcarchive')
            command += ['-framework',str(archive/'Products/Library/Frameworks'/(name+'.framework')),'-debug-symbols',str(archive/'dSYMs'/(name+'.framework.dSYM'))]
        command += ['-output',str(products/(name+'.xcframework'))]
        run(command,'package-'+name,timeout=180)
        archive_tree(products/(name+'.xcframework'),products/(name+'.xcframework.zip'),name+'.xcframework')
        archive_tree(output/'ios.xcarchive/dSYMs'/(name+'.framework.dSYM'),products/(name+'.xcframework.dSYM.zip'),name+'.dSYMs/'+name+'.framework.ios-arm64.dSYM')
    require_source_state(source,CORE);require_source_state(generator,GENERATOR);require_source_state(runtime,RUNTIME);check_native()
    if subprocess.check_output(['git','diff','HEAD','--binary'],cwd=work) != expected:
        raise ValueError('Apple source changed during build')
    for row in generated:
        if digest(native/row['path']) != row['sha256']:
            raise ValueError('Native generated input changed during build')
    if inventory(work/'build/local') != prefix_inventory:
        raise ValueError('Native tool/dependency prefix changed during build')
    result = dict(status='passed',upstream_commit=CORE,generator_commit=GENERATOR,runtime_commit=RUNTIME,patch_sha256=hashlib.sha256(expected).hexdigest(),toolchain=versions,artifacts=inventory(products),runtime_executed=False,limitations=['Unsigned generic archives; no simulator or device launch.','Prepared native inputs are hash-checked; follow the public native recipe to recreate them.','Reproducible commands do not establish byte-for-byte equality or historical App Store equivalence.'])
    (logs/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'passed','artifact_directory':str(products)}))

if __name__ == '__main__':
    main()
