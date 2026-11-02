#!/usr/bin/env python3
"""Regenerate the actual C tables and check their points using independent affine arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from source_state import require_source_state

PACKAGE = 'e70a10e036a55fffea31568f0af92d69b6d449cd'
SECP_TAG_OBJECT = '833ca65c66b6e97b86489807103ca6e187ab25aa'
UPSTREAM = {'secp256k1': '1a53f4961f337b4d166c25fce72ef0dc88806618',
            'secp256k1-zkp': '08d1cd0c9c35a5a151ba80c226d49ea949e90374',
            'swift-crypto': '1b6b2e274e85105bfa155183145a1dcfd63331f1'}
P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
CONFIGS = [(2, 5, 26), (11, 6, 4), (43, 6, 1)]

def add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    x, y = a
    u, v = b
    if x == u:
        if (y + v) % P == 0:
            return None
        slope = 3*x*x * pow(2*y, -1, P)
    else:
        slope = (v-y) * pow(u-x, -1, P)
    new_x = (slope*slope - x - u) % P
    return new_x, (slope*(x-new_x) - y) % P

def multiple(scalar, powers):
    point = None
    scalar %= N
    while scalar:
        bit = scalar & -scalar
        point = add(point, powers[bit.bit_length()-1])
        scalar -= bit
    return point

def entries(text):
    for row in re.findall(r'\bS\(([0-9a-f,]+)\)', text):
        parts = row.split(',')
        if len(parts) != 16 or any(not 1 <= len(p) <= 8 for p in parts):
            raise ValueError('Invalid coordinate encoding')
        data = ''.join(p.zfill(8) for p in parts)
        yield int(data[:64], 16), int(data[64:], 16)

def verify_math(odd_file, comb_file):
    powers = [G]
    for _ in range(255):
        powers.append(add(powers[-1], powers[-1]))
    odd = iter(entries(odd_file.read_text()))
    for base in [G, powers[128]]:
        point = base
        stride = add(base, base)
        for _ in range(8192):
            if next(odd) != point:
                raise ValueError('Incorrect odd multiple')
            point = add(point, stride)
    if next(odd, None) is not None:
        raise ValueError('Extra odd multiples')
    comb = comb_file.read_text()
    groups = re.split(r'^#elif \(COMB_BLOCKS == (\d+)\) && \(COMB_TEETH == (\d+)\) && \(COMB_SPACING == (\d+)\)\s*$', comb, flags=re.M)
    configs = [tuple(map(int, groups[i:i+3])) for i in range(1, len(groups), 4)]
    if configs != CONFIGS:
        raise ValueError('Unexpected generator configurations')
    count = 0
    for i, (blocks, teeth, spacing) in enumerate(configs):
        points = iter(entries(groups[4*(i+1)]))
        for block in range(blocks):
            weights = [pow(2, (block*teeth + t)*spacing, N) for t in range(teeth)]
            offset = -sum(weights) * pow(2, -1, N)
            for index in range(1 << (teeth-1)):
                scalar = offset + sum(value for t, value in enumerate(weights) if index & (1 << t))
                if multiple(scalar, powers) != next(points):
                    raise ValueError('Unexpected signed-comb point')
                count += 1
        if next(points, None) is not None:
            raise ValueError('Extra comb points')
    return {'odd_multiples': 16384, 'signed_comb_points': count, 'configurations': configs}

def tree(source, revision):
    raw = subprocess.check_output(['git','-C',source,'ls-tree','-rz',revision])
    result = {}
    for entry in raw.split(b'\0'):
        if entry:
            metadata, name = entry.split(b'\t', 1)
            result[name.decode()] = metadata.decode()
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['package','secp','zkp','swift_crypto','output']:
        parser.add_argument(name,type=Path)
    args = parser.parse_args()
    pkg = args.package.resolve()
    upstreams = dict(zip(UPSTREAM,[args.secp.resolve(),args.zkp.resolve(),args.swift_crypto.resolve()],strict=True))
    require_source_state(pkg, PACKAGE)
    comparisons = {}
    files = {}
    with tempfile.TemporaryDirectory(prefix='secp-tables-') as tmp:
        work = Path(tmp)
        for name, upstream in upstreams.items():
            require_source_state(upstream, UPSTREAM[name])
            if name == 'secp256k1':
                commit = subprocess.check_output(['git','-C',upstream,'rev-parse',SECP_TAG_OBJECT+'^{commit}'],text=True).strip()
                if commit != UPSTREAM[name]:
                    raise ValueError('Annotated upstream tag does not resolve to the pinned commit')
            tracked = tree(pkg, 'HEAD:Vendor/'+name)
            canonical = tree(upstream,'HEAD')
            changed = sorted(k for k in tracked.keys() & canonical.keys() if tracked[k]!=canonical[k])
            comparisons[name] = dict(commit=UPSTREAM[name], identical=len(tracked.keys() & canonical.keys())-len(changed),
                                     modified=changed, package_only=sorted(tracked.keys()-canonical.keys()),
                                     upstream_only=sorted(canonical.keys()-tracked.keys()))
            if name == 'swift-crypto':
                continue
            output = work/name
            (output/'src').mkdir(parents=True)
            for suffix in ['ecmult','ecmult_gen']:
                binary = output/('generate-'+suffix)
                rel = 'src/precomputed_'+suffix+'.c'
                generator = upstream/('src/precompute_'+suffix+'.c')
                subprocess.run(['cc','-O2',generator,'-o',binary],check=True,timeout=90)
                subprocess.run([binary],cwd=output,check=True,timeout=90)
                reference = (output/rel).read_bytes()
                for path in ['Vendor/'+name+'/'+rel, 'Sources/'+('libsecp256k1' if name=='secp256k1' else 'libsecp256k1_zkp')+'/'+rel]:
                    if (pkg/path).read_bytes()!=reference:
                        raise ValueError('Regeneration did not match '+path)
                    files[path] = hashlib.sha256(reference).hexdigest()
        math_results=verify_math(work/'secp256k1/src/precomputed_ecmult.c',work/'secp256k1/src/precomputed_ecmult_gen.c')
        for suffix in ['ecmult','ecmult_gen']:
            normal = files['Vendor/secp256k1/src/precomputed_'+suffix+'.c']
            fork = files['Vendor/secp256k1-zkp/src/precomputed_'+suffix+'.c']
            if normal != fork:
                raise ValueError('Fork tables differ and require their own arithmetic check')
    for name, source in upstreams.items():
        require_source_state(source, UPSTREAM[name])
    require_source_state(pkg, PACKAGE)
    result=dict(check='secp-table-provenance',status='passed',package_commit=PACKAGE,secp_tag_object=SECP_TAG_OBJECT,upstream_trees=comparisons,
                vendor_and_package_files=files,arithmetic=math_results,compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],
                scope='Git object IDs include file modes. Source identity does not validate implementations. Arithmetic checks cover the two distinct generated tables; the fork and package copies match those bytes.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(math_results)
    for name,c in comparisons.items():
        print(name,c['identical'],'identical entries;',len(c['modified']),'modified;',len(c['package_only']),'package-only;',len(c['upstream_only']),'upstream-only')

if __name__=='__main__':
    main()
