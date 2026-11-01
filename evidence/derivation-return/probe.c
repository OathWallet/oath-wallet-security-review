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
    TWString *parent=TWStringCreateWithUTF8Bytes("m/44'/501'/0'");
    TWString *invalid=TWStringCreateWithUTF8Bytes("m/44'/501'/0'/7");
    TWString *valid=TWStringCreateWithUTF8Bytes("m/44'/501'/0'/7'");
    enum TWCoinType coins[]={TWCoinTypeSolana,TWCoinTypePolkadot,TWCoinTypeNEAR,TWCoinTypeStellar,TWCoinTypeSui,TWCoinTypeAptos,TWCoinTypeTON};
    unsigned aliases=0,checked=0;
    for(unsigned i=0;i<sizeof(coins)/sizeof(coins[0]);i++) {
      struct TWPrivateKey *p=TWHDWalletGetKey(wallet,coins[i],parent), *x=TWHDWalletGetKey(wallet,coins[i],invalid), *v=TWHDWalletGetKey(wallet,coins[i],valid);assert(p&&v);
      TWData *pd=TWPrivateKeyData(p),*vd=TWPrivateKeyData(v);assert(!TWDataEqual(pd,vd));
      if(x){TWData *xd=TWPrivateKeyData(x);aliases+=TWDataEqual(pd,xd);TWDataDelete(xd);TWPrivateKeyDelete(x);}
      TWDataDelete(pd);TWDataDelete(vd);TWPrivateKeyDelete(p);TWPrivateKeyDelete(v);checked++;
    }
    TWHDWalletDelete(wallet);TWStringDelete(phrase);TWStringDelete(empty);TWStringDelete(parent);TWStringDelete(invalid);TWStringDelete(valid);
    printf("CORE_PATH_CHARACTERIZATION checked=%u nonhardened_parent_aliases=%u hardened_children_distinct=%u\n",checked,aliases,checked);
    return 0;
}
