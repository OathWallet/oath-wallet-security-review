# Core Rust-result wrapper transitions

Dependency: Wallet Core 4.8.4, `d40d24a63d92619167903369308bf0e2f7eb3a59`.
Application source inspected: `92423215ddd638b070c605a5911a9ebc7b15615f`.
This increment is a maintainer-commissioned Codex review, not independent
certification, an App Store claim or whole-wallet completion.

## DEP-CORE-007: stale values survive error and empty-result assignments

In `src/rust/Wrapper.h:213–230`, `CResult::operator=` updates the error code but only
assigns `inner` on success. Reusing a successful wrapper for an error therefore
leaves the earlier payload engaged. `unwrap_or_default()` returns that old
payload despite `isErr()` being true. `unwrap()` also returns it, contradicting
the method's documented throwing behavior. For a fresh error, dereferencing the
disengaged optional does not implement that documented exception contract.

Separately, `CByteArrayWrapper::operator=` at lines 143–150 returns early for empty/null input
without clearing its existing `data`. Both direct assignment and assignment
through an already-engaged result wrapper can retain old bytes after a valid
empty decode. An allocated zero-length Rust buffer must also be released; its
length does not alone establish that it owns no capacity.

Classification: **dependency wrapper correctness defect**. The safe local
reproduction uses real Rust `decode_hex` results and synthetic byte strings.
No application exploit, authorization bypass, signature error or fund loss has
been established. Inspected production callers construct a fresh result for
each operation and check errors or use the default result; no affected
reassignment caller was established. Broader callers remain a coverage gap.

## Candidate repair and regression evidence

[The patch](../patches/walletcore-4.8.4-result-state.patch) resets the optional
before accepting a new result, constructs a fresh payload on success, and uses
`optional::value()` to enforce the documented exception contract. Direct empty
byte-array assignment clears the prior data and calls the real Rust release
function, which accepts null arrays and releases non-null owned allocations.
No type layout, cryptography, wallet format or derivation behavior changes.
This does not establish complete secret erasure, allocation-failure recovery
or leak freedom.

[The regression](../tests/UpstreamResultState.cpp) compiles the actual production
header and calls the actual built Rust library, without substituting FFI
functions. It runs 1,000 iterations of eight transition assertions:
valid result, subsequent error/default, subsequent error/unwrap, recovery to a
valid result, successful empty result, direct empty-array assignment, fresh
error and fresh empty result. The two valid inputs alternate; these are 8,000
transition checks, not 8,000 independent cryptographic vectors.

- Before: 8,000 checks, 4,000 failures.
- After: identical 8,000 checks, zero failures.
- Separate initial error/default and error/unwrap reproductions fail before
  and pass after.

The C++ fixture runs with ASan and UBSan. The Rust archive is not sanitizer
instrumented, and leak detection is disabled. A source check records the exact
upstream revision before/after and verifies the patch, fixture, generated Rust
header and library hashes do not change during execution.

The complete native build with all seven repairs passes **2,363 C++ tests and
113 C cryptography checks**, with zero failures, errors or disabled C++ tests.
That optimized suite is separate from the focused sanitizer corpus.
Original and repaired logs, full-suite results and command records are retained
in [the evidence bundle](../evidence/core-result-state).

**Integration remains outstanding.** The public application still selects the
original Core dependency. Do not infer a distributed fix from source tests or
generic archive compilation. A fresh scripted Apple rebuild and final app
integration are separate work.

## Reproduce

Use [the native preparation recipe](CORE-NATIVE-REPRODUCTION.md) for the actual
Rust library and generated bindings, and a separate clean pinned Core checkout:

```sh
python3 scripts/walletcore-result-state.py /absolute/path/clean-wallet-core \
  --rust-library /absolute/path/prepared-wallet-core/build/local/lib/libwallet_core_rs.a \
  --bindgen-header /absolute/path/prepared-wallet-core/src/rust/bindgen/WalletCoreRSBindgen.h \
  --output /tmp/core-result-state-evidence
```

`status: passed` requires the expected baseline failure and repaired pass.
The runner records the supplied library/header identity; it does not claim to
rebuild them. Full dependency builds, app compilation and runtime testing are
separate verification layers. No simulator runtime, device operation, live
wallet, transaction or App Store action is involved.

## Source-read disposition

The complete `src/AsnParser.h` and
`src/Everscale/CommonTON/BitReader.cpp` wrappers were read: each operation
constructs a fresh result, checks its error state, then unwraps it. Those wrapper
files are reviewed; the delegated Rust ASN.1 and bit-reader implementations do
not inherit that status.

`src/Base32.h`, `src/Base58.h` and `src/Base64.cpp` were read, and
`src/Hash.cpp:77–128` was inspected for wrapper call sites. Fresh-result handling
avoids the reproduced reassignment defect in these inspected paths. Their
broader decoding/hash validation remains partial, including the Base32
output-parameter behavior on an empty input. The complete Rust
`rust/tw_memory/src/ffi/c_byte_array.rs` was read for null/empty ownership and
release behavior, and the `decode_hex` region of `rust/tw_encoding/src/ffi.rs`
was traced. Unsafe FFI caller contracts and remaining encoding functions remain
partial coverage. This does not classify the full dependency as reviewed.
