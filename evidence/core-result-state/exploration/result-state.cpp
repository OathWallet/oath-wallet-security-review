#include "rust/Wrapper.h"
#include <cstdio>
#include <cstring>
#include <optional>
int main(int argc, char** argv) {
    using namespace TW::Rust;
    if (argc != 2) return 2;
    CByteArrayResultWrapper result = decode_hex("010203");
    if (!result.isOk() || result.unwrap().data.size() != 3) return 3;
    result = decode_hex("invalid");
    if (!result.isErr()) return 4;
    if (std::strcmp(argv[1], "default") == 0) {
        const bool empty = result.unwrap_or_default().data.empty();
        std::printf("error_result_empty=%d\n", empty);
        return empty ? 0 : 1;
    }
    if (std::strcmp(argv[1], "unwrap") == 0) {
        bool rejected = false;
        try { (void)result.unwrap(); }
        catch (const std::bad_optional_access&) { rejected = true; }
        std::printf("error_unwrap_rejected=%d\n", rejected);
        return rejected ? 0 : 1;
    }
    return 2;
}
