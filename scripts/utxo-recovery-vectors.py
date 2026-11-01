#!/usr/bin/env python3
"""Independent synthetic BIP32/BIP44 reference using OpenSSL's secp256k1."""
import hashlib,hmac,json,struct,subprocess
N=0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
def point(scalar):
    der=bytes.fromhex('302e0201010420')+scalar.to_bytes(32,'big')+bytes.fromhex('a00706052b8104000a')
    pub=subprocess.run(['openssl','ec','-inform','DER','-pubout','-outform','DER','-conv_form','compressed'],input=der,capture_output=True,check=True).stdout
    prefix=bytes.fromhex('3036301006072a8648ce3d020106052b8104000a032200')
    if not pub.startswith(prefix) or len(pub)!=len(prefix)+33:raise ValueError('Unexpected compressed-point SPKI')
    return pub[-33:]
def b58(data):
    encoded=data+hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    number=int.from_bytes(encoded,'big');out=''
    while number:
        number,digit=divmod(number,58)
        out='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'[digit]+out
    return '1'*(len(encoded)-len(encoded.lstrip(b'\0')))+out
def generate():
    root=point(1)[1:];out={}
    for name,coin,version in [('bitcoin',0,0x0488ade4),('bitcoincash',145,0x0488ade4),('dogecoin',3,0x02fac398),('litecoin',2,0x019d9cfe)]:
        s=int.from_bytes(root,'big');code=bytes([7])*32
        for i in [44|2**31,coin|2**31,2**31,0,0]:
            key=b'\0'+s.to_bytes(32,'big') if i>=2**31 else point(s)
            digest=hmac.digest(code,key+struct.pack('>I',i),'sha512');t=int.from_bytes(digest[:32],'big');s=(s+t)%N
            if t>=N or s==0:raise ValueError('Invalid vector branch')
            code=digest[32:]
        script=b'\x76\xa9\x14'+hashlib.new('ripemd160',hashlib.sha256(point(s)).digest()).digest()+b'\x88\xac'
        wire=struct.pack('>I',version)+bytes(9)+bytes([7])*32
        out[name]=dict(script=script.hex(),legacy=b58(wire+b'\x02'+root),canonical=b58(wire+b'\0'+root))
    return out
if __name__=='__main__':print(json.dumps(generate(),indent=2))
