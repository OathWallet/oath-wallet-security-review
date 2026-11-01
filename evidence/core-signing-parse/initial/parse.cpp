#include <TrustWalletCore/TWAnySigner.h>
#include "PrivateKey.h"
#include "Tron/Address.h"
#include "proto/Tron.pb.h"
#include <cstdio>
#include <string>
int main() {
    using namespace TW;
    const Data syntheticKey(32, 0x11), recipientKey(32, 0x22);
    Tron::Proto::SigningInput input;
    input.set_private_key(syntheticKey.data(), syntheticKey.size());
    auto* tx = input.mutable_transaction();
    tx->set_timestamp(1700000000000LL); tx->set_expiration(1700000060000LL);
    tx->mutable_block_header()->set_number(1);
    auto* transfer = tx->mutable_transfer();
    transfer->set_owner_address(Tron::Address(PrivateKey(syntheticKey).getPublicKey(TWPublicKeyTypeSECP256k1Extended)).string());
    transfer->set_to_address(Tron::Address(PrivateKey(recipientKey).getPublicKey(TWPublicKeyTypeSECP256k1Extended)).string());
    transfer->set_amount(1);
    const std::string valid = input.SerializeAsString();
    int failures = 0;
    for (int mode = 0; mode < 2; ++mode) {
        auto bytes = valid;
        if (mode) bytes.push_back('\0');
        Tron::Proto::SigningInput parsed;
        bool parseOK = parsed.ParseFromString(bytes);
        auto* in = TWDataCreateWithBytes(reinterpret_cast<const uint8_t*>(bytes.data()), bytes.size());
        auto* out = TWAnySignerSign(in, TWCoinTypeTron);
        Tron::Proto::SigningOutput output;
        bool outputOK = output.ParseFromArray(TWDataBytes(out), static_cast<int>(TWDataSize(out)));
        bool signedOK = outputOK && output.error() == 0 && output.signature().size() == 65;
        std::printf("mode=%s input_parse_ok=%d signed_ok=%d error=%d\n",mode?"malformed":"valid",parseOK,signedOK,static_cast<int>(output.error()));
        if ((mode == 0 && (!parseOK || !signedOK)) || (mode == 1 && (parseOK || signedOK))) ++failures;
        TWDataDelete(in);TWDataDelete(out);
    }
    return failures ? 1 : 0;
}
