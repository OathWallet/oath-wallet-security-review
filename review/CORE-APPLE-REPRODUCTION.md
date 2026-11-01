# Repaired Core Apple artifact reproduction

> Integration update: the eight repairs are now selected by public app commit
> `27fcf5f58f6169e1a40fb6afced883bc736d124d`, merged in PR 11.
> [Final app checks and remaining gaps](CORE-APP-INTEGRATION.md). Earlier
> integration-outstanding statements below describe their original checkpoints.

This builds the Wallet Core 4.8.4 source at
`d40d24a63d92619167903369308bf0e2f7eb3a59` with the seven published source
repairs. It does not rebuild or prove equivalence with a historical App Store
binary. This is an unsigned compile/archive procedure; no simulator or physical
device is launched. The public app dependency selection has not changed yet.

The first manual build sequence compiled both generic iOS and universal iOS
simulator archives. A generic iOS Release app build also passed with the first
six repaired APIs packaged locally. That app build predates the seventh repair
and is not final integration evidence. The consolidated scripted procedure
below completed successfully in a fresh output directory with all seven repairs.
Both generic archives, Rust targets, packaged frameworks and matching debug
symbols passed their build steps. [Commands, hashes and logs](../evidence/core-apple-seven)
retain an earlier failed attempt: XcodeGen could not determine the username after
the build environment omitted USER/LOGNAME. The runner now preserves those ordinary
environment variables; a new output directory was used for the successful run.
The later eighth signing-parser repair is not included in this seven-repair
artifact result. App integration and an eight-repair artifact rebuild remain separate.

## Exact public inputs

- Core source: `d40d24a63d92619167903369308bf0e2f7eb3a59`.
- [Combined seven-repair patch](../patches/walletcore-4.8.4-combined-seven.patch),
  SHA-256 `9a73daf4c0105ea604f5c9a034004443122b138cce26b100d5b3ca37bcfe471a`.
- Swift protobuf generator 1.18.0:
  `7e2c5f3cbbeea68e004915e3a8961e20bd11d824` in
  `https://github.com/apple/swift-protobuf.git`, as selected by upstream tooling.
- Swift protobuf runtime 1.29.0:
  `d72aed98f8253ec1aa9ea1141e28150f408cf17f` in the same repository, matching
  upstream `swift/Podfile.lock`. Runtime podspec SHA-1
  `a4798576a2d309511fc45f81843d348732ec571d` matches that lock. SHA-1 is the
  upstream CocoaPods lock identifier, not a new security checksum policy.
- Protobuf compiler/C++ source 3.20.3 and other native dependencies from the
  hash-pinned [native recipe](CORE-NATIVE-REPRODUCTION.md).
- Rust nightly-2025-12-11, its matching `rust-src`, unchanged Core Cargo locks,
  cbindgen 0.29.2; Xcode 27.0/Apple Clang 21 and XcodeGen 2.45.4.

Keep separate clean checkouts for Core, the generator and the runtime. Follow
the native recipe in a disposable prepared Core checkout, replacing its
four-repair patch with `walletcore-4.8.4-combined-seven.patch`. The exact whole
tracked diff must match the selected patch; generated outputs must match the
[374-file generated-input manifest](../scope/walletcore-generated-inputs.json).
These hashes are build input evidence, not manual review dispositions.

The following native test command rejects any different tracked source or
untracked non-ignored source inputs:

```sh
python3 scripts/walletcore-native-tests.py /absolute/path/prepared-core \
  --repair-set all-seven \
  --app-source /absolute/path/oath-source \
  --app-commit 92423215ddd638b070c605a5911a9ebc7b15615f \
  --output /tmp/core-seven-native-tests
```

The application pin labels the reviewed application context; native dependency
tests execute the separately pinned Core source. This command has passed the
2,363 C++ and 113 C tests with all seven repairs.

## Fresh Apple build

The generator/runtime/source arguments are clean checkouts at the pins above.
The scoped Rust homes are the ones created by native preparation. Output must
not already exist. Existing source inputs are checked and read, not rewritten.
The script creates its own disposable Core clone and build directories.

```sh
python3 scripts/walletcore-apple.py \
  --source /absolute/path/clean-core \
  --native /absolute/path/prepared-core \
  --generator /absolute/path/swift-protobuf-generator \
  --runtime /absolute/path/swift-protobuf-runtime \
  --rustup-home /absolute/path/scoped-tools/rustup \
  --cargo-home /absolute/path/scoped-tools/cargo \
  --output /tmp/core-seven-apple-reproduction
```

The script builds the generator, generates Swift protobuf code, cross-compiles
Rust for device arm64 and simulator arm64/x86_64, builds both full framework
archives, checks source identities again, and packages frameworks and matching
device debug symbols. It derives its Xcode project from the pinned upstream
project specification and replaces CocoaPods setup with the pinned runtime
source target. The optional upstream SwiftLint post-compile step is omitted;
this is not a claim that that lint check passed.

The upstream iOS 13 minimum is unsupported by the selected Xcode SDK. These
dependency archives use iOS 15; Oath's own iOS 26 minimum remains unchanged.
The Core privacy manifest is copied verbatim from pinned upstream source.
The protobuf privacy resource bundle comes from its actual built resource
target and is checked against the pinned runtime manifest. No executable is
modified during resource packaging. Matching dSYMs are included, rather than
reusing symbols from the original downloaded release.

Commands, failures, toolchain versions, generated inputs, native tool/dependency
prefix hashes and final artifact hashes are written below `output/evidence`.
Archives are written below `output/artifacts`. ZIP entry ordering/timestamps
are fixed; that makes packaging repeatable for identical inputs, but does not
establish byte-identical compiler outputs between independent builds.

No deployment secrets, provider keys or signing identities are needed. Required
compiler/tool downloads and public package downloads need network access. App
integration must separately update both binary targets, their checksums and
matching symbol acquisition, then pass its own host tests and unsigned Release
build. Do not point a published package at a local filesystem build directory.
