/* A binary fixture adapter for the pinned library's internal scalar operations. */
#include <stdio.h>
#include "include/secp256k1.h"
#include "src/int128_impl.h"
#include "src/scalar_impl.h"

static int emit(const secp256k1_scalar *value) {
    unsigned char bytes[32];
    secp256k1_scalar_get_b32(bytes, value);
    return fwrite(bytes, 1, sizeof bytes, stdout) == sizeof bytes;
}

int main(void) {
    unsigned char input[64];
    size_t count;
    while ((count = fread(input, 1, sizeof input, stdin)) != 0) {
        if (count != sizeof input) return 2;
        secp256k1_scalar a, b, check, sum, product, half, neg, inv, var_inv, r1, r2;
        int overflow_a, overflow_b;
        secp256k1_scalar_set_b32(&a, input, &overflow_a);
        secp256k1_scalar_set_b32(&b, input + 32, &overflow_b);
        int accepted = secp256k1_scalar_set_b32_seckey(&check, input);
        int carry = secp256k1_scalar_add(&sum, &a, &b);
        secp256k1_scalar_mul(&product, &a, &b);
        secp256k1_scalar_half(&half, &a);
        secp256k1_scalar_negate(&neg, &a);
        inv = var_inv = secp256k1_scalar_zero;
        if (!secp256k1_scalar_is_zero(&a)) {
            secp256k1_scalar_inverse(&inv, &a);
            secp256k1_scalar_inverse_var(&var_inv, &a);
        }
        secp256k1_scalar_split_lambda(&r1, &r2, &a);
        unsigned char flags[] = {overflow_a, overflow_b, accepted, carry, secp256k1_scalar_is_high(&a)};
        if (fwrite(flags, 1, sizeof flags, stdout) != sizeof flags ||
            !emit(&a) || !emit(&b) || !emit(&sum) || !emit(&product) || !emit(&half) ||
            !emit(&neg) || !emit(&inv) || !emit(&var_inv) || !emit(&r1) || !emit(&r2)) return 3;
    }
    return ferror(stdin) || fflush(stdout) != 0;
}
