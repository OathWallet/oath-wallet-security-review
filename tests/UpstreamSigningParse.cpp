// Synthetic, offline regression against production Wallet Core signing/planning.
#include <TrustWalletCore/TWAnySigner.h>
#include "PrivateKey.h"
#include "Tron/Address.h"
#include "Bitcoin/Address.h"
#include "Bitcoin/Script.h"
#include "proto/Tron.pb.h"
#include "proto/Bitcoin.pb.h"
#include <cstdio>
#include <string>
#include <vector>

using namespace TW;
struct Variant { const char* name; std::string suffix; bool valid; };
const std::vector<Variant> variants = {
    {"valid", "", true},
    {"valid_unknown_field", std::string("\xf8\x7f\x01", 3), true},
    {"zero_tag", std::string("\0", 1), false},
    {"truncated_tag", std::string("\x80", 1), false},
    {"invalid_wire_type", std::string("\x0f", 1), false},
    {"truncated_unknown_field", std::string("\xfa\x7f\x05\x01", 4), false},
};

template<class Input, class Output, class Success>
int check(const char* action, const Input& input, TWCoinType coin, bool plan, Success success) {
    int failures = 0;
    std::string canonical;
    for (const auto& variant : variants) {
        const auto bytes = input.SerializeAsString() + variant.suffix;
        Input parsed;
        const bool parsedOK = parsed.ParseFromString(bytes);
        auto* in = TWDataCreateWithBytes(reinterpret_cast<const uint8_t*>(bytes.data()), bytes.size());
        auto* out = plan ? TWAnySignerPlan(in, coin) : TWAnySignerSign(in, coin);
        Output result;
        const bool outputOK = result.ParseFromArray(TWDataBytes(out), static_cast<int>(TWDataSize(out)));
        const bool produced = outputOK && result.error() == Common::Proto::OK && success(result);
        if (std::string(variant.name) == "valid") canonical = result.SerializeAsString();
        const bool passed = parsedOK == variant.valid && outputOK &&
            (variant.valid ? produced && result.SerializeAsString() == canonical :
             result.error() == Common::Proto::Error_input_parse && !success(result));
        failures += !passed;
        std::printf("action=%s case=%s parsed=%d produced=%d error=%d passed=%d\n",
                    action, variant.name, parsedOK, produced, static_cast<int>(result.error()), passed);
        TWDataDelete(in); TWDataDelete(out);
    }
    return failures;
}

int main() {
    const Data key(32, 0x11), otherKey(32, 0x22);
    Tron::Proto::SigningInput tron;
    tron.set_private_key(key.data(), key.size());
    auto* tx = tron.mutable_transaction();
    tx->set_timestamp(1700000000000LL); tx->set_expiration(1700000060000LL);
    tx->mutable_block_header()->set_number(1);
    auto* transfer = tx->mutable_transfer();
    transfer->set_owner_address(Tron::Address(PrivateKey(key).getPublicKey(TWPublicKeyTypeSECP256k1Extended)).string());
    transfer->set_to_address(Tron::Address(PrivateKey(otherKey).getPublicKey(TWPublicKeyTypeSECP256k1Extended)).string());
    transfer->set_amount(1);
    int failures = check<Tron::Proto::SigningInput, Tron::Proto::SigningOutput>(
        "tron_sign", tron, TWCoinTypeTron, false, [](const auto& r) { return !r.signature().empty(); });

    Bitcoin::Proto::SigningInput bitcoin;
    const auto owner = Bitcoin::Address(PrivateKey(key).getPublicKey(TWPublicKeyTypeSECP256k1), 0).string();
    const auto recipient = Bitcoin::Address(PrivateKey(otherKey).getPublicKey(TWPublicKeyTypeSECP256k1), 0).string();
    bitcoin.set_hash_type(1); bitcoin.set_amount(1000); bitcoin.set_byte_fee(1);
    bitcoin.set_coin_type(TWCoinTypeBitcoin);
    bitcoin.set_to_address(recipient); bitcoin.set_change_address(owner);
    bitcoin.add_private_key(key.data(), key.size());
    auto* utxo = bitcoin.add_utxo(); utxo->set_amount(100000);
    auto script = Bitcoin::Script::lockScriptForAddress(owner, TWCoinTypeBitcoin);
    utxo->set_script(script.bytes.data(), script.bytes.size());
    const Data fakeHash(32, 0x33);
    utxo->mutable_out_point()->set_hash(fakeHash.data(), fakeHash.size());
    utxo->mutable_out_point()->set_index(0);
    utxo->mutable_out_point()->set_sequence(0xffffffff);
    failures += check<Bitcoin::Proto::SigningInput, Bitcoin::Proto::TransactionPlan>(
        "bitcoin_plan", bitcoin, TWCoinTypeBitcoin, true, [](const auto& r) { return r.utxos_size() != 0; });
    failures += check<Bitcoin::Proto::SigningInput, Bitcoin::Proto::SigningOutput>(
        "bitcoin_sign", bitcoin, TWCoinTypeBitcoin, false, [](const auto& r) { return !r.encoded().empty(); });
    std::printf("checks=18 failures=%d\n", failures);
    return failures ? 1 : 0;
}
