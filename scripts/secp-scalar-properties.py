#!/usr/bin/env python3
"""Compare the two packaged secp256k1 scalar implementations with integer arithmetic."""
import argparse
import hashlib
import io
import itertools
import json
import shlex
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PIN = 'e70a10e036a55fffea31568f0af92d69b6d449cd'
N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
LAMBDA = 0x5363ad4cc05c30e0a5261c028812645a122e22ea20816678df02967c1b23bd72
SEED = b'oath-scalar-properties-v1'
TREES = ['libsecp256k1', 'libsecp256k1_zkp']
MODES = ['USE_FORCE_WIDEMUL_INT64','USE_FORCE_WIDEMUL_INT128','USE_FORCE_WIDEMUL_INT128_STRUCT']
WIDTH = 5 + 12*32

def digest(data):
    return hashlib.sha256(data).hexdigest()

def pairs():
    edges = {0,1,N//2,N//2+1,N-2,N-1,N,N+1,2**256-1}
    for bit in range(32,256,32):
        for delta in (-1,0,1):
            edges.add((1<<bit)+delta)
            edges.add(N-(1<<bit)+delta)
    values = list(itertools.product(sorted(edges),repeat=2))
    for index in range(2048):
        block = hashlib.sha512(SEED+index.to_bytes(4,'big')).digest()
        values.append((int.from_bytes(block[:32],'big'), int.from_bytes(block[32:],'big')))
    return values

def verify(records, data):
    if len(data) != len(records)*WIDTH:
        raise ValueError('Incomplete or extra scalar output')
    inverses = {}
    for i,(raw_a, raw_b) in enumerate(records):
        a,b=raw_a%N,raw_b%N
        if a not in inverses:
            inverses[a]=pow(a,-1,N) if a else 0
        row=data[i*WIDTH:(i+1)*WIDTH]
        flags=bytes([raw_a>=N,raw_b>=N,0<raw_a<N,a+b>=N,a>N//2])
        outputs=[int.from_bytes(row[j:j+32],'big') for j in range(5,WIDTH,32)]
        expected=[a,b,(a+b)%N,(a*b)%N,((a+N) if a%2 else a)//2,(-a)%N,inverses[a],inverses[a]]
        r1,r2=outputs[8:10]
        if (row[:5]!=flags or outputs[:8]!=expected or outputs[10:]!=[a*a%N,raw_a%2**64] or max(r1,r2)>=N or
            (r1+LAMBDA*r2)%N!=a or max(min(r1,N-r1),min(r2,N-r2))>=2**128):
            raise ValueError(f'Scalar oracle mismatch at public fixture {i}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('repository',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--cc',default='clang')
    args=p.parse_args()
    records=pairs()
    corpus=b''.join(v.to_bytes(32,'big') for pair in records for v in pair)
    driver=ROOT/'fixtures/secp-scalars/driver.c'
    start=time.monotonic()
    runs=[]
    with tempfile.TemporaryDirectory(prefix='scalar-properties-') as tmp:
        directory=Path(tmp)
        raw=subprocess.check_output(['git','-C',args.repository,'archive',PIN,*['Sources/'+t for t in TREES]])
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(directory,filter='data')
        hashes={}
        for tree in TREES:
            src=directory/'Sources'/tree
            for path in sorted((src/'src').glob('scalar*.h')):
                hashes[str(path.relative_to(directory))]=digest(path.read_bytes())
            for mode in MODES:
                binary=directory/'driver'
                flags=['-std=c11','-O2','-DVERIFY','-D'+mode,'-fsanitize=undefined','-fno-sanitize-recover=undefined']
                if tree=='libsecp256k1_zkp':
                    flags.append('-DOATH_TEST_ZKP')
                deps=directory/'includes.d'
                subprocess.run([args.cc,*flags,'-I',src,'-MMD','-MF',deps,driver,'-o',binary],check=True)
                # Extract only the package inputs from the compiler dependency list.
                includes=shlex.split(deps.read_text().replace(chr(92)+'\n',' ').split(':',1)[1])
                inputs={str(f.relative_to(directory)):digest(f.read_bytes()) for name in includes
                        if (f:=Path(name)).is_relative_to(src)}
                data=subprocess.run([binary],input=corpus,stdout=subprocess.PIPE,check=True,timeout=180).stdout
                verify(records,data)
                runs.append(dict(tree=tree,flags=flags,cases=len(records),output_sha256=digest(data),compiled_package_inputs=inputs))
    if len({r['output_sha256'] for r in runs})!=1:
        raise ValueError('Backends returned different results for the same input stream')
    result=dict(status='passed',package_commit=PIN,seed=SEED.decode(),case_count=len(records),corpus_sha256=digest(corpus),
                harness_sha256=digest(driver.read_bytes()),compiler=subprocess.check_output([args.cc,'--version'],text=True).splitlines()[0],
                runs=runs,scalar_header_hashes=hashes,duration_seconds=round(time.monotonic()-start,2),
                scope='Deterministic host arithmetic and decomposition, with VERIFY and undefined-behavior checks. No constant-time or device-code equivalence claim.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(len(records),'pairs across',len(runs),'compiled configurations')

if __name__=='__main__':
    main()
