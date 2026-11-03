# Aezeed dependency repairs and replacement archives

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

This is a maintainer-commissioned, Codex-led review in progress. It is not an
independent certification or a whole-wallet completion verdict.

The repaired public source is application commit
`92423215ddd638b070c605a5911a9ebc7b15615f`, based on reviewed commit
`02a6e8ab66c7629dcb9dd36637c683457e821d98`. It was merged in [application PR 10](https://github.com/devdasx/oath-wallet/pull/10),
merge `24e0fcedf4a55ba60345de77bed304e272b67dac`. The original findings and their
unpatched reproductions remain in [AEZEED-DEPENDENCY-REVIEW.md](AEZEED-DEPENDENCY-REVIEW.md).

## Repairs

- **DEP-AEZEED-001:** the bsaes CBC decoder now rejects partial blocks and short
  destination buffers before writing output or advancing chaining state.
- **DEP-AEZEED-002:** BLAKE2b state deserialization now checks digest size and
  buffer offset before modifying the receiver. Valid state round trips remain
  compatible, including continuation after restoration.
- **DEP-AEZEED-003:** bsaes GCM now encodes nonce, additional-data and ciphertext
  bit lengths using the required 64-bit fields, rather than truncating to 32 bits.

These are real defects in dependency APIs, but those APIs are outside the traced
Oath aezeed decoding path. No reachable wallet exploit or fund-loss path has
been established for these three findings. The wallet format, scrypt settings,
seed derivation and C ABI are unchanged.

The application contains an explicit, hash-bound patch. Its preparation script
downloads and verifies the pinned modules, copies them into a disposable vendor
tree, verifies the three upstream hashes, applies only the declared changes, and
checks all resulting file hashes. It never modifies the shared Go module cache.
Both archive compilation and tests use that prepared tree. Plain `go test` in
the source bridge directory still selects the original dependencies; the new
regressions intentionally fail there. `bash Tools/AezeedBridge/test.sh` is the
supported repaired-source test command.

## Reproduction and interpretation

From the review repository, with a clean checkout at the candidate commit:

```sh
python3 scripts/aezeed-repairs.py /path/to/oath-wallet \
  --expected-commit 92423215ddd638b070c605a5911a9ebc7b15615f \
  --output /tmp/aezeed-paired
python3 scripts/aezeed-primitives.py /path/to/oath-wallet \
  --expected-commit 92423215ddd638b070c605a5911a9ebc7b15615f \
  --output /tmp/aezeed-primitives
```

The paired runner executes the identical production regression fixture against
the original modules and the prepared dependencies. The five top-level tests
cover CBC rejection and unchanged state, malformed BLAKE2b state and valid
continuation, and actual 512 MiB GCM inputs compared with Go's standard GCM.
The large cases exercise additional data, a nonstandard nonce, and plaintext;
they require several GiB of memory under the race detector. Passing small
messages alone would not test the overflow defect.

Independent positive checks cover AES, GHASH, CBC, CTR, GCM, AEZ and BLAKE2b.
Old tests that characterized defects are not reported as repaired-code passes;
the paired regression explicitly replaces those characterizations.

## Build provenance

All three arm64 archives (macOS, iOS and iOS simulator) were rebuilt from the
repaired source. Two isolated builds on source commit
`0d41065b02fe54efc37f41c6b548874237bf659f` produced identical hashes for all ten
framework files. The final candidate changes only the provenance description:
all sixteen bridge input hashes and all ten framework hashes are identical.
That cross-commit comparison is recorded separately; the earlier rebuild is
not relabeled as an execution on the later commit.

Reproduction requires Go 1.26.5 and Xcode 27.0 (27A266a), as recorded in the
application's `BuildProvenance.json`. Equality with the historical App Store
binary remains unproven. No simulator runtime, physical device, App Store
upload or submission is part of this repair.

## Remaining boundaries

The whole-wallet review remains incomplete. In particular, five Wallet Core
source fixes still need Apple-framework integration, and the remaining source,
standard-library, upstream implementation and runtime coverage gaps remain
visible in the ledgers. These dependency repairs do not clear unrelated gaps.


## Recorded results on the final target

The [paired result](../evidence/aezeed-repairs/paired/result.json) preserves four
expected failing top-level tests before the patch and five passing top-level
tests afterward (25 nested cases, 30 pass events). The
[positive primitive result](../evidence/aezeed-repairs/positive/aezeed-primitives.json)
has ten passing checks. The [bridge script](../evidence/aezeed-repairs/bridge-test.json)
passes race tests, vet and vector generation; seed output equals the canonical
fixture. Seven aezeed host tests pass. Diagnostics has 118 passes and two explicit
skips. The [unsigned iOS Release build](../evidence/aezeed-repairs/build/build.json)
passes. Public-source and secret checks and diagnostics coverage pass.

The [manifest](../evidence/aezeed-repairs/manifest.json) records original and
published hashes for sanitized or compressed evidence. `log_sha256` fields in
original result records refer to the original log bytes; use the manifest's
published hashes for the committed compressed copies. Pin-preflight rejections
remain preserved separately; they are not counted as executed build/test failures.
