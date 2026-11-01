#include "HDWallet.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
static const void *watched = nullptr;
static bool watched_freed = false, entropy_retained = false;
void *operator new(std::size_t n) { if(void *p=std::malloc(n?n:1)) return p; throw std::bad_alloc(); }
void operator delete(void *p) noexcept {
 if(p && p==watched) { watched_freed=true; auto b=static_cast<const unsigned char*>(p); entropy_retained=true; for(unsigned i=0;i<16;i++) entropy_retained &= b[i]==0x7f; }
 std::free(p);
}
void operator delete(void *p, std::size_t) noexcept { ::operator delete(p); }
static const std::string phrase="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
int main(int argc,char **argv) {
 if(argc==2 && std::strcmp(argv[1],"mnemonic32")==0){TW::HDWallet<32> w(phrase, "TREZOR");return w.getEntropy().empty();}
 if(argc==2 && std::strcmp(argv[1],"entropy32")==0){TW::HDWallet<32> w(TW::Data(16,0), "TREZOR");return w.getEntropy().empty();}
 if(argc==2 && std::strcmp(argv[1],"strength32")==0){TW::HDWallet<32> w(128, "TREZOR");return w.getEntropy().empty();}
 if(argc==2 && std::strcmp(argv[1],"entropy-lifetime")==0){
  auto *w=new TW::HDWallet<64>(TW::Data(16,0x7f), "");watched=w->getEntropy().data();delete w;watched=nullptr;
  assert(watched_freed);printf("ENTROPY_DEALLOCATION retained_public_fixture=%d bytes=16\n",entropy_retained);return entropy_retained?0:1;
 }
 unsigned checks=0;
 for(unsigned n : {32u,64u}){
  TW::Data input(n,0x7f);
  if(n==32){TW::HDWallet<32> w(input);assert(w.getSeed().size()==32&&std::memcmp(w.getSeed().data(),input.data(),32)==0);}
  else{TW::HDWallet<64> w(input);assert(w.getSeed().size()==64&&std::memcmp(w.getSeed().data(),input.data(),64)==0);}
  checks++;
 }
 for(unsigned n : {0u,1u,31u,33u,63u,65u}){
  bool rejected=false;try{TW::HDWallet<32> w(TW::Data(n,0));}catch(const std::invalid_argument&){rejected=true;}assert(rejected);checks++;
  rejected=false;try{TW::HDWallet<64> w(TW::Data(n,0));}catch(const std::invalid_argument&){rejected=true;}assert(rejected);checks++;
 }
 TW::HDWallet<64> mnemonic(phrase,"TREZOR"), entropy(TW::Data(16,0),"TREZOR");
 assert(mnemonic.getSeed()==entropy.getSeed());assert(mnemonic.getMnemonic()==phrase);assert(entropy.getEntropy()==TW::Data(16,0));checks+=3;
 for(unsigned strength : {128u,160u,192u,224u,256u}){TW::HDWallet<64> generated(strength,"");assert(generated.getEntropy().size()==strength/8);checks++;}
 printf("CONSTRUCTOR_OK checks=%u\n",checks);
}
