#include <assert.h>
#include <stdio.h>
#include <WalletCore/TWHDWallet.h>
#include <WalletCore/TWPrivateKey.h>
#include <WalletCore/TWString.h>
#include <WalletCore/TWData.h>
int main(void) {
    TWString *phrase=TWStringCreateWithUTF8Bytes("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about");
    TWString *empty=TWStringCreateWithUTF8Bytes("");
    struct TWHDWallet *wallet=TWHDWalletCreateWithMnemonic(phrase,empty);assert(wallet);
    const char *paths[][2]={
      {"m/44'/501'/0'/7", "m/44'/501'/0'"},
      {"m/7/44'/0'/9/3'", "m/44'/0'/3'"},
      {"m/0/1/2", "m"},
      {"m/0'/1'/2147483647'", "m/0'/1'/2147483647'"},
      {"m/2147483647/0'/2147483647", "m/0'"},
      {"m/0/2147483647/1'/2147483647'", "m/1'/2147483647'"},
      {"m", "m"},
      {"m/44'/501'/00'/07", "m/44'/501'/00'"}
    };
    enum TWCoinType coins[]={TWCoinTypeSolana,TWCoinTypePolkadot,TWCoinTypeNEAR,TWCoinTypeStellar,TWCoinTypeSui,TWCoinTypeAptos,TWCoinTypeTON};
    unsigned checked=0;
    for(unsigned seed=0;seed<2;seed++) {
      if(seed){TWHDWalletDelete(wallet);TWString *password=TWStringCreateWithUTF8Bytes("TREZOR");wallet=TWHDWalletCreateWithMnemonic(phrase,password);TWStringDelete(password);assert(wallet);}
      for(unsigned i=0;i<sizeof(coins)/sizeof(coins[0]);i++) {
        for(unsigned j=0;j<sizeof(paths)/sizeof(paths[0]);j++) {
          TWString *original=TWStringCreateWithUTF8Bytes(paths[j][0]),*canonical=TWStringCreateWithUTF8Bytes(paths[j][1]);
          struct TWPrivateKey *a=TWHDWalletGetKey(wallet,coins[i],original), *b=TWHDWalletGetKey(wallet,coins[i],canonical);assert(a&&b);
          TWData *ad=TWPrivateKeyData(a),*bd=TWPrivateKeyData(b);assert(TWDataEqual(ad,bd));
          TWDataDelete(ad);TWDataDelete(bd);TWPrivateKeyDelete(a);TWPrivateKeyDelete(b);TWStringDelete(original);TWStringDelete(canonical);checked++;
        }
      }
    }
    TWHDWalletDelete(wallet);TWStringDelete(phrase);TWStringDelete(empty);
    printf("CORE_PATH_COMPATIBILITY equivalent_keys=%u chains=7 path_pairs=8 seeds=2\n",checked);
    assert(checked==112);
    return 0;
}
