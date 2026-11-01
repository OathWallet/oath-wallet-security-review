// Compile against the reviewed Wallet Core source; all inputs are synthetic paths.
#include <TrustWalletCore/TWDerivationPath.h>
#include <TrustWalletCore/TWDerivationPathIndex.h>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

static void check(bool value, const char* reason) {
    if (!value) throw std::runtime_error(reason);
}

static TWDerivationPath* parse(const std::string& text) {
    auto input = TWStringCreateWithRawBytes(reinterpret_cast<const uint8_t*>(text.data()), text.size());
    auto path = TWDerivationPathCreateWithString(input);
    TWStringDelete(input);
    return path;
}

static std::string consume(TWString* value) {
    std::string result(TWStringUTF8Bytes(value), TWStringSize(value));
    TWStringDelete(value);
    return result;
}

int main() {
    uint32_t state = 0x53a7f02bU;
    for (int i = 0; i < 512; ++i) {
        state = state * 1664525U + 1013904223U;
        const uint32_t leaf = i == 0 ? 0U : i == 1 ? 0x7fffffffU : state >> 1;
        auto typed = TWDerivationPathCreate(TWPurposeBIP84, 0, 3, 1, leaf);
        const std::string canonical = "m/84'/0'/3'/1/" + std::to_string(leaf);
        check(consume(TWDerivationPathDescription(typed)) == canonical, "typed encoding");
        auto parsed = parse(canonical);
        check(parsed && TWDerivationPathIndicesCount(parsed) == 5, "parsed length");
        check(TWDerivationPathPurpose(parsed) == TWPurposeBIP84 &&
              TWDerivationPathCoin(parsed) == 0 && TWDerivationPathAccount(parsed) == 3 &&
              TWDerivationPathChange(parsed) == 1 && TWDerivationPathAddress(parsed) == leaf, "field values");
        check(!TWDerivationPathIndexAt(parsed, 5) && !TWDerivationPathIndexAt(parsed, UINT32_MAX), "index bounds");
        auto segment = TWDerivationPathIndexAt(parsed, 4);
        TWDerivationPathDelete(parsed);
        TWDerivationPathDelete(typed);
        check(segment && TWDerivationPathIndexValue(segment) == leaf &&
              !TWDerivationPathIndexHardened(segment), "index owns a copy after path deletion");
        check(consume(TWDerivationPathIndexDescription(segment)) == std::to_string(leaf), "leaf description");
        TWDerivationPathIndexDelete(segment);
        auto index = TWDerivationPathIndexCreate(leaf, true);
        check(TWDerivationPathIndexHardened(index) && TWDerivationPathIndexValue(index) == leaf &&
              consume(TWDerivationPathIndexDescription(index)) == std::to_string(leaf) + "'", "hardened index");
        TWDerivationPathIndexDelete(index);
    }
    for (const std::string bad : {std::string("m/-1"), std::string("m/2147483648"),
            std::string("m/999999999999999999999999999"), std::string("m/1''"),
            std::string("m/1//2"), std::string("m/1x"), std::string("m/1\0/2", 6)}) {
        check(parse(bad) == nullptr, "invalid text must fail through the C ABI");
    }
    // The string parser accepts a root, relative components, and a trailing slash.
    auto root = parse("m/");
    check(root && TWDerivationPathIndicesCount(root) == 0 && !TWDerivationPathIndexAt(root,0) &&
          TWDerivationPathPurpose(root) == TWPurposeBIP44 && TWDerivationPathCoin(root) == 0 &&
          TWDerivationPathAccount(root) == 0 && TWDerivationPathChange(root) == 0 &&
          TWDerivationPathAddress(root) == 0 && consume(TWDerivationPathDescription(root)) == "m", "root defaults");
    TWDerivationPathDelete(root);
    auto relative = parse("1'/2/");
    check(relative && consume(TWDerivationPathDescription(relative)) == "m/1'/2", "canonical description");
    TWDerivationPathDelete(relative);

    // Characterize an API asymmetry. The numeric constructor accepts all uint32_t
    // values, including those with the hardened bit already set. Record that
    // boundary; do not treat acceptance as validation of a BIP32 child index.
    auto high = TWDerivationPathCreate(TWPurposeBIP44,0,0,0,0x80000000U);
    auto text = consume(TWDerivationPathDescription(high));
    check(TWDerivationPathAddress(high) == 0x80000000U && parse(text) == nullptr, "typed high-bit boundary");
    TWDerivationPathDelete(high);
    std::cout << "Passed 512 path and index vectors, 7 invalid raw strings, 2 canonicalization cases, 1 characterized numeric boundary.\n";
}
