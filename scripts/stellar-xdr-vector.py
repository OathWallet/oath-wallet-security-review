#!/usr/bin/env python3
"""Regenerate the independent public test vector without Swift or Stellar SDK code."""
import hashlib, json, struct, subprocess
def words(*values): return struct.pack('>'+'I'*len(values),*values)
def vector():
    # RFC 8410 PKCS#8 prefix followed by the 32-byte repeated-value test seed.
    spki=subprocess.run(['openssl','pkey','-inform','DER','-pubout','-outform','DER'],input=bytes.fromhex('302e020100300506032b657004220420')+bytes([7])*32,capture_output=True,check=True).stdout
    if not spki.startswith(bytes.fromhex('302a300506032b6570032100')) or len(spki)!=44: raise ValueError('Unexpected Ed25519 public key encoding')
    pub=spki[-32:]
    tx=words(0)+pub+words(100,0,42,0,0,1,0,24,0,1)+bytes([4])*32+words(1)+b'f\0\0\0'+words(1)+words(16,1,1)*2+words(1,0,0)
    network=hashlib.sha256(b'Test SDF Network ; September 2015').digest()
    return dict(network='stellar:testnet',synthetic_seed='32 bytes each equal to 7',public_key_hex=pub.hex(),
        envelope_hex=(words(2)+tx+words(0)).hex(),signature_payload_hash=hashlib.sha256(network+words(2)+tx).hexdigest())
if __name__=='__main__':print(json.dumps(vector(),indent=2))
