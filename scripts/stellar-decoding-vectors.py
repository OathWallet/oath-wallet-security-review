#!/usr/bin/env python3
"""Deterministic synthetic Stellar vectors using Python stdlib primitives, not app helpers."""
import base64
import binascii
import hashlib
import json
from pathlib import Path
import struct
import sys
SEED = 'oath-stellar-decoding-v1'
NETWORK = 'Public Global Stellar Network ; September 2015'
TEST_NETWORK = 'Test SDF Network ; September 2015'
def u32(n): return struct.pack('>I', n)
def blob(i): return hashlib.sha256(f'{SEED}:{i}'.encode()).digest()
def strkey(raw, version):
    payload = bytes([version]) + raw
    return base64.b32encode(payload + struct.pack('<H', binascii.crc_hqx(payload, 0))).decode().rstrip('=')
def b64(raw): return base64.b64encode(raw).decode()
def text(s):
    raw=s.encode(); return u32(15)+u32(len(raw))+raw+bytes((-len(raw))%4)
def amount(n): return u32(10)+n.to_bytes(16,'big',signed=True)
def generate():
    addresses=[];contracts=[];amounts=[];maps=[];events=[]
    codes=['A','USD','USDC','TOKEN','ABCDEFGHIJKL','a0B9','x1y2Z3']
    for i in range(64):
        raw=blob(i); account=strkey(raw,48); contract=strkey(raw,16)
        damaged=bytearray(bytes([48])+raw);damaged+=struct.pack('<H',binascii.crc_hqx(damaged,0));damaged[34]^=1
        addresses.append({'bytes':list(raw),'account':account,'contract':contract,'bad_checksum':base64.b32encode(damaged).decode(),'sc_account':b64(u32(18)+u32(0)+u32(0)+raw),'sc_contract':b64(u32(18)+u32(1)+raw),'sc_muxed':b64(u32(18)+u32(2)+struct.pack('>Q',i)+raw)})
        code=codes[i%len(codes)];size=4 if len(code)<=4 else 12
        asset=u32(1 if size==4 else 2)+code.encode().ljust(size,b'\0')+u32(0)+raw
        for network in [NETWORK,TEST_NETWORK]:
            preimage=u32(8)+hashlib.sha256(network.encode()).digest()+u32(1)+asset
            contracts.append({'code':code,'issuer':account,'network':network,'contract':strkey(hashlib.sha256(preimage).digest(),16)})
    values=[0,1,127,128,255,256,2**32-1,2**64-1,2**64,2**127-1]+[int.from_bytes(blob(100+i)[:16],'big')>>1 for i in range(118)]
    for i,n in enumerate(values):
        decimals=[0,1,6,7,18,38,255][i%7]
        digits=str(n).rjust(decimals+1,'0'); display=digits if not decimals else digits[:-decimals]+'.'+digits[-decimals:]
        amounts.append({'integer':str(n),'decimal':display,'decimals':decimals,'xdr':b64(amount(n)),'negative_xdr':b64(amount(-n)),'negative':str(-n)})
        if i<24:
            for variant in range(3):
                memo=u32(5)+struct.pack('>Q',i) if variant==0 else u32(13 if variant==1 else 14)+u32(3)+b'abc\0'
                entries=[text('amount')+amount(n),text('to_muxed_id')+memo]
                maps.append({'xdr':b64(u32(17)+u32(1)+u32(2)+b''.join(entries)),'amount':str(n)})
    owner=addresses[0]['account'];other=addresses[1]['account']
    native=strkey(hashlib.sha256(u32(8)+hashlib.sha256(NETWORK.encode()).digest()+u32(1)+u32(0)).digest(),16)
    for kind in ['transfer','mint','burn','clawback','fee']:
        for successful in [True,False]:
            for n in ([100,-7] if kind=='fee' else [100]):
                topics=[b64(text(kind)),addresses[0]['sc_account']]
                if kind=='transfer':topics.append(addresses[1]['sc_account'])
                events.append({'owner':owner,'expected_amount':str(n),'accepted':successful or kind=='fee','direction':'incoming' if kind=='mint' else 'outgoing','row':{'id':f'{kind}-{successful}-{n}','contractId':native,'topic':topics,'value':b64(amount(n)),'inSuccessfulContractCall':successful,'txHash':'ab'*32,'ledger':123,'ledgerClosedAt':'2026-01-01T00:00:00Z'}})
    malformed=[b64(u32(0xffffffff)+blob(i)*((i%8)+1)) for i in range(256)]
    return {'seed':SEED,'addresses':addresses,'contracts':contracts,'amounts':amounts,'maps':maps,'events':events,'malformed':malformed,'native_contract':native,'other_owner':other}
if __name__=='__main__':
    Path(sys.argv[1]).write_text(json.dumps(generate(),sort_keys=True,indent=2)+'\n')
