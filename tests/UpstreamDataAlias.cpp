// Synthetic regression corpus for the production Wallet Core TWData interface.
#include <TrustWalletCore/TWData.h>
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

using Bytes = std::vector<uint8_t>;
static size_t checks = 0;
static void verify(TWData* data, const Bytes& expected) {
    ++checks;
    if (TWDataSize(data) != expected.size() ||
        (!expected.empty() && !std::equal(expected.begin(), expected.end(), TWDataBytes(data))))
        throw std::runtime_error("byte comparison failed");
}
static Bytes pattern(size_t size) {
    Bytes bytes(size);
    for (size_t i = 0; i < size; ++i) bytes[i] = static_cast<uint8_t>((i * 73 + size) % 256);
    return bytes;
}
static TWData* create(const Bytes& bytes) {
    static const uint8_t empty = 0;
    return TWDataCreateWithBytes(bytes.empty() ? &empty : bytes.data(), bytes.size());
}
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const bool properties = std::strcmp(argv[1], "properties") == 0;
    const bool controls = std::strcmp(argv[1], "controls") == 0;
    const bool self = std::strcmp(argv[1], "self") == 0;
    const bool alias = std::strcmp(argv[1], "alias") == 0;
    if (!(properties || controls || self || alias)) return 2;
    if (self || alias) {
        auto expected = pattern(32);
        auto* data = create(expected);
        if (self) TWDataAppendData(data, data);
        else TWDataAppendBytes(data, TWDataBytes(data), TWDataSize(data));
        auto copy = expected;
        expected.insert(expected.end(), copy.begin(), copy.end());
        verify(data, expected);
        TWDataDelete(data);
    } else {
        // All lengths 0..256, plus allocation boundaries and larger inputs.
        std::vector<size_t> sizes;
        for (size_t size = 0; size <= 256; ++size) sizes.push_back(size);
        for (size_t size : {511, 512, 513, 1023, 1024, 4095, 4096}) sizes.push_back(size);
        for (size_t size : sizes) {
            auto expected = pattern(size);
            auto* data = create(expected);
            auto external = pattern(19);
            TWDataAppendBytes(data, external.data(), external.size());
            expected.insert(expected.end(), external.begin(), external.end());
            verify(data, expected);
            auto* other = create(external);
            TWDataAppendData(data, other);
            expected.insert(expected.end(), external.begin(), external.end());
            verify(data, expected);
            TWDataDelete(other);
            TWDataAppendBytes(data, external.data(), 0);
            verify(data, expected);
            TWDataDelete(data);
            if (controls) continue;
            for (size_t mode = 0; mode < 4; ++mode) {
                expected = pattern(size);
                data = create(expected);
                for (size_t repeat = 0; repeat < 4; ++repeat) {
                    // Snapshot the oracle independently before any production mutation.
                    size_t offset = mode == 2 ? expected.size() / 2 : 0;
                    size_t count = mode == 3 ? expected.size() / 2 : expected.size() - offset;
                    Bytes copy(expected.begin() + offset, expected.begin() + offset + count);
                    if (mode == 0) TWDataAppendData(data, data);
                    else if (count) TWDataAppendBytes(data, TWDataBytes(data) + offset, count);
                    expected.insert(expected.end(), copy.begin(), copy.end());
                    verify(data, expected);
                }
                TWDataDelete(data);
            }
        }
        if (properties) {
            auto expected = pattern(32);
            auto* data = create(expected);
            bool rejected = false;
            try { TWDataAppendBytes(data, TWDataBytes(data), std::numeric_limits<size_t>::max()); }
            catch (const std::length_error&) { rejected = true; }
            if (!rejected) return 3;
            verify(data, expected);
            rejected = false;
            try { TWDataAppendBytes(data, TWDataBytes(data) + 31, 2); }
            catch (const std::out_of_range&) { rejected = true; }
            if (!rejected) return 4;
            verify(data, expected);
            TWDataDelete(data);
        }
    }
    std::printf("DATA_ALIAS_CHECKS mode=%s checks=%zu failures=0\n", argv[1], checks);
    return 0;
}
