#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <TrezorCrypto/bip32.h>
#include <TrezorCrypto/curves.h>
#include <TrezorCrypto/ed25519-donna/ed25519-blake2b.h>
#include <TrezorCrypto/memzero.h>
#include "bip32-vectors.h"
static unsigned hex(const char *s, unsigned char *out, unsigned capacity) {
 unsigned count=(unsigned)strlen(s)/2;assert(strlen(s)%2==0&&count<=capacity);
 for(unsigned i=0;i<count;i++){unsigned v;assert(sscanf(s+2*i,"%2x",&v)==1);out[i]=(unsigned char)v;}return count;
}
static unsigned public_pairs=0;
static void check(const struct Vector *v, unsigned number, int known) {
 unsigned char seed[64],expected[33];unsigned length=hex(v->seed,seed,sizeof(seed));HDNode node;
 assert(hdnode_from_seed(seed,(int)length,v->curve,&node)==1);
 for(unsigned i=0;i<v->depth;i++){
  HDNode public_node=node;int eligible=node.curve->params && !(v->indices[i]&0x80000000u);
  if(eligible){assert(hdnode_fill_public_key(&public_node)==0);memzero(public_node.private_key,32);}
  assert(hdnode_private_ckd(&node,v->indices[i])==1);
  if(eligible){assert(hdnode_public_ckd(&public_node,v->indices[i])==1);assert(hdnode_fill_public_key(&node)==0);assert(memcmp(node.public_key,public_node.public_key,33)==0);assert(memcmp(node.chain_code,public_node.chain_code,32)==0);public_pairs++;}
 }
 hex(v->priv,expected,sizeof(expected));if(memcmp(node.private_key,expected,32)){fprintf(stderr,"private mismatch vector=%u known=%d curve=%s\n",number,known,v->curve);assert(0);}
 hex(v->chain,expected,sizeof(expected));assert(memcmp(node.chain_code,expected,32)==0);
 assert(node.depth==v->depth);assert(node.child_num==(v->depth?v->indices[v->depth-1]:0));
 if(v->pub[0]){
  hex(v->pub,expected,sizeof(expected));assert(hdnode_fill_public_key(&node)==0);
  // SLIP-0010 uses a 00 serialization prefix for 25519 keys; Trezor uses
  // 01 internally to mark a populated cached key. Compare the 32 key bytes.
  if(node.curve->params){assert(memcmp(node.public_key,expected,33)==0);}
  else {assert(expected[0]==0&&node.public_key[0]==1);assert(memcmp(node.public_key+1,expected+1,32)==0);}
 }
 memzero(&node,sizeof(node));memzero(seed,sizeof(seed));memzero(expected,sizeof(expected));
}
int main(int argc,char **argv) {
 if(argc==2 && strcmp(argv[1],"unknown-curve")==0){HDNode node;return hdnode_deserialize_private("invalid",0x0488ade4u,"not-a-curve",&node,NULL)==0;}
 if(argc==2 && strcmp(argv[1],"nano-public")==0){
  for(unsigned n=0;n<64;n++){
   unsigned char seed[16]={0}, expected[32];seed[0]=(unsigned char)n;HDNode node;
   assert(hdnode_from_seed(seed,16,"ed25519-blake2b-nano",&node));
   assert(hdnode_fill_public_key(&node)==0);unsigned any=0;for(unsigned i=1;i<33;i++)any|=node.public_key[i];assert(any!=0);
   // Dispatch regression against the separate primitive used by PrivateKey.
   // This is not an independent proof of the primitive's cryptography.
   ed25519_publickey_blake2b(node.private_key,expected);
   assert(node.public_key[0]==1&&memcmp(node.public_key+1,expected,32)==0);
   assert(hdnode_fill_public_key(&node)==0&&memcmp(node.public_key+1,expected,32)==0);
  }return 0;
 }
 if(argc==2 && strcmp(argv[1],"curve-guards")==0){
  HDNode node;assert(hdnode_deserialize_public("invalid",0x0488b21eu,NULL,&node,NULL)!=0);
  assert(hdnode_deserialize_private("invalid",0x0488ade4u,NULL,&node,NULL)!=0);
  memset(&node,0,sizeof(node));assert(hdnode_fill_public_key(&node)!=0);assert(node.public_key[0]==0);
  curve_info unsupported={0};node.curve=&unsupported;
  assert(hdnode_fill_public_key(&node)!=0);assert(node.public_key[0]==0);return 0;
 }
 for(unsigned i=0;i<sizeof(official)/sizeof(*official);i++)check(official+i,i,1);
 for(unsigned i=0;i<sizeof(oracle)/sizeof(*oracle);i++)check(oracle+i,i,0);
 unsigned char seed[32]={1};HDNode node,before;
 assert(hdnode_from_seed(seed,32,ED25519_NAME,&node)==1);before=node;
 assert(hdnode_private_ckd(&node,0)==0);assert(memcmp(&node,&before,sizeof(node))==0);
 assert(hdnode_private_ckd(&node,0x7fffffffu)==0);assert(memcmp(&node,&before,sizeof(node))==0);
 assert(hdnode_from_seed(seed,32,"unknown",&node)==0);
 uint32_t state=0x4f415448u;char malformed[129];unsigned accepted=0;
 for(unsigned i=0;i<10000;i++){
  unsigned len=i%128;
  for(unsigned j=0;j<len;j++){state^=state<<13;state^=state>>17;state^=state<<5;malformed[j]=(char)(33+state%94);}malformed[len]=0;
  accepted+=hdnode_deserialize_public(malformed,0x0488b21eu,SECP256K1_NAME,&node,NULL)==0;
  accepted+=hdnode_deserialize_private(malformed,0x0488ade4u,SECP256K1_NAME,&node,NULL)==0;
 }
 assert(accepted==0);
 printf("BIP32_OK official=52 independent_hardened=1920 public_private_pairs=%u malformed_calls=20000 unsupported_child_unchanged=2\n",public_pairs);
}
