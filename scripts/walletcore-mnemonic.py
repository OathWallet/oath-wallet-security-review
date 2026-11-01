#!/usr/bin/env python3
"""Compile pinned production BIP39 C with ASan/UBSan and independent seed vectors."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from bounded_process import logged_command
from source_state import require_source_state

ROOT = Path(__file__).resolve().parents[1]
PIN = 'd40d24a63d92619167903369308bf0e2f7eb3a59'
SOURCES = ['bip39.c', 'sha2.c', 'hmac.c', 'pbkdf2.c', 'memzero.c', 'rand.c']

def make_vectors(words):
    if len(words) != 2048 or len(set(words)) != 2048:
        raise ValueError('Invalid wordlist')
    rows = []
    for length in [16,20,24,28,32]:
        for pattern in [0, 0x7f, 0x80, 0xff, None]:
            entropy = bytes([pattern]*length) if pattern is not None else bytes(range(length))
            checksum = hashlib.sha256(entropy).digest()[0] >> (8-length//4)
            bits = (int.from_bytes(entropy, 'big') << (length//4)) | checksum
            n = length*3//4
            mnemonic = ' '.join(words[(bits >> (11*(n-i-1))) & 2047] for i in range(n))
            for password in ['', 'TREZOR', ' leading and trailing ', 'é', '㍍ガバヴァぱばぐゞちぢ十人十色', 'p'*256]:
                normalized = unicodedata.normalize('NFKD', password).encode()
                seed = hashlib.pbkdf2_hmac('sha512', mnemonic.encode(), b'mnemonic'+normalized, 2048, 64)
                rows.append(dict(entropy=entropy.hex(), mnemonic=mnemonic, password=normalized.hex(), seed=seed.hex()))
    assert len(rows)==150
    assert rows[0]['mnemonic']==' '.join(['abandon']*11+['about'])
    assert rows[1]['seed']=='c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04'
    return rows

def make_kdf_vectors():
    """Independent Python/OpenSSL oracle, including binary and block boundaries."""
    rows = []
    lengths = [0, 1, 31, 32, 63, 64, 65, 127, 128, 129, 256]
    for algorithm in ['sha256', 'sha512']:
        for keylen in lengths:
            key = bytes(i % 256 for i in range(keylen))
            for msglen in lengths:
                message = bytes((i * 17 + 3) % 256 for i in range(msglen))
                rows.append(dict(kind=0, algorithm=algorithm, key=key.hex(), message=message.hex(),
                                 rounds=0, expected=hmac.digest(key, message, algorithm).hex()))
        for keylen in [0, 1, 64, 65, 128, 129]:
            key = bytes(i % 256 for i in range(keylen))
            salt = bytes((i * 19) % 256 for i in range(keylen + 1))
            for rounds in [1, 2, 129]:
                for size in [1, 31, 32, 33, 63, 64, 65, 129]:
                    rows.append(dict(kind=1, algorithm=algorithm, key=key.hex(), message=salt.hex(),
                                     rounds=rounds, expected=hashlib.pbkdf2_hmac(algorithm, key, salt, rounds, size).hex()))
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--app-source',required=True,type=Path);p.add_argument('--app-commit',required=True);args=p.parse_args()
    source=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if not subprocess.check_output(['ruby','--version'],text=True).startswith('ruby 4.0.5 '):
        raise ValueError('Ruby 4.0.5 is required for pinned upstream header generation')
    require_source_state(source,PIN)
    app=args.app_source.resolve();require_source_state(app,args.app_commit)
    wordfile=source/'trezor-crypto/include/TrezorCrypto/bip39_english.h'
    words=re.findall(r'"([a-z]+)"',wordfile.read_text().split('wordlist[] = {', 1)[1])
    rows=make_vectors(words)
    fixture=ROOT/'tests/UpstreamMnemonic.c'
    header='struct Vector { const char *entropy,*mnemonic,*password,*seed; };\nstatic const struct Vector vectors[] = {\n'
    header+='\n'.join('{'+','.join(json.dumps(row[k]) for k in ['entropy','mnemonic','password','seed'])+'},' for row in rows)+'\n};\n'
    (out/'vectors.json').write_text(json.dumps(rows,indent=2)+'\n')
    env={k:v for k,v in os.environ.items() if k in ['HOME','PATH','TMPDIR','DEVELOPER_DIR','LANG','LC_ALL']}
    env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1';env['ASAN_OPTIONS']='halt_on_error=1:detect_leaks=0'
    started=time.monotonic()
    extra_checks=[]
    with tempfile.TemporaryDirectory(prefix='oath-bip39-') as tmp:
        work=Path(tmp);(work/'mnemonic-vectors.h').write_text(header)
        kdf_rows=make_kdf_vectors()
        (out/'kdf-vectors.json').write_text(json.dumps(kdf_rows,indent=2)+'\n')
        kdf_header='struct KDFVector { unsigned kind, bits, rounds; const char *key,*message,*expected; };\nstatic const struct KDFVector kdf_vectors[] = {\n'
        kdf_header+='\n'.join('{'+','.join([str(r['kind']), r['algorithm'][3:], str(r['rounds'])]+[json.dumps(r[k]) for k in ['key','message','expected']])+'},' for r in kdf_rows)+'\n};\n'
        (work/'kdf-vectors.h').write_text(kdf_header)
        command=['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(work),'-I',str(source/'trezor-crypto/include'),str(fixture)]
        command += [str(source/'trezor-crypto/crypto'/name) for name in SOURCES]+['-o',str(work/'mnemonic')]
        with (out/'compile.log').open('w') as log:code,timed_out=logged_command(command,stream=log,timeout=120,env=env)
        run_code=None;run_timeout=False
        if code==0:
            with (out/'run.log').open('w') as log:run_code,run_timeout=logged_command([str(work/'mnemonic')],stream=log,timeout=180,env=env)
        # Generate headers with upstream's own pinned registry/template code in
        # an isolated copy. The source checkout remains unchanged.
        shutil.copytree(source/'codegen',work/'codegen')
        shutil.copytree(source/'include',work/'include')
        shutil.copyfile(source/'registry.json',work/'registry.json')
        (work/'docs').mkdir();(work/'rust/tw_coin_registry/src').mkdir(parents=True)
        shutil.copyfile(source/'rust/tw_coin_registry/src/tw_derivation.rs',work/'rust/tw_coin_registry/src/tw_derivation.rs')
        with (out/'header-generation.log').open('w') as log:
            header_code,header_timeout=logged_command(['ruby','codegen/bin/coins'],cwd=work,stream=log,timeout=60,env=env)
        extra_checks.append(dict(check='upstream-header-generation',status='passed' if header_code==0 else 'failed',exit_code=header_code,timed_out=header_timeout))
        if header_code==0:
            shutil.copyfile(work/'include/TrustWalletCore/TWHRP.h',out/'TWHRP.h')
        boundary_jobs=[
            ('hmac-pbkdf2', ['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(work),'-I',str(source/'trezor-crypto/include'),str(ROOT/'tests/UpstreamKDF.c')]+[str(source/'trezor-crypto/crypto'/s) for s in ['hmac.c','pbkdf2.c','sha2.c','memzero.c']], 'UPSTREAM_KDF_OK hmac=242 pbkdf2=288 zero_round_characterizations=2'),
            ('derivation-path', ['clang++','-std=c++17','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(source/'src'),'-I',str(work/'include'),str(ROOT/'tests/UpstreamDerivationPath.cpp'),str(source/'src/DerivationPath.cpp')], 'UPSTREAM_PATH_OK malformed=20000 fixed_boundary_cases=21'),
            ('passphrase', ['swiftc','-swift-version','6','-parse-as-library',str(app/'Packages/OathCloudBackup/Sources/OathCloudBackup/RecoveryPassphrase.swift'),str(ROOT/'tests/RecoveryPassphraseBoundary.swift')], 'PASSPHRASE_BOUNDARY_OK checks=11')]
        for name,compile_command,marker in boundary_jobs:
            binary=work/name
            with (out/(name+'-compile.log')).open('w') as log:compile_code,compile_timeout=logged_command(compile_command+['-o',str(binary)],stream=log,timeout=120,env=env)
            run_result=None;timeout=False
            if compile_code==0:
                with (out/(name+'.log')).open('w') as log:run_result,timeout=logged_command([str(binary)],stream=log,timeout=60,env=env)
            valid=compile_code==0 and run_result==0 and (out/(name+'.log')).read_text().strip()==marker
            extra_checks.append(dict(check=name,status='passed' if valid else 'failed',compile_exit_code=compile_code,run_exit_code=run_result,timed_out=compile_timeout or timeout))
    require_source_state(source,PIN);require_source_state(app,args.app_commit)
    expected='UPSTREAM_MNEMONIC_OK vectors=150 malformed=20000 words=2048 truncation_characterized=2'
    passed=all(r['status']=='passed' for r in extra_checks) and code==0 and run_code==0 and (out/'run.log').read_text().strip()==expected
    result=dict(check='upstream-mnemonic',upstream_commit=PIN,status='passed' if passed else 'failed',compile_exit_code=code,run_exit_code=run_code,timed_out=timed_out or run_timeout,duration_seconds=round(time.monotonic()-started,2),seed='0x4f41544842495039',vectors=150,malformed_inputs=20000,word_indices=2048,toolchain=subprocess.check_output(['clang','--version'],env=env,text=True).splitlines()[0],python=sys.version,normalization='Python unicodedata NFKD '+unicodedata.unidata_version,runtime_scope='macOS host; C/C++ AddressSanitizer and UndefinedBehaviorSanitizer; Swift passphrase checks without sanitizers; leak detection disabled; not Apple release binary equivalence',source_hashes={str(path.relative_to(source)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [wordfile]+[source/'trezor-crypto/crypto'/s for s in SOURCES]},fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),vectors_sha256=hashlib.sha256((out/'vectors.json').read_bytes()).hexdigest())
    result['source_commit']=args.app_commit
    result['application_commit']=args.app_commit
    result['ruby']=subprocess.check_output(['ruby','--version'],env=env,text=True).strip()
    result['additional_checks']=extra_checks
    result['additional_source_hashes']={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ['src/DerivationPath.cpp','src/DerivationPath.h']}
    result['app_passphrase_sha256']=hashlib.sha256((app/'Packages/OathCloudBackup/Sources/OathCloudBackup/RecoveryPassphrase.swift').read_bytes()).hexdigest()
    result['additional_fixture_hashes']={name:hashlib.sha256((ROOT/'tests'/name).read_bytes()).hexdigest() for name in ['UpstreamKDF.c','UpstreamDerivationPath.cpp','RecoveryPassphraseBoundary.swift']}
    result['kdf_vectors_sha256']=hashlib.sha256((out/'kdf-vectors.json').read_bytes()).hexdigest()
    result['log_sha256']=hashlib.sha256((out/'run.log' if run_code is not None else out/'compile.log').read_bytes()).hexdigest()
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
