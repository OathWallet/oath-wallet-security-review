# Child derivation and dependency API characterizations

Application target: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
Wallet Core source: `d40d24a63d92619167903369308bf0e2f7eb3a59` (4.8.4).
This is an incomplete maintainer-commissioned source review, not a certification.

## Reproduction

From this review repository, with clean checkouts of both pins:

```sh
python3 scripts/walletcore-bip32.py /path/to/wallet-core \
  --app-source /path/to/oath-wallet \
  --app-commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --output /tmp/oath-bip32-evidence
```

The runner compiles the actual 61 C translation units selected by the pinned
Trezor CMake source list. It archives them and links only required objects into
the fixture, with AddressSanitizer and UndefinedBehaviorSanitizer. No production
function is replaced. A first attempt to link all objects directly failed on
unused Monero symbols; that failed attempt is retained. Building a static
archive matches the upstream library's object-extraction model. Compilation is
not evidence that all 61 files were exercised or reviewed.

Positive host results:

- 52 published SLIP-0010 vectors across secp256k1, NIST P-256, Ed25519 and
  Curve25519, including the published NIST retry cases.
- 1,920 independently generated hardened derivation cases: 64 deterministic
  synthetic seeds, five curve identifiers, and path depths zero through five.
  Seed lengths are 16, 32 and 64 bytes; indices include the hardened-bit and
  maximum-UInt32 boundaries. The fifth identifier is Nano's Blake2b variant;
  these cases test its private derivation, not its public-key generation.
- 33 public/private child-derivation comparisons.
- 20,000 malformed extended-key parser calls, generated with xorshift seed
  `0x4f415448`, rejected without sanitizer errors.
- Two unsupported Ed25519 non-hardened children rejected without node mutation.

The Python oracle uses HMAC/hashlib and modular integer arithmetic, independently
of Trezor C. It is anchored against 33 official root/all-hardened cases before
generating additional expectations. Official fixtures are pinned to
[SLIP-0010 commit e2824d0](https://github.com/satoshilabs/slips/blob/e2824d0027c90187caa9ea300a889dfda61976a0/slip-0010.md).
The 25519 vectors use a zero serialization prefix whereas Trezor's internal
populated-key cache uses one; the fixture checks the prefixes separately and
compares the 32 actual public-key bytes.

## DEP-CORE-001 — invalid curve dereference (unrepaired dependency API)

`trezor-crypto/crypto/bip32.c:752`: `hdnode_deserialize` assigns the result of
`get_curve_by_name` and dereferences it without checking for null. Calling the
private deserializer with an unknown curve identifier and the public string
`invalid` triggers UBSan's null-member-access diagnostic. A robust API should
return an invalid-curve error before dereferencing it. Run the fixture with
`unknown-curve` to reproduce; the runner preserves the failing subprocess log.

The pinned Core `src` tree has no call to `hdnode_deserialize_public` or
`hdnode_deserialize_private`. Core's C++ HDWallet implementation has a separate
deserializer that checks the curve mapping. This is a confirmed low-level API
hazard, not an established reachable Oath vulnerability or fund-loss path.
It remains unrepaired in the pinned dependency; there is no app fix or after-pass.

## DEP-CORE-002 — Nano public-key cache reports success without a key

`trezor-crypto/crypto/bip32.c:484–518`: `hdnode_fill_public_key` sets the cached-key
prefix to one for non-Weierstrass curves, but has no branch for the accepted
`ed25519-blake2b-nano` curve. It returns success while leaving all 32 key bytes
zero. A valid 16-byte synthetic seed reproduces this; `nano-public` fails its
nonzero-key assertion. Expected behavior is deriving the correct public key or
explicitly rejecting an unsupported curve without populating the cache marker.

Ordinary Core `PrivateKey::getPublicKey` calls `ed25519_publickey_blake2b`
directly. Oath's inspected Swift application sources do not select Nano.
The three C++ HDWallet calls to the affected helper serve extended-key and
fingerprint paths; a reachable Oath Nano request was not established. This
dependency API hazard also remains unrepaired; its intentional failing process
is not presented as a successful regression fix.

## Source review disposition and limitations

The complete `bip32.c` and HDWallet implementation were read, including optional
cache, NEM, ECDH and signing branches. Their dispositions remain partial: optional
branches, transitive scalar arithmetic and broader caller contracts still need
review. `USE_BIP32_CACHE` defaults to zero in the pinned options; the cache's
depth/copy assumptions are not proven for a different build configuration.
PrivateKey ownership/signing and HDWallet's secret-copy lifetime remain open.
The separate [constructor reachability note](HDWALLET-CONSTRUCTOR-REACHABILITY.md)
narrows the 32-byte seed-template lead without asserting an unreachable-code proof.

The positive corpus is bounded, does not test all valid serialized extended keys,
does not establish constant-time behavior, and does not prove the distributed
Apple frameworks correspond to these sources. Expected API crashes are recorded
separately from positive tests. No simulator, phone, production provider or
transaction was used for this new derivation harness. Earlier progress 12 used a
minimal simulator process for a separately documented framework-only check.
