#!/usr/bin/env python3
"""Fetch the official ARM macOS Bitcoin Core test binaries and verify two builder attestations."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile

SIGNERS = {
    'fanquake':'E777299FC265DD04793070EB944D35F9AC3DB76A',
    'hebasto':'D1DBF2C4B96F2DEBF4C16654410108112E7EA81F',
}
VERSION='32.1'
ATTESTATIONS='fdc0f9635ca5bee7dd46c51f3bcf3afca83b2d5d'
ARCHIVE='bitcoin-32.1-arm64-apple-darwin.tar.gz'
ARCHIVE_SHA='cd3dcdacb4ff861e862b2d7df4786ecef66472e2468dca1673a70dd761e064e7'

def download(url,path):
    subprocess.run(['curl','--fail','--silent','--show-error','--location','--retry','3',url,'-o',path],check=True,timeout=240)

def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args()
    if platform.system()!='Darwin' or platform.machine()!='arm64': raise RuntimeError('Expected Apple silicon host')
    a.destination.mkdir(parents=True,exist_ok=True);a.evidence.parent.mkdir(parents=True,exist_ok=True)
    origin=f'https://raw.githubusercontent.com/bitcoin-core/guix.sigs/{ATTESTATIONS}'
    records=[]
    with tempfile.TemporaryDirectory(prefix='oath-core-',dir='/tmp') as d:
        d=Path(d); sums=d/'SUMS';sig=d/'signature.asc';key=d/'key.gpg'
        for builder,fingerprint in SIGNERS.items():
            keyring=d/builder;keyring.mkdir(mode=0o700)
            download(f'{origin}/{VERSION}/{builder}/all.SHA256SUMS',sums)
            download(f'{origin}/{VERSION}/{builder}/all.SHA256SUMS.asc',sig)
            download(f'{origin}/builder-keys/{builder}.gpg',key)
            gpg=['gpg','--no-options','--homedir',keyring,'--batch','--no-auto-key-retrieve']
            subprocess.run([*gpg,'--import',key],check=True,capture_output=True)
            result=subprocess.check_output([*gpg,'--status-fd','1','--verify',sig,sums],stderr=subprocess.DEVNULL,text=True)
            fields=[line.split() for line in result.splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
            if len(fields)!=1 or fields[0][-1]!=fingerprint: raise ValueError('Unexpected release signer')
            selected=[line.split() for line in sums.read_text().splitlines() if line.split()[-1:]==[ARCHIVE]]
            if selected!=[[ARCHIVE_SHA,ARCHIVE]]:raise ValueError('Unexpected archive checksum in signed statement')
            records.append(dict(builder=builder,primary_fingerprint=fingerprint,signing_fingerprint=fields[0][2],
                                statement_sha256=hashlib.sha256(sums.read_bytes()).hexdigest()))
        archive=d/ARCHIVE;download(f'https://bitcoincore.org/bin/bitcoin-core-{VERSION}/{ARCHIVE}',archive)
        with archive.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=ARCHIVE_SHA:raise ValueError('Archive mismatch')
        with tarfile.open(archive,'r:gz') as tar:
            for name in ('bitcoin-cli','bitcoind'):
                item=tar.getmember(f'bitcoin-{VERSION}/bin/{name}')
                if not item.isfile(): raise ValueError('Unexpected executable archive entry')
                dst=a.destination/name
                with tar.extractfile(item) as src, dst.open('wb') as out:shutil.copyfileobj(src,out)
                dst.chmod(0o755)
    a.evidence.write_text(json.dumps(dict(version=VERSION,archive=ARCHIVE,sha256=ARCHIVE_SHA,attestations_commit=ATTESTATIONS,signatures=records),indent=2)+'\n')

if __name__=='__main__':main()
