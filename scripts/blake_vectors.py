"""Independent Python hashlib BLAKE2b reference for the pinned Go implementation."""
import hashlib

def vectors():
    return [dict(Size=size, Key=bytes(range(key_size)).hex(),
                 Message=bytes((i * 37 + length) % 256 for i in range(length)).hex(),
                 Digest=hashlib.blake2b(bytes((i * 37 + length) % 256 for i in range(length)),
                                        digest_size=size, key=bytes(range(key_size))).hexdigest())
            for size in [1, 16, 32, 48, 64]
            for key_size in [0, 1, 32, 64]
            for length in [0, 1, 2, 127, 128, 129, 255, 256, 257, 511, 1024]]
