# Eight-repair Core integration checkpoint

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

> Integration update: the eight repairs are now selected by public app commit
> `27fcf5f58f6169e1a40fb6afced883bc736d124d`, merged in PR 11.
> [Final app checks and remaining gaps](CORE-APP-INTEGRATION.md). Earlier
> integration-outstanding statements below describe their original checkpoints.

Core source: `d40d24a63d92619167903369308bf0e2f7eb3a59` (4.8.4).
Combined patch: [walletcore-4.8.4-combined-eight.patch](../patches/walletcore-4.8.4-combined-eight.patch),
SHA-256 `2dc70e8dbfb31dee39d6e27ba54b92257ec742c2e594d46ee7e4d3bff68e0d18`.

The native build passes 2,363 C++ tests and 113 C cryptography checks. The eighth
repair has an identical production C API regression: 12 failures before and
zero after, out of 18 cases. The seventh repair's wrapper-transition corpus
has 4,000 failures before and zero after, out of 8,000 repeated checks.
Neither count establishes whole-wallet coverage or an application exploit.

The fresh eight-repair Apple builder also **passed**: Rust targets for iOS
arm64 and simulator arm64/x86_64, both generic framework archives, and both
framework/debug-symbol ZIP packages. [Commands, logs and artifact hashes](../evidence/core-apple-eight)
record Xcode 27.0 and the exact patch. The exported-symbol comparison retains
all public `TW` C API symbols; the removed symbols are CocoaPods placeholders
and five Rust `anyhow` internals. That comparison is not full ABI or runtime
compatibility proof. The initial comparison command used an incorrect local
artifact path; the recorded comparison uses the actual nested SwiftPM artifact.

## Rebuild

Use the exact inputs and native preparation in
[the Apple reproduction recipe](CORE-APPLE-REPRODUCTION.md), but select the
combined **eight**-repair patch for the prepared native checkout. Run the native
suite with `--repair-set all-eight`, and the Apple builder with:

```sh
python3 scripts/walletcore-apple.py \
  --source /absolute/path/clean-core \
  --native /absolute/path/prepared-core \
  --generator /absolute/path/swift-protobuf-generator \
  --runtime /absolute/path/swift-protobuf-runtime \
  --rustup-home /absolute/path/scoped-tools/rustup \
  --cargo-home /absolute/path/scoped-tools/cargo \
  --repair-set eight \
  --output /tmp/core-eight-apple-reproduction
```

This performs generic compilation only; it does not launch a simulator or
physical device, upload an app, or submit anything for review.

## Remaining integration boundary

The reviewed public app target remains
`92423215ddd638b070c605a5911a9ebc7b15615f`. It still selects the original Core
artifacts. The package manifest, checksums and matching debug-symbol selection
must be updated together, then the app's required source checks, host tests and
unsigned generic Release build must pass on the resulting exact commit.
No dependency-native test result substitutes for those application checks.

The review remains maintainer-commissioned and Codex-led, with outstanding
source coverage and dependency-provenance limitations. Reproducible commands
do not alone establish byte-identical independent builds or historical App
Store binary equivalence.
