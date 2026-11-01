#include "HDWallet.h"
#include "Base58.h"
#include <array>
#include <cstdio>
#include <stdexcept>
struct Versions { TWHDVersion pub, priv; };
static constexpr std::array<Versions,10> versions{{
 {TWHDVersionXPUB,TWHDVersionXPRV},{TWHDVersionYPUB,TWHDVersionYPRV},
 {TWHDVersionZPUB,TWHDVersionZPRV},{TWHDVersionVPUB,TWHDVersionVPRV},
 {TWHDVersionTPUB,TWHDVersionTPRV},{TWHDVersionLTUB,TWHDVersionLTPV},
 {TWHDVersionMTUB,TWHDVersionMTPV},{TWHDVersionTTUB,TWHDVersionTTPV},
 {TWHDVersionDPUB,TWHDVersionDPRV},{TWHDVersionDGUB,TWHDVersionDGPV}
}};
int main() {
 TW::HDWallet<> wallet("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about", "");
 unsigned failures=0,checks=0,publicRejected=0;
 auto check=[&](bool ok,const char* label){checks++;if(!ok){failures++;std::printf("FAILED %s\n",label);}};
 for(auto version:versions){
  // Recognized mainnet encodings are accepted independently of coin here.
  // Testnet enum values remain unsupported by the existing classifier.
  bool supported=TWHDVersionIsPublic(version.pub)&&TWHDVersionIsPrivate(version.priv);
  auto pub=wallet.getExtendedPublicKey(TWPurposeBIP44,TWCoinTypeBitcoin,version.pub);
  auto priv=wallet.getExtendedPrivateKey(TWPurposeBIP44,TWCoinTypeBitcoin,version.priv);
  for(auto address:std::array<unsigned,3>{0u,7u,0x7fffffffu}){
   TW::DerivationPath path(TWPurposeBIP44,0,0,1,address);
   auto expected=wallet.getKey(TWCoinTypeBitcoin,path);
   auto expectedPublic=expected.getPublicKey(TWPublicKeyTypeSECP256k1);
   auto privateResult=TW::HDWallet<>::getPrivateKeyFromExtended(priv,TWCoinTypeBitcoin,path);
   check(supported?(privateResult&&privateResult->bytes==expected.bytes):!privateResult,"private encoding respects existing version support");
   auto publicResult=TW::HDWallet<>::getPublicKeyFromExtended(pub,TWCoinTypeBitcoin,path);
   check(supported?(publicResult&&publicResult->bytes==expectedPublic.bytes):!publicResult,"public encoding respects existing version support");
   auto rejected=TW::HDWallet<>::getPrivateKeyFromExtended(pub,TWCoinTypeBitcoin,path);
   publicRejected+=!rejected;check(!rejected,"public encoding must not produce a private key");
  }
 }
 TW::DerivationPath path("m/44'/0'/0'/0/0");
 for(const auto& malformed:std::array<std::string,3>{"","invalid","xprv9y0000"})
  check(!TW::HDWallet<>::getPrivateKeyFromExtended(malformed,TWCoinTypeBitcoin,path),"malformed input rejects");
 auto xprv=wallet.getExtendedPrivateKey(TWPurposeBIP44,TWCoinTypeBitcoin,TWHDVersionXPRV);
 auto raw=TW::Base58::decodeCheck(xprv);std::fill(raw.begin()+46,raw.end(),0);
 bool zeroAccepted=false;try{zeroAccepted=TW::HDWallet<>::getPrivateKeyFromExtended(TW::Base58::encodeCheck(raw),TWCoinTypeBitcoin,path).has_value();}catch(const std::invalid_argument&){}
 check(!zeroAccepted,"zero scalar rejects through existing error behavior");
 std::printf("EXTENDED_KEY_CHECKS total=%u public_rejected=%u failures=%u\n",checks,publicRejected,failures);
 return failures?1:0;
}
