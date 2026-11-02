#include <TrustWalletCore/TWHDVersion.h>
#include <array>
#include <cstdint>
#include <cstdio>

// Baseline public ABI values. The classifier supports seven of the ten pairs.
struct Pair {
    TWHDVersion publicKind, privateKind;
    uint32_t publicValue, privateValue;
    bool supported;
};

constexpr std::array<Pair, 10> pairs{{
    {TWHDVersionXPUB, TWHDVersionXPRV, 0x0488b21e, 0x0488ade4, true},
    {TWHDVersionYPUB, TWHDVersionYPRV, 0x049d7cb2, 0x049d7878, true},
    {TWHDVersionZPUB, TWHDVersionZPRV, 0x04b24746, 0x04b2430c, true},
    {TWHDVersionVPUB, TWHDVersionVPRV, 0x045f1cf6, 0x045f18bc, false},
    {TWHDVersionTPUB, TWHDVersionTPRV, 0x043587cf, 0x04358394, false},
    {TWHDVersionLTUB, TWHDVersionLTPV, 0x019da462, 0x019d9cfe, true},
    {TWHDVersionMTUB, TWHDVersionMTPV, 0x01b26ef6, 0x01b26792, true},
    {TWHDVersionTTUB, TWHDVersionTTPV, 0x0436f6e1, 0x0436ef7d, false},
    {TWHDVersionDPUB, TWHDVersionDPRV, 0x02fda926, 0x02fda4e8, true},
    {TWHDVersionDGUB, TWHDVersionDGPV, 0x02facafd, 0x02fac398, true},
}};

bool classified(TWHDVersion version, bool publicKey, bool privateKey) {
    return TWHDVersionIsPublic(version) == publicKey &&
           TWHDVersionIsPrivate(version) == privateKey;
}

int main() {
    if (TWHDVersionNone != 0 || !classified(TWHDVersionNone, false, false)) return 1;
    for (const Pair& p : pairs) {
        if (p.publicKind != p.publicValue || p.privateKind != p.privateValue ||
            !classified(p.publicKind, p.supported, false) ||
            !classified(p.privateKind, false, p.supported)) return 2;
    }
    // Unknown values below the smallest registered version, within the enum's range.
    for (uint32_t i = 1; i <= 4096; ++i) {
        if (!classified(static_cast<TWHDVersion>(i), false, false)) return 3;
    }
    std::puts("21 named version values and 4096 unregistered values passed");
}
