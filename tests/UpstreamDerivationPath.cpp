#include "DerivationPath.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

int main() {
 using TW::DerivationPath;
 for(const auto& input: {"m/44'/60'/0'/0/0","m/2147483647/2147483647'","m/0","m/0'"}) {
  DerivationPath p(input);assert(p.string()==input);assert(DerivationPath(p.string())==p);
  for(const auto& i:p.indices)assert(i.value<0x80000000u);
 }
 for(const auto& input:{"m/-1","m/+1","m/2147483648","m/2147483648'","m/18446744073709551616","m/1h","m/1''","m//0","m/ 1","x/1","m/0/garbage"}) {
  bool rejected=false;try{DerivationPath p(input);}catch(const std::invalid_argument&){rejected=true;}assert(rejected);
 }
 // Permissive canonicalization is existing API behavior, not evidence that
 // the caller accepts a strict absolute BIP32 grammar.
 for(const auto& input:{"","m","/","m/"})assert(DerivationPath(input).string()=="m");
 assert(DerivationPath("m1/2/").string()=="m/1/2");
 assert(DerivationPath("1/2").string()=="m/1/2");
 uint64_t state=UINT64_C(0x4f41544850415448);
 for(unsigned n=0;n<20000;n++) {
  auto next=[&](){state^=state<<13;state^=state>>7;state^=state<<17;return uint32_t(state);};
  std::string input;const unsigned length=next()%257;
  for(unsigned i=0;i<length;i++)input.push_back(static_cast<char>(next()%128));
  try {
   DerivationPath p(input);assert(DerivationPath(p.string())==p);
   for(const auto& i:p.indices)assert(i.value<0x80000000u);
  } catch(const std::invalid_argument&) {}
 }
 std::cout<<"UPSTREAM_PATH_OK malformed=20000 fixed_boundary_cases=21\n";
}
