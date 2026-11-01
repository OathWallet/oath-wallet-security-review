#!/usr/bin/env python3
"""Compare every BDK binary package member to the artifact used by Xcode."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

PIN = '5e7f8ac46306f9de7ec2cc1c6486d9db5141c793d33cc13071ea7d1e3dae817f'
PREFIX = 'bdkFFI.xcframework/'

def digest(stream):
    return hashlib.file_digest(stream, 'sha256').hexdigest()

def compare(archive, resolved):
    with archive.open('rb') as stream:
        checksum = digest(stream)
    if checksum != PIN:
        raise ValueError('BDK archive SHA-256 differs from its package pin')
    disk = {path.relative_to(resolved).as_posix(): path for path in resolved.rglob('*') if path.is_file()}
    checked = {}
    with ZipFile(archive) as package:
        for member in package.infolist():
            if member.is_dir():
                continue
            if not member.filename.startswith(PREFIX):
                raise ValueError(f'Unexpected archive member {member.filename}')
            name = member.filename[len(PREFIX):]
            if name not in disk or name in checked or disk[name].is_symlink():
                raise ValueError(f'Unexpected or duplicate framework member {name}')
            with package.open(member) as stream, disk[name].open('rb') as built:
                actual = digest(stream)
                if actual != digest(built):
                    raise ValueError(f'Xcode bytes differ at {name}')
            checked[name] = actual
    if not checked or set(checked) != set(disk):
        raise ValueError('BDK framework member set differs')
    return dict(archive_sha256=checksum, archive_bytes=archive.stat().st_size, members=checked,
                scope='Distribution archive matches every regular file in the resolved framework. Rust source to binary and App Store executable equivalence remain unproven.')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('archive','framework','output'):
        p.add_argument(key, type=Path)
    a=p.parse_args()
    result=compare(a.archive, a.framework)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"Verified {len(result['members'])} framework members")
