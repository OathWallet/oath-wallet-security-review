#!/usr/bin/env python3
"""Fetch pinned native-build archives, verify hashes, then extract locally."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request
import zipfile

INPUTS = [
    ('src/gtest/googletest-1.16.0.tar.gz',
     'https://github.com/google/googletest/releases/download/v1.16.0/googletest-1.16.0.tar.gz',
     '78c676fc63881529bf97bf9d45948d905a66833fbfa5318ea2cd7478cb98f399'),
    ('src/check/check-0.15.2.tar.gz',
     'https://github.com/libcheck/check/releases/download/0.15.2/check-0.15.2.tar.gz',
     'a8de4e0bacfb4d76dd1c618ded263523b53b85d92a146d8835eb1a52932fa20a'),
    ('src/protobuf/protobuf-java-3.20.3.tar.gz',
     'https://github.com/protocolbuffers/protobuf/releases/download/v3.20.3/protobuf-java-3.20.3.tar.gz',
     'aa109c630d85a3ef625d69344a83e72bf3d58df034db8d099c95c51f01cde20e'),
    ('json/include.zip',
     'https://github.com/nlohmann/json/releases/download/v3.11.3/include.zip',
     'a22461d13119ac5c78f205d3df1db13403e58ce1bb1794edc9313677313f4a9d'),
]


def prepare(prefix):
    rows = []
    for relative, url, expected in INPUTS:
        archive = prefix/relative
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Download hash mismatch: '+relative)
            archive.write_bytes(data)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise ValueError('Cached archive hash mismatch: '+relative)
        if archive.suffix == '.zip':
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    if not (prefix/name).resolve().is_relative_to(prefix.resolve()):
                        raise ValueError('Archive path escapes prefix')
                z.extractall(prefix)
        else:
            with tarfile.open(archive) as t:
                t.extractall(archive.parent, filter='data')
        rows.append(dict(path=relative, url=url, sha256=expected))
    (prefix/'verified-inputs.json').write_text(json.dumps(rows, indent=2)+'\n')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path, help='The prepared Core checkout build/local directory')
    args = parser.parse_args()
    print(json.dumps(prepare(args.prefix.resolve()), indent=2))
