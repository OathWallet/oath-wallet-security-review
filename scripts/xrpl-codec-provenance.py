#!/usr/bin/env python3
"""Rebuild the shipped XRP codec and inventory its exact bundled input closure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from source_state import require_source_state

COMMIT='8a31eb265c34ef7f37ba21741201842366d43b7b'
SOURCE='Tools/WalletConnectXrplCodec'
BUNDLE='Packages/OathAnkr/Sources/OathAnkr/Resources/XrplCodec.js'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source','scratch','output']: p.add_argument(name,type=Path)
    a=p.parse_args(); source=a.source.resolve();scratch=a.scratch.resolve();out=a.output.resolve()
    require_source_state(source,COMMIT)
    scratch.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    sdk=scratch/'sdk';sdk.mkdir(exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','LANG','LC_ALL']}
    env['npm_config_update_notifier']='false'
    versions={name:subprocess.check_output([name,'--version'],env=env,text=True).strip() for name in ['node','npm']}
    if versions!={'node':'v26.5.0','npm':'11.17.0'}:raise ValueError('Unexpected Node/npm toolchain')
    for name in ['package.json','package-lock.json','index.js']: shutil.copyfile(source/SOURCE/name,sdk/name)
    start=time.monotonic()
    def run(cmd,name):
        with (out/name).open('w') as f: result=subprocess.run(cmd,cwd=sdk,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
        if result.returncode: raise RuntimeError(name+' failed; original log retained')
    run(['npm','ci','--ignore-scripts','--no-audit','--no-fund','--cache',str(scratch/'npm-cache')],'npm.log')
    esbuild=sdk/'node_modules/.bin/esbuild'
    versions['esbuild']=subprocess.check_output([str(esbuild),'--version'],env=env,text=True).strip()
    if versions['esbuild']!='0.25.12':raise ValueError('Unexpected bundler')
    run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',str(esbuild),'index.js',
         '--bundle','--platform=browser','--format=iife','--global-name=OathXrplCodec','--target=safari17','--minify',
         '--outfile='+str(out/'XrplCodec.js'),'--banner:js=var window = globalThis;','--metafile='+str(out/'meta.json')],'build.log')
    meta=json.loads((out/'meta.json').read_text());lock=json.loads((sdk/'package-lock.json').read_text())['packages'];inputs=[];packages={}
    if len(meta['outputs']) != 1:raise ValueError('Unexpected output count')
    output_inputs=next(iter(meta['outputs'].values()))['inputs']
    for name,info in sorted(meta['inputs'].items()):
        path=sdk/name
        if not path.is_file() or not path.resolve().is_relative_to(sdk): raise ValueError('Unbounded compiler input')
        package=None
        if name.startswith('node_modules/'):
            parent=path.parent
            while parent!=sdk and not (parent/'package.json').exists(): parent=parent.parent
            if parent==sdk:raise ValueError('No package identity for input')
            relative=str(parent.relative_to(sdk));record=json.loads((parent/'package.json').read_text());pin=lock[relative]
            if record['version']!=pin['version']:raise ValueError('Installed version differs from lock')
            package=relative
            packages[relative]={'name':record['name'],'version':record['version'],'license':record.get('license'),
                                'integrity':pin.get('integrity'),'resolved':pin.get('resolved'),
                                'manifest_sha256':sha(parent/'package.json'),'review_status':'outstanding'}
        inputs.append({'path':name,'bytes':path.stat().st_size,'sha256':sha(path),'package':package,
                       'bytes_in_output':output_inputs.get(name,{}).get('bytesInOutput',0),'review_status':'outstanding'})
    if not inputs or not packages:raise ValueError('Empty closure')
    same=(out/'XrplCodec.js').read_bytes()==(source/BUNDLE).read_bytes()
    result={'source_commit':COMMIT,'toolchain':versions,'lock_sha256':sha(sdk/'package-lock.json'),
            'entry_sha256':sha(sdk/'index.js'),'shipped_bundle_sha256':sha(source/BUNDLE),'rebuilt_bundle_sha256':sha(out/'XrplCodec.js'),
            'byte_identical':same,'inputs':inputs,'packages':packages,'duration_seconds':round(time.monotonic()-start,2),
            'script_sha256':sha(Path(__file__)),'build_network':'denied; installation is separate',
            'scope':'Reproducible bundle and dependency input/license inventory, not a manual review of all upstream implementations'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    require_source_state(source,COMMIT)
    if not same:raise ValueError('Rebuilt bundle differs from shipped bytes')
    print('Byte-identical bundle;',len(inputs),'inputs;',len(packages),'dependency packages')

if __name__=='__main__':main()
