# Core data append aliasing review

> Integration update: the eight repairs are now selected by public app commit
> `27fcf5f58f6169e1a40fb6afced883bc736d124d`, merged in PR 11.
> [Final app checks and remaining gaps](CORE-APP-INTEGRATION.md). Earlier
> integration-outstanding statements below describe their original checkpoints.

Application inspected: `92423215ddd638b070c605a5911a9ebc7b15615f`.
Dependency: Wallet Core 4.8.4, `d40d24a63d92619167903369308bf0e2f7eb3a59`.
This is a maintainer-commissioned, Codex-led review increment, not an
independent audit or a completed whole-wallet assessment.

## DEP-CORE-006: append reads freed aliased storage

`src/interface/TWData.cpp:79–83` and `90–94` copy from source iterators into
the destination vector through a back-insert iterator. When the source belongs
to that same vector, the first growth can invalidate the source pointers. The
remaining copy reads freed memory. Both `TWDataAppendData(data, data)` and
`TWDataAppendBytes(data, TWDataBytes(data), TWDataSize(data))` reproduce this
with 32 synthetic bytes under AddressSanitizer. The public header does not
prohibit aliasing.

Classification: **dependency API memory-safety defect**. This demonstrates a
heap-use-after-free read, not arbitrary code execution or a wallet fund-loss
exploit. A tracked-source search found no calls to either append API in the
application source. The inspected Swift bridge creates, copies and deletes
TWData; it does not append. Core's tracked uses found by the search are API
definitions and tests. Dynamic/third-party consumers and historical binaries
are not proven unreachable by a source search.

## Repair and exact tests

The [patch](../patches/walletcore-4.8.4-data-alias.patch) saves an offset for an
aliased source, checks length arithmetic, reserves capacity, then rebases the
source before copying. It avoids an additional temporary copy of input data.
`TWDataAppendData` delegates to the same guarded implementation, with an empty
source fast path. Oversized appends and internal ranges extending beyond the
original bytes are rejected before mutation. External buffers must still meet
the existing valid-buffer contract; this is not a general arbitrary-pointer
validation mechanism. Existing allocation exceptions and C/C++ exception
boundaries are not comprehensively repaired by this change.

The [fixture](../tests/UpstreamDataAlias.cpp) tests the actual production
translation units. No cryptographic or data function is substituted.

- Before: self-append, aliased-byte append and the property corpus each stop
  with an AddressSanitizer heap-use-after-free. All 792 external/zero-length
  control checks pass.
- After: both direct reproductions pass; the same 792 controls pass; all
  5,018 property/boundary checks pass under ASan and UBSan. These counts overlap:
  the property corpus includes the controls, so they are not 5,812 unique cases.
- The property corpus covers lengths 0 through 256 and seven larger allocation
  boundaries, full/partial aliases, four repeated appends, external data,
  zero-length input, overflow rejection and invalid internal-range rejection.
- All **2,363 upstream C++ tests** pass with this repair plus the prior five
  repairs linked into the full native dependency. No failures, disabled tests
  or errors. That optimized full suite is separate from sanitizer testing.

The two initial reusable-runner compile failures are retained: the clean source
checkout lacks generated Rust bindings; the second attempt also needed the
nested include path. The successful runner now takes the real generated header
explicitly and records its hash alongside the Rust library. It does not claim
to rebuild either input itself. Initial two-case experiments are retained too.

Status: **source-repair-tested-integration-outstanding**. The public app still
pins the original dependency; framework/application integration is separate work.
There is no App Store or installed-device repair claim.

## Reproduction

First follow [native preparation](CORE-NATIVE-REPRODUCTION.md), keeping an
additional clean checkout at the pinned upstream commit. Then run:

```sh
python3 scripts/walletcore-data-alias.py /absolute/path/clean-wallet-core \
  --rust-library /absolute/path/prepared-wallet-core/build/local/lib/libwallet_core_rs.a \
  --bindgen-header /absolute/path/prepared-wallet-core/src/rust/bindgen/WalletCoreRSBindgen.h \
  --output /tmp/core-data-alias-evidence
```

Expected runner result: `status: passed`, meaning the expected baseline failures
and repaired passes were both observed. It does not mean the baseline is safe.
The runner checks source identity before and after, and rejects changed test,
patch, generated-header or library inputs. Leak detection is disabled. This is
a macOS host test with Apple Clang 21/Xcode 27.0, not simulator or device testing.

See [preserved evidence](../evidence/core-data-alias), including full-suite
commands/results and source-call searches. The full-suite command uses the
complete repaired TWData and HDWallet objects before the original static
library, not copied test-only logic. The earlier native recipe supplies the
remaining libraries and test fixtures.

## Review disposition and remaining work

The complete TWData implementation/header, its existing upstream tests and
Swift bridge were read. Append growth is repaired; copy/replace overlapping
ranges and empty-vector nonnull contracts still require dedicated review.
Logical bytes are wiped on deletion, but allocator capacity, reallocations and
temporary Swift copies are not a complete memory-erasure guarantee.

`Data.cpp` was read for bounds and constant-time comparison: slices reject a
start at or beyond the end and clamp length, while equality checks length first.
`TWString.cpp` was read; unchecked indexing and embedded-NUL handling need
caller-contract review. `HexCoding.h` and `rust/Wrapper.h` were read for the
actual linker dependencies; Rust ownership/error-state review remains open.
These incomplete analyses remain partial coverage, not automatic passes from
the upstream suite. No simulator, physical device or App Store operation ran.
