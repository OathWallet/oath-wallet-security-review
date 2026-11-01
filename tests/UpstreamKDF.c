#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <TrezorCrypto/hmac.h>
#include <TrezorCrypto/pbkdf2.h>
#include "kdf-vectors.h"

static size_t decode(const char *hex, uint8_t *out, size_t cap) {
    size_t count = strlen(hex) / 2;
    assert(strlen(hex) % 2 == 0 && count <= cap);
    for (size_t i = 0; i < count; ++i) {
        unsigned byte;
        assert(sscanf(hex + i * 2, "%2x", &byte) == 1);
        out[i] = (uint8_t)byte;
    }
    return count;
}
static void wiped(const void *context, size_t count) {
    const uint8_t *bytes = context;
    for (size_t i = 0; i < count; ++i) assert(bytes[i] == 0);
}

#define CHECK_ALGORITHM(BITS, DIGEST) \
static void check##BITS(const struct KDFVector *v) { \
    uint8_t key[256] = {0}, message[256] = {0}, expected[129] = {0}; \
    size_t k = decode(v->key, key, sizeof key); \
    size_t m = decode(v->message, message, sizeof message); \
    size_t n = decode(v->expected, expected, sizeof expected); \
    struct { uint8_t before[16], value[129], after[16]; } result; \
    memset(&result, 0xa5, sizeof result); \
    if (v->kind == 0) { \
        assert(n == DIGEST); \
        hmac_sha##BITS(key, (uint32_t)k, message, (uint32_t)m, result.value); \
        assert(memcmp(expected, result.value, n) == 0); \
        for (size_t split = 0; split <= m; ++split) { \
            HMAC_SHA##BITS##_CTX context; \
            hmac_sha##BITS##_Init(&context, key, (uint32_t)k); \
            hmac_sha##BITS##_Update(&context, message, (uint32_t)split); \
            hmac_sha##BITS##_Update(&context, message + split, (uint32_t)(m - split)); \
            hmac_sha##BITS##_Final(&context, result.value); \
            assert(memcmp(expected, result.value, n) == 0); \
            wiped(&context, sizeof context); \
        } \
    } else { \
        pbkdf2_hmac_sha##BITS(key, (int)k, message, (int)m, v->rounds, result.value, (int)n); \
        assert(memcmp(expected, result.value, n) == 0); \
        PBKDF2_HMAC_SHA##BITS##_CTX context; \
        uint8_t block[DIGEST]; \
        pbkdf2_hmac_sha##BITS##_Init(&context, key, (int)k, message, (int)m, 1); \
        pbkdf2_hmac_sha##BITS##_Update(&context, 1); \
        if (v->rounds > 1) pbkdf2_hmac_sha##BITS##_Update(&context, v->rounds - 1); \
        pbkdf2_hmac_sha##BITS##_Final(&context, block); \
        assert(memcmp(expected, block, n < DIGEST ? n : DIGEST) == 0); \
        wiped(&context, sizeof context); \
    } \
    for (size_t i = 0; i < 16; ++i) assert(result.before[i] == 0xa5 && result.after[i] == 0xa5); \
    for (size_t i = n; i < sizeof result.value; ++i) assert(result.value[i] == 0xa5); \
}
CHECK_ALGORITHM(256, 32)
CHECK_ALGORITHM(512, 64)

int main(void) {
    size_t hmac = 0, pbkdf2 = 0;
    for (size_t i = 0; i < sizeof kdf_vectors / sizeof kdf_vectors[0]; ++i) {
        const struct KDFVector *v = &kdf_vectors[i];
        if (v->bits == 256) check256(v); else { assert(v->bits == 512); check512(v); }
        if (v->kind == 0) ++hmac; else ++pbkdf2;
    }
    // Characterization, not approval: this low-level API treats zero rounds as
    // one rather than rejecting it. BIP39 uses the fixed 2,048-round path.
    uint8_t zero[64], one[64], byte = 0;
    pbkdf2_hmac_sha256(&byte, 1, &byte, 1, 0, zero, 32);
    pbkdf2_hmac_sha256(&byte, 1, &byte, 1, 1, one, 32);
    assert(memcmp(zero, one, 32) == 0);
    pbkdf2_hmac_sha512(&byte, 1, &byte, 1, 0, zero, 64);
    pbkdf2_hmac_sha512(&byte, 1, &byte, 1, 1, one, 64);
    assert(memcmp(zero, one, 64) == 0);
    // Zero output length must not write to the caller's buffer.
    memset(zero, 0xa5, sizeof zero);
    pbkdf2_hmac_sha256(&byte, 1, &byte, 1, 2, zero, 0);
    pbkdf2_hmac_sha512(&byte, 1, &byte, 1, 2, zero, 0);
    for (size_t i = 0; i < sizeof zero; ++i) assert(zero[i] == 0xa5);
    assert(hmac == 242 && pbkdf2 == 288);
    puts("UPSTREAM_KDF_OK hmac=242 pbkdf2=288 zero_round_characterizations=2");
    return 0;
}
