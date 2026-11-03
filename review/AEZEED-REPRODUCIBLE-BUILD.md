# Aezeed reproducible-build follow-up — reproducible replacement

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

This work follows progress release 8 and is not part of that frozen release.
The repaired application commit is `f7441b85d5216b702dde490eb027aece1a6cfb5a`,
based on `90b5b28`, merged in [PR 8](https://github.com/devdasx/oath-wallet/pull/8). No App Store binary equivalence is claimed.

Two builds with separate source and cache paths initially differed only in the
Darwin archive symbol-table timestamp: all 14 archive member contents matched.
The candidate build suppresses VCS/debug-path/build-ID metadata and sets
`ZERO_AR_DATE=1`. Two fresh macOS archives then matched byte-for-byte.

Two full three-slice builds subsequently matched all archive/header files but
not Info.plist. Inspection found only `AvailableLibraries` descriptor ordering
changed. Sorting by LibraryIdentifier and emitting canonical plist keys gives
identical hashes for all ten framework files in two additional complete builds.
The same Go 1.26.5 / Xcode 27.0 (27A266a) toolchain was used. These observations
do not assert reproducibility across toolchain versions or equivalence to the
old shipped archives. Original failed comparisons remain in the evidence.

The rebuilt macOS archive passed seven OathAezeed host cases: the five existing
seed/password tests plus two C ABI tests for invalid lengths, null pointers,
output clearing and surrounding canaries. All 22 aezeed wallet-integration checks
passed. The targeted Bitcoin subset passed 27 tests and explicitly skipped one;
this is not a full Bitcoin-suite result. Diagnostics passed 118 cases and skipped
two. Public-source validation (4,641 files), diagnostics coverage (713 catch sites),
secret scanning, Go race tests, vet, module verification and regenerated public
seed fixtures passed. Unsigned generic iOS Release compilation passed.

The final-pin reproduction is in `evidence/aezeed-reproduction/final-pin`;
all ten files match two isolated source/output/cache builds and the checked-in
bundled framework. The reference toolchain is Go 1.26.5 / Xcode 27.0 (27A266a).
CI on Xcode 27.1 verifies recorded hashes and executes primitive checks; it is
not presented as reproduction of the Xcode 27.0 archives.

Reproduce (a clean checkout at the stated commit is required):

```sh
python3 scripts/aezeed-provenance.py /path/to/source --expected-commit f7441b85d5216b702dde490eb027aece1a6cfb5a --output /tmp/aezeed-proof --rebuild
python3 scripts/aezeed-primitives.py /path/to/source --expected-commit f7441b85d5216b702dde490eb027aece1a6cfb5a --output /tmp/aes-proof
```

Without `--rebuild`, the provenance command checks only input/artifact hashes;
it explicitly records no two-build result. A mismatched reference Xcode version
fails the rebuild check instead of silently accepting different binaries.

## Additional upstream source reads

The pinned AEZ dependency files `aead.go`, `round_bitsliced32.go` and
`round_vartime.go` were read in full. The wrapper checks nonce length and only
returns authenticated plaintext; overlap is handled through fresh intermediate
buffers. Its Reset method cannot establish erasure of every runtime copy.
The 32-bit path batches rounds using the separate ct32 primitives and wipes
local word buffers; the underlying Boolean S-box still needs its own review.
The variable-time implementation uses secret-dependent table indices and must
not be mistaken for constant-time code. The package initializer selects the
bitsliced 64-bit implementation for arm64; no bridge caller selects the
variable-time implementation. This source trace is not a timing measurement or
proof about the historical archive. Ledger updates and upstream regression
linkage will accompany the final candidate publication.

## ct64 primitive source review and independent checks

The pinned `ct64/aes_ct64.go`, `aes_ct64_enc.go` and `aes_ct64_dec.go` were read
in full. The S-box is a fixed Boolean circuit; round-key access is indexed by
public round count, not secret bytes. Key schedules accept 16/24/32-byte keys;
callers allocate sufficient fixed-size expanded-key buffers. The bridge's AEZ
round adapter uses `RkeyOrtho`, the forward S-box/row/mix operations and fixed-size
load/store paths. Full AES encryption/decryption is additionally exercised here,
although the bridge does not use the `cipher.Block` modes API.

The public test fixture calls the real pinned `ct64` package. It exhausts all
256 inputs in all 64 S-box lanes using separate GF(2^8) inversion and affine
arithmetic, then checks inverse recovery. A public FIPS-197 AES-128 example and
768 deterministic AES-128/192/256 samples are checked against Go's standard AES,
including four-block paths and in-place decryption. Reset rejects subsequent
operations; short source/destination slices panic without yielding a usable result.
All three cases passed with the race detector. Results and seed are in
`evidence/aezeed-reproduction/primitives/aezeed-primitives.json`.

This is not a formal proof of the Boolean circuit, a compiler timing analysis,
or a memory-erasure guarantee. Stack/register copies and the Go runtime remain
limitations. The unrelated CBC/CTR/GCM helper implementations and remaining ct32
and BLAKE2 implementation files retain their own outstanding dispositions.
