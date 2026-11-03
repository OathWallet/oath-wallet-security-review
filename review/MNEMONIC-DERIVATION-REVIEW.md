# Mnemonic, passphrase and derivation boundaries — progress 11

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Application: `f7441b85d5216b702dde490eb027aece1a6cfb5a` (4.1.15/100).
Wallet Core source: `d40d24a63d92619167903369308bf0e2f7eb3a59` (4.8.4).
This is a maintainer-commissioned, Codex-led source review, not independent
certification or evidence that Apple's distributed binary matches this source.

## Source disposition

The following files were read in full. Exact hashes and dispositions are in
`scope/upstream-wallet-core.json`; `reviewed` describes this stated source scope,
not a guarantee about all called cryptographic primitives or compiled variants.

- `trezor-crypto/crypto/bip39.c` and its `bip39.h`: entropy lengths (16–32,
  multiples of four), 240-byte output admission, checksum sizes, English word
  lookup and completion, supported 12/15/18/21/24-word parsing, 33-byte decoded
  output contract, seed salt construction, fixed 2,048-round derivation and
  progress-callback accounting. Low-level pointer APIs require valid caller
  allocations and NUL termination; this is not a general arbitrary-pointer API.
- `trezor-crypto/include/TrezorCrypto/options.h`: default BIP39/BIP32 caches are
  disabled; `CONFIDENTIAL` alone is not a memory-erasure guarantee. This is source
  configuration, not proof of the flags used in the upstream Apple archives.
- `src/Mnemonic.cpp`: bounded suggestion result count, unsigned-character case
  conversion, exact word-length matching and C-string bridging. Its full-phrase
  validator inherits the underlying C-string contract. Oath separately validates
  its multilingual phrase before constructing a wallet with Core's English-only
  check disabled; see `INPUT-BOUNDARIES.md` for that earlier source review.
- `src/DerivationPath.cpp` and `.h`: `from_chars` parsing, 31-bit index bounds,
  overflow/error handling, separators, hardened flags, defaults, setters and
  canonical serialization. The parser also accepts relative paths and `m1/2/`;
  Oath's restoration grammar is stricter. Typed constructors/setters require
  caller-side valid indices. Syntactic validity does not establish that a curve
  supports a particular derivation path.
- `trezor-crypto/crypto/hmac.c` and `hmac.h`: SHA-256/SHA-512 block-size handling,
  long-key hashing, inner/outer pad construction, prepared digest states and
  final context clearing. Underlying SHA-2 compression remains a separate review
  item; passing these vectors does not mark `sha2.c` manually reviewed.
- `trezor-crypto/crypto/pbkdf2.c` and `pbkdf2.h`: big-endian block number,
  first-iteration accounting, cumulative updates, XOR accumulation, partial final
  block output and final context clearing. The API trusts signed length arguments
  and does not reject zero iterations; see the characterization below. The local
  `digest` array in the one-shot functions is not explicitly erased after copy.
- `trezor-crypto/crypto/memzero.c`: platform-specific secure-clear functions and
  volatile fallback. The harness checks cleared HMAC/PBKDF2 contexts; it does not
  establish absence of secret copies elsewhere or test all platform branches.

Application `Packages/OathCloudBackup/Sources/OathCloudBackup/RecoveryPassphrase.swift`
was read in full and tested directly. New passphrases are NFKD-normalized, bounded
to 256 UTF-8 bytes and reject NUL. Case and whitespace are retained. The separately
named legacy function intentionally preserves old derivation behavior, with a
4,096-byte normalized bound; changing it would change existing wallet addresses.
The raw 16,384-byte admission limit bounds normalization work in both functions.

## Reproduction and actual results

```sh
python3 scripts/walletcore-mnemonic.py /path/to/pinned-wallet-core \
  --app-source /path/to/pinned-oath \
  --app-commit f7441b85d5216b702dde490eb027aece1a6cfb5a \
  --output evidence/local-mnemonic
```

Both checkouts must be clean and exactly pinned. The runner requires Ruby 4.0.5
for upstream header generation. CI pins Python 3.14.7, Ruby and all actions;
the C/C++ compiler comes from the recorded Xcode toolchain. Header generation
runs in an isolated copy; it does not modify the upstream checkout.

`evidence/walletcore-mnemonic/with-kdf/result.json` and its logs record:

