#!/usr/bin/env python3
"""Isolate unchanged upstream constructor bodies with their actual class layout."""
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

ROOT = Path(__file__).resolve().parents[1]
PIN = 'd40d24a63d92619167903369308bf0e2f7eb3a59'


def constructor_slice(text):
    start = text.index('const int MnemonicBufLength')
    end = text.index('template <size_t seedSize>\nstatic HDNode getMasterNode')
    return text[start:end], text[:start].count('\n')+1, text[:end].count('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path); p.add_argument('--app-source',required=True,type=Path)
    p.add_argument('--app-commit',required=True); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); source=a.source.resolve(); app=a.app_source.resolve(); out=a.output.resolve()
    require_source_state(source,PIN); require_source_state(app,a.app_commit)
    ruby=subprocess.check_output(['ruby','--version'],text=True).strip()
    if not ruby.startswith('ruby 4.0.5 '): raise ValueError('Ruby 4.0.5 required')
    out.mkdir(parents=True,exist_ok=True); started=time.monotonic(); commands=[]
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    env.update(ASAN_OPTIONS='halt_on_error=1:detect_leaks=0', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    def run(command,name,cwd=None,required=True):
        with (out/(name+'.log')).open('w') as log:
            code,timeout=logged_command(command,stream=log,timeout=120,cwd=cwd,env=env)
        commands.append(dict(name=name,command=command,exit_code=code,timed_out=timeout))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if required and code: raise RuntimeError(name+' failed; logs retained')
        return code,timeout
    body,first,last=constructor_slice((source/'src/HDWallet.cpp').read_text())
    fixture=ROOT/'tests/UpstreamHDWalletConstructors.cpp'
    c_names=['bip39.c','sha2.c','hmac.c','pbkdf2.c','memzero.c','rand.c']
    with tempfile.TemporaryDirectory(prefix='oath-hdwallet-') as temp:
        work=Path(temp)
        shutil.copytree(source/'codegen',work/'codegen'); shutil.copytree(source/'include',work/'include')
        shutil.copyfile(source/'registry.json',work/'registry.json'); (work/'docs').mkdir()
        (work/'rust/tw_coin_registry/src').mkdir(parents=True)
        shutil.copyfile(source/'rust/tw_coin_registry/src/tw_derivation.rs',work/'rust/tw_coin_registry/src/tw_derivation.rs')
        run(['ruby','codegen/bin/coins'],'headers',cwd=work)
        translation='#include "HDWallet.h"\n#include "Mnemonic.h"\n#include "memory/memzero_wrapper.h"\n#include <TrezorCrypto/bip39.h>\n#include <algorithm>\n#include <cstring>\nusing namespace TW;\n'
        translation+=f'#line {first} "{source}/src/HDWallet.cpp"\n'+body+'\nnamespace TW { template class HDWallet<32>; template class HDWallet<64>; }\n'
        (work/'Constructors.cpp').write_text(translation)
        flags=['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(source/'trezor-crypto/include')]
        objects=[]
        for i,name in enumerate(c_names):
            obj=work/f'c{i}.o';objects.append(str(obj))
            run(['clang','-std=c11']+flags+['-c',str(source/'trezor-crypto/crypto'/name),'-o',str(obj)],f'c-{i}')
        cxx=['clang++','-std=c++17']+flags+['-I',str(source/'src'),'-I',str(work/'include')]
        cases=[]
        for mode in ['assertions','release']:
            obj=work/(mode+'.o')
            run(cxx+(['-DNDEBUG'] if mode=='release' else [])+['-c',str(work/'Constructors.cpp'),'-o',str(obj)],mode+'-compile')
            binary=work/mode
            run(cxx+[str(fixture),str(obj),str(source/'src/Mnemonic.cpp')]+objects+['-Wl,-dead_strip','-o',str(binary)],mode+'-link')
            for case in ['positive','mnemonic32','entropy32','entropy-lifetime']:
                name=mode+'-'+case
                code,timeout=run([str(binary)]+([] if case=='positive' else [case]),name,required=False)
                log=(out/(name+'.log')).read_text()
                if case=='positive': observed=code==0 and log.strip()=='CONSTRUCTOR_OK checks=22'
                elif case=='entropy-lifetime': observed=code==0 and log.strip()=='ENTROPY_DEALLOCATION retained_public_fixture=1 bytes=16'
                elif mode=='assertions': observed=code!=0 and 'entropy.size() > 10' in log
                else: observed=code==1 and not log.strip()
                cases.append(dict(configuration=mode,case=case,exit_code=code,timed_out=timeout,observed=observed and not timeout,
                                  classification='positive-constructor-checks' if case=='positive' else 'unrepaired-api-characterization'))
    require_source_state(source,PIN);require_source_state(app,a.app_commit)
    paths=['src/HDWallet.cpp','src/HDWallet.h','src/Mnemonic.cpp','src/Mnemonic.h','src/Data.h','src/memory/memzero_wrapper.h']+['trezor-crypto/crypto/'+n for n in c_names]
    result=dict(check='upstream-constructors',source_commit=a.app_commit,upstream_commit=PIN,
                status='passed' if all(c['observed'] for c in cases) else 'failed',cases=cases,
                duration_seconds=round(time.monotonic()-started,3),ruby=ruby,
                compiler=subprocess.check_output(['clang++','--version'],text=True),
                source_hashes={path:hashlib.sha256((source/path).read_bytes()).hexdigest() for path in paths},
                extraction=dict(start_line=first,end_line=last,sha256=hashlib.sha256(body.encode()).hexdigest(),
                                qualification='Exact contiguous production constructor/destructor bodies and real class header; unrelated methods not compiled.'),
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                log_sha256=hashlib.sha256((out/'assertions-positive.log').read_bytes()).hexdigest(),
                limitations=['Expected failures are not fixes.', '32-byte mnemonic constructor not established reachable in Oath.',
                             'Deallocation observer reads synthetic entropy before free, not attacker-accessible memory.', 'Not a full upstream build or binary-equivalence proof.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Constructor checks:',result['status'],'; positive checks=22 in each of two configurations; API characterizations retained')
    return 0 if result['status']=='passed' else 1


if __name__=='__main__': raise SystemExit(main())
