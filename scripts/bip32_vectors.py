"""Independent SLIP-0010 HMAC/integer oracle; public synthetic fixtures only."""
import json, hashlib, hmac
orders={'secp256k1':int('fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141',16),'nist256p1':int('ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551',16)}
keys={'secp256k1':b'Bitcoin seed','nist256p1':b'Nist256p1 seed','ed25519':b'ed25519 seed','curve25519':b'curve25519 seed','ed25519-blake2b-nano':b'ed25519 seed'}
def master(seed,curve):
 raw=hmac.digest(keys[curve],seed,'sha512')
 while curve in orders and not 0<int.from_bytes(raw[:32],'big')<orders[curve]:raw=hmac.digest(keys[curve],raw,'sha512')
 return raw[:32],raw[32:]
def child(priv,chain,index,curve):
 assert index>=2**31
 raw=hmac.digest(chain,b'\0'+priv+index.to_bytes(4,'big'),'sha512')
 if curve in orders:
  n=orders[curve];parent=int.from_bytes(priv,'big')
  while int.from_bytes(raw[:32],'big')>=n or (int.from_bytes(raw[:32],'big')+parent)%n==0:
   raw=hmac.digest(chain,b'\1'+raw[32:]+index.to_bytes(4,'big'),'sha512')
  priv=((int.from_bytes(raw[:32],'big')+parent)%n).to_bytes(32,'big')
 else:priv=raw[:32]
 return priv,raw[32:]
def generate(official, out):
 # Anchor this independently written oracle to the official roots and all-hardened paths,
 # including the NIST retry vectors; non-hardened official paths go directly to C.
 anchors=0
 for row in official:
  parts=row['path'].split('/')[1:]
  if any(not p.endswith("'") for p in parts):continue
  priv,chain=master(bytes.fromhex(row['seed']),row['curve'])
  for p in parts:priv,chain=child(priv,chain,2**31+int(p[:-1]),row['curve'])
  assert priv.hex()==row['private'] and chain.hex()==row['chain code'];anchors+=1
 rows=[]
 for i in range(64):
  seed=hashlib.sha512(b'Oath public SLIP10 synthetic fixture v1'+i.to_bytes(4,'big')).digest()[:[16,32,64][i%3]]
  indices=[0x80000000,0xffffffff,0x80000001,0xfffffffe,0x80000000|int.from_bytes(hashlib.sha256(seed).digest()[:4],'big')]
  for curve in keys:
   priv,chain=master(seed,curve);path=[]
   for depth in range(6):
    rows.append(dict(curve=curve,seed=seed.hex(),indices=path[:],private=priv.hex(),chain=chain.hex()))
    if depth<5:
     path.append(indices[depth]);priv,chain=child(priv,chain,indices[depth],curve)
 (out/'oracle-vectors.json').write_text(json.dumps({'oracle':'Python hmac/hashlib and modular integer addition, independent of Trezor implementation','anchor_count':anchors,'rows':rows},indent=2)+'\n')
 def inds(path):return [int(p.rstrip("'"))+(2**31 if p.endswith("'") else 0) for p in path.split('/')[1:]]
 header='struct Vector {const char *curve,*seed,*priv,*chain,*pub; unsigned depth; uint32_t indices[5];};\nstatic const struct Vector official[] = {\n'
 for row in official:
  path=inds(row['path']);header+='{'+','.join(json.dumps(row[k]) for k in ['curve','seed','private','chain code','public'])+','+str(len(path))+',{'+(','.join(str(i)+'u' for i in path) or '0')+'}},\n'
 header+='};\nstatic const struct Vector oracle[] = {\n'
 for row in rows:
  path=row['indices'];header+='{'+','.join(json.dumps(row[k]) for k in ['curve','seed','private','chain'])+',"",'+str(len(path))+',{'+(','.join(str(i)+'u' for i in path) or '0')+'}},\n'
 header+='};\n';(out/'bip32-vectors.h').write_text(header)
 return {'official':len(official),'independent_hardened':len(rows),'oracle_anchors':anchors}