- 150 entropy/mnemonic/seed vectors, covering all five entropy lengths and six
  passphrases. Python `hashlib` SHA-256/PBKDF2 supplies an independent algorithmic
  oracle, including the public TREZOR known-answer seed. The English wordlist is
  shared input (previously cross-checked), not an independently generated list.
- All 2,048 word indices, short-output guards, entropy/checksum round trips,
  progress callbacks and 20,000 seeded malformed mnemonic inputs.
- 21 fixed derivation-path cases and 20,000 seeded malformed paths, with accepted
  paths round-tripped through canonical serialization.
- 242 HMAC cases with every two-part split position, and 288 PBKDF2 cases with
  1/2/129 rounds, binary keys/salts and 1/31/32/33/63/64/65/129-byte outputs.
  Python `hmac`/`hashlib` provides the expected bytes. Output sentinels and cleared
  finalized contexts are asserted; split PBKDF2 updates are compared to the
  one-shot oracle. Zero-length output must leave the buffer untouched.
- 11 checks compiling Oath's actual passphrase implementation: normalized byte
  boundaries, NUL/empty rejection, NFKD expansion, case/space retention and legacy
  compatibility. This Swift executable did not use sanitizers.

C and C++ checks used AddressSanitizer and UndefinedBehaviorSanitizer on macOS,
with leak detection disabled. No sanitizer failure occurred. This is bounded
testing, not exhaustive fuzzing or timing/side-channel validation. No simulator,
device, network transaction or App Store operation was used.

## Characterizations, not repaired application findings

**DEP-WC-001 — low-level PBKDF2 accepts zero iterations.** Both SHA variants
produce the same result for zero and one round. The production C tests retain
this behavior explicitly; it is not a positive validation of the input policy.
The BIP39 path uses fixed 2,048 rounds. A source search of OathApp,
OathAtmosphere and Packages finds no direct `TWPBKDF2`, `PBKDF2.hmac` or
`pbkdf2_hmac_sha*` call. Oath's other password derivations use CommonCrypto.
Wallet Core's general keystore/scrypt APIs are outside this call-path conclusion
and need their own review. No upstream repair is claimed.

**Passphrase truncation:** production `mnemonic_to_seed` treats 257 repeated bytes
as the first 256 and treats `p\0x` as `p`. Oath's new-wallet guard already rejects
both conditions. Tests prove the library behavior and the application guard
separately; legacy derivation is intentionally unchanged. This was not a newly
introduced fix and has no fabricated failed-before/passed-after claim.

## Open leads and incomplete review

`src/HDWallet.cpp`, `HDWallet.h`, `PrivateKey.cpp` and `PrivateKey.h` were read,
but remain **partially-reviewed** because the following implementation/caller
questions are unresolved:

1. `HDWallet.cpp:139–150` ignores child-derivation return values. The inspected
   `bip32.c` branch rejects non-hardened derivation for curves without Weierstrass
   parameters. Oath's ordinary Ed25519 defaults are hardened; however,
   `OathWalletRestoration.swift:178–189` checks generic path syntax, not curve
   compatibility. End-to-end reproduction, migration/compatibility analysis and
   any necessary repair remain outstanding. A malformed backup must not silently
   select a parent key while recording the requested child path.
2. The templated mnemonic constructor writes a 64-byte seed; `HDWallet<32>` is
   also instantiated. The public C wrapper embeds `HDWallet<>` (64 bytes), and
   the 32-byte instantiation is used for raw-seed derivation. A reachable unsafe
   constructor call has not been established; do not label this a demonstrated
   Oath vulnerability.
3. Destructor wiping covers seed/mnemonic/passphrase, not the entropy vector;
   copies and some intermediate HD nodes/PrivateKey buffers are not uniformly
   cleared. Runtime lifetime, compiler behavior and exploitability remain open.
4. Curve-specific private-key validation, Cardano extensions, extended-key
   deserialization and Rust-backed signing require deeper called-code review.

Only sections of `bip32.c` were inspected; its ledger remains incomplete.
`sha2.c` was executed by these tests but not read in full. Wallet Core binary
source equivalence, all remaining chain implementations and whole-application
coverage remain outstanding.

## Retained harness failures

`attempt1` rejected the initial incomplete wordlist extraction before compiling;
`attempt3` failed C++ compilation because generated `TWHRP.h` was missing.
`attempt2` covered C only; `attempt4` and `final` predate the added KDF cases.
The runner now extracts all words and invokes the pinned upstream generator in
an isolated copy. `with-kdf` supersedes those attempts without deleting them.
These were review-harness failures, not defects in the shipped wallet.
