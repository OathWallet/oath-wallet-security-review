# Core serialized signing-input boundary

Core baseline: `d40d24a63d92619167903369308bf0e2f7eb3a59` (4.8.4).
Application source: `92423215ddd638b070c605a5911a9ebc7b15615f`.
Maintainer-commissioned Codex review; no independent certification or App Store claim.

## DEP-CORE-008: failed input parsing does not stop signing or planning

`src/CoinEntry.h:79–110` ignores `ParseFromArray`'s result in both `signTemplate`
and `planTemplate`. Protobuf can populate a valid prefix of the message before
rejecting a malformed trailing field. The templates then invoke the signer or
planner on that partially parsed message and return a successful result.

The production C API reproduction confirms this for TRON signing, Bitcoin
signing and Bitcoin planning. A valid serialized input followed by a zero tag,
truncated tag, invalid wire type or truncated unknown length-delimited field
is rejected by the parser but nevertheless produces a signature or transaction
plan before repair. No network request or transaction broadcast is performed.

Classification: **dependency input-validation defect**. This violates the
serialized-input acceptance boundary. It does not establish a signature over
an attacker-chosen transaction without user authorization, key disclosure,
fund loss, or reachable Oath attack. A tracked Swift/C/C++ search under the
application and package directories found no `AnySigner`/`TWAnySigner` caller.
The inspected Bitcoin signer uses BDK; the inspected TRON signer serializes its
own reviewed plan and signs through OathSecp256k1. Dynamic or generated callers,
other products and the broader signing dependencies remain separate scope.

## Repair and exact evidence

The [source patch](../patches/walletcore-4.8.4-signing-parse.patch) checks parsing
before invoking signing/planning and returns `Error_input_parse` with no signed
payload on failure. It also checks the `size_t` to `int` boundary before parsing
in all four shared signing/planning/compiler templates. The compiler helpers
already rejected a false parse result; their added size guard is preventative.
No multi-gigabyte input was allocated to runtime-test that guard.

The [identical fixture](../tests/UpstreamSigningParse.cpp) invokes real
`TWAnySignerSign` and `TWAnySignerPlan`, linked to the rebuilt production C++,
C cryptography, Rust and protobuf libraries. It uses two fixed synthetic keys,
a fake UTXO, fixed timestamps and offline-only operations. No FFI, parser,
signer or planner is replaced by a test-only implementation.

For each of three paths, there is an ordinary valid control, a valid unknown
Protobuf-field control, and four malformed cases: **18 cases total**.

- Before: all six controls pass, all twelve malformed cases incorrectly produce
  successful signed/plan output. The fixture reports 12 failures.
- After: all 18 pass. Malformed inputs produce `Error_input_parse` and no signed
  transaction/signature or selected UTXOs. Both valid controls still succeed.
- Within each stage, the valid unknown-field control must serialize exactly the
  same output as the ordinary valid input. This is not a general cross-version
  signature-byte equivalence claim.

The [paired runner](../scripts/walletcore-signing-parse.py) checks the exact
seven-repair source diff, builds the baseline library, applies only the eighth
repair, rebuilds, and executes the same fixture. The initial two-case proof,
expanded proof, paired builds and binary/input hashes are retained in
[evidence/core-signing-parse](../evidence/core-signing-parse).
This is an optimized native macOS test, not a sanitizer or app runtime test.
The full eight-repair native suite separately passes **2,363 C++ tests and
113 C cryptography checks**, with zero failures, errors or disabled C++ tests.
Its logs and result are preserved under `full-native` in the evidence directory.
The Apple archives are separate checks.
Integration into the public application remains outstanding.

## Reproduction

Follow the native build recipe in a **disposable, dedicated** Core checkout,
with `walletcore-4.8.4-combined-eight.patch` as the exact tracked diff. No other
build may use that checkout while this runner temporarily reverses/reapplies
the eighth repair. The output directory must be new.

```sh
python3 scripts/walletcore-signing-parse.py /absolute/path/prepared-core \
  --output /tmp/core-signing-parse-evidence
```

Source restoration runs in `finally`. If the process or machine is forcibly
terminated, inspect the tracked diff before reusing the disposable checkout.
Never infer the source identity from an old build directory or terminal message.

## Source coverage in this increment

- `src/CoinEntry.h`: complete read of the interface, four templates and their
  exception paths; the input-parse defect is reproduced and repaired. Downstream
  coin-specific algorithms do not inherit this review disposition.
- `src/Tron/Address.cpp`: complete read of Base58Check length/prefix validation,
  extended-key type requirement and Keccak address derivation. Hash and Base58
  implementations remain separate dependencies.
- `src/interface/TWAnySigner.cpp`: complete wrapper read, partial disposition;
  unsupported coin dispatch and C pointer preconditions remain outstanding.
- `src/Tron/Entry.cpp`: complete wrapper read, partial disposition; compiler
  signature verification and all delegated signer internals remain outstanding.
- `src/AnyAddress.cpp`: complete wrapper read, partial disposition; behavior of
  every dispatched normalizer/deriver remains outstanding.
- Oath `BitcoinSendSigner.swift` and `TronSendCrypto.swift`: complete file reads
  for the AnySigner reachability trace, partial security dispositions. Plan
  validation, BDK/PSBT behavior, cryptographic implementation and all cross-wallet
  authorization paths still require their own evidence.

The inspected upstream `Coin.cpp` dispatch region and portions of `Tron/Signer.cpp`
are not marked fully reviewed. Shared-template repair does not mean every
chain's transaction builder has been tested against adversarial inputs.
