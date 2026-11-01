#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <TrezorCrypto/bip39.h>
#include "mnemonic-vectors.h"

static unsigned calls;
static void progress(uint32_t current,uint32_t total) {
 assert(total==2048 && current==calls*128);calls++;
}
static size_t decode(const char *hex,uint8_t *out,size_t capacity) {
 size_t n=strlen(hex)/2;assert(strlen(hex)%2==0 && n<=capacity);
 for(size_t i=0;i<n;i++){unsigned v;assert(sscanf(hex+2*i,"%2x",&v)==1);out[i]=(uint8_t)v;}return n;
}
static uint64_t state=UINT64_C(0x4f41544842495039);
static uint32_t next(void){state^=state<<13;state^=state>>7;state^=state<<17;return (uint32_t)state;}
int main(void) {
 const size_t count=sizeof(vectors)/sizeof(vectors[0]);
 for(size_t i=0;i<count;i++) {
  const struct Vector *v=&vectors[i];uint8_t entropy[32],expected[64];char password[4097]={0};
  size_t n=decode(v->entropy,entropy,sizeof entropy);decode(v->password,(uint8_t*)password,sizeof password-1);assert(decode(v->seed,expected,sizeof expected)==64);
  struct {uint8_t before[16];char output[240];uint8_t after[16];} words;
  memset(&words,0xa5,sizeof words);
  assert(mnemonic_from_data(entropy,(int)n,words.output,sizeof words.output)==words.output);
  assert(strcmp(words.output,v->mnemonic)==0);assert(mnemonic_check(words.output));
  for(size_t j=0;j<16;j++){assert(words.before[j]==0xa5 && words.after[j]==0xa5);}
  struct {uint8_t before[16];uint8_t output[33];uint8_t after[16];} bits;
  memset(&bits,0xa5,sizeof bits);assert(mnemonic_to_bits(v->mnemonic,bits.output)==(int)(n*8+n/4));assert(memcmp(bits.output,entropy,n)==0);
  for(size_t j=0;j<16;j++){assert(bits.before[j]==0xa5 && bits.after[j]==0xa5);}
  struct {uint8_t before[16];uint8_t output[64];uint8_t after[16];} seed;
  memset(&seed,0xa5,sizeof seed);calls=0;mnemonic_to_seed(v->mnemonic,password,seed.output,progress);
  assert(calls==17 && memcmp(seed.output,expected,64)==0);
  for(size_t j=0;j<16;j++){assert(seed.before[j]==0xa5 && seed.after[j]==0xa5);}
  // Changing checksum index by one is not guaranteed invalid. Mutate an
  // existing word to a non-dictionary spelling instead.
  char invalid[300];snprintf(invalid,sizeof invalid,"x%s",v->mnemonic);assert(!mnemonic_check(invalid));
 }
 for(int i=-1;i<=2048;i++) {
  const char *word=mnemonic_get_word(i);
  if(i<0||i>=2048){assert(word==NULL);continue;}
  assert(word && mnemonic_find_word(word)==i);
  assert(mnemonic_complete_word(word,(int)strlen(word))!=NULL);
  assert(mnemonic_word_completion_mask(word,(int)strlen(word))<=0x3ffffff);
 }
 uint8_t entropy[32]={0},bits[33];char output[240];
 for(int n=-2;n<=34;n++) {
  const char *r=mnemonic_from_data(entropy,n,output,sizeof output);
  assert((r!=NULL)==(n>=16&&n<=32&&n%4==0));
 }
 for(int n=0;n<240;n++){memset(output,0xa5,sizeof output);assert(mnemonic_from_data(entropy,16,output,n)==NULL);for(size_t i=0;i<sizeof output;i++)assert((unsigned char)output[i]==0xa5);}
 assert(mnemonic_from_data(entropy,16,NULL,240)==NULL);assert(mnemonic_to_bits(NULL,bits)==0);assert(!mnemonic_check(NULL));
 for(int strength=-1;strength<=257;strength++) {
  if(strength>=128&&strength<=256&&strength%32==0)continue;
  assert(mnemonic_generate(strength,output,sizeof output)==NULL);
 }
 // Bounded malformed ASCII parser corpus: valid allocations and terminators,
 // not undefined C API invocations with invalid pointers or unterminated data.
 for(int sample=0;sample<20000;sample++) {
  char input[1025];size_t n=next()%1025;
  for(size_t i=0;i<n;i++){uint32_t v=next()%30;input[i]=v<26?(char)('a'+v):' ';}input[n]=0;
  struct{uint8_t pre[16],bits[33],post[16];} guarded;memset(&guarded,0xa5,sizeof guarded);
  int result=mnemonic_to_bits(input,guarded.bits);assert(result==0||result==132||result==165||result==198||result==231||result==264);
  (void)mnemonic_check(input);
  for(size_t i=0;i<16;i++)assert(guarded.pre[i]==0xa5&&guarded.post[i]==0xa5);
 }
 // Historical API behavior is recorded, not fixed or recommended: bytes past
 // 256 and bytes after an embedded NUL are not included by this C API.
 char longPass[258];memset(longPass,'p',257);longPass[257]=0;
 uint8_t a[64],b[64];mnemonic_to_seed(vectors[0].mnemonic,longPass,a,NULL);
 longPass[256]=0;mnemonic_to_seed(vectors[0].mnemonic,longPass,b,NULL);assert(memcmp(a,b,64)==0);
 char nulPass[4]={'p',0,'x',0};mnemonic_to_seed(vectors[0].mnemonic,nulPass,a,NULL);
 mnemonic_to_seed(vectors[0].mnemonic,"p",b,NULL);assert(memcmp(a,b,64)==0);
 puts("UPSTREAM_MNEMONIC_OK vectors=150 malformed=20000 words=2048 truncation_characterized=2");
 return 0;
}
