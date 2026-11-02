#!/usr/bin/env python3
"""Rebuild the four public scalar-oracle P2PKH expectations checked by the package tests."""
from pathlib import Path
import argparse,json,runpy,hmac,hashlib
crypto=runpy.run_path(str(Path(__file__).with_name('utxo-recovery-vectors.py')))
def script(coin):
 d=hmac.digest(b'Bitcoin seed',bytes(range(32)),'sha512');k=int.from_bytes(d[:32],'big');c=d[32:]
 for index in [2**31+44,2**31+coin,2**31,0,2**31-1]:
  key=b'\0'+k.to_bytes(32,'big') if index>=2**31 else crypto['point'](k)
  d=hmac.digest(c,key+index.to_bytes(4,'big'),'sha512');t=int.from_bytes(d[:32],'big');assert t<crypto['N'];k=(k+t)%crypto['N'];assert k;c=d[32:]
 return '76a914'+hashlib.new('ripemd160',hashlib.sha256(crypto['point'](k)).digest()).hexdigest()+'88ac'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path,help='Pinned public app checkout')
    args=parser.parse_args()
    fixture=(args.source/'Packages/OathBitcoin/Tests/OathBitcoinTests/BitcoinKeysTests.swift').read_text()
    for chain,coin in [('bitcoin',0),('bitcoincash',145),('dogecoin',3),('litecoin',2)]:
        expected=script(coin)
        assert fixture.count('.'+chain+': "'+expected+'"')==1,chain
        print(chain,expected)
