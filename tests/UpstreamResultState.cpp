#include "rust/Wrapper.h"
#include <cstdio>
#include <string>
#include <optional>
int main() {
    using namespace TW::Rust;
    size_t checks = 0, failures = 0;
    auto check = [&](bool value) { ++checks; if (!value) ++failures; };
    for (size_t i = 0; i < 1000; ++i) {
        const std::string good = i % 2 ? "01020304" : "aabbcc";
        const std::string invalid = good + (i % 2 ? "x" : "z0");
        CByteArrayResultWrapper result = decode_hex(good.c_str());
        check(result.isOk() && result.unwrap().data.size() == good.size() / 2);
        result = decode_hex(invalid.c_str());
        check(result.isErr() && result.unwrap_or_default().data.empty());
        bool rejected = false;
        try { (void)result.unwrap(); } catch (const std::bad_optional_access&) { rejected = true; }
        check(rejected);
        result = decode_hex("010203");
        check(result.isOk() && result.unwrap().data == TW::Data({1, 2, 3}));
        result = decode_hex("");
        check(result.isOk() && result.unwrap().data.empty());
        CByteArrayWrapper direct = decode_hex("aabb").result;
        direct = decode_hex("").result;
        check(direct.data.empty());
        CByteArrayResultWrapper freshError = decode_hex(invalid.c_str());
        check(freshError.isErr() && freshError.unwrap_or_default().data.empty());
        CByteArrayResultWrapper freshEmpty = decode_hex("");
        check(freshEmpty.isOk() && freshEmpty.unwrap().data.empty());
    }
    std::printf("RESULT_STATE_CHECKS total=%zu failures=%zu\n", checks, failures);
    return failures ? 1 : 0;
}
