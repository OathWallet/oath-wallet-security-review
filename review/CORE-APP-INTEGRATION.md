# Core repairs integrated into public application source

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Application commit: `27fcf5f58f6169e1a40fb6afced883bc736d124d`.
[PR 11](https://github.com/devdasx/oath-wallet/pull/11) merged as
`99742291d6124fd2628bbf1653ec0ba5f121456f`; a tree comparison found no difference
between the tested candidate and that merge. Version remains 4.1.15 (100).
No App Store upload or submission was performed.

## Change and provenance

Both binary targets now select the eight-repair artifacts from
[progress 19](https://github.com/devdasx/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress19).
The combined source patch, pinned upstream commit, Rust/Swift generators,
runtime and reproducible build procedure are public. All six uploaded release
assets have server-reported digests and sizes matching the local files.

Binary ZIP checksums, device-symbol ZIP checksums and expected UUIDs changed
together. The symbol tool successfully downloaded the public assets and checked
their checksums and arm64 UUIDs. The final generic app build's embedded
`WalletCore` and `WalletCoreSwiftProtobuf` executable files are byte-for-byte
identical to the corresponding published iOS framework binaries. This verifies
the selected dependency artifacts in that local build; it does not compare
Apple's distributed app or establish whole-app reproducible binary equality.

The dependency deployment minimum is iOS 15; the app remains iOS 26. The first
candidate, `74c971197ecad485a17575ce6c583a11151356b3`, failed package resolution
because `.v15` is unavailable in its Swift-tools-5.3 manifest. The final commit
uses `.iOS("15.0")`. The manifest dump, original build failure and successful
retest remain in [the evidence](../evidence/core-app-integration).

## Verified checks on the final application commit

- Public release validation and hash-bound Gitleaks scan: passed.
- Diagnostics coverage: passed.
- Diagnostics host tests: 118 passed, two explicit skips, zero failures. The
  separate empty Swift Testing run is not counted as additional coverage.
- Targeted security host harness: 158 checks passed using synthetic credentials,
  a test clock and production vault/session code. No user Keychain or network.
- Unsigned generic iOS Release app build: passed in 467.87 seconds.
- Source identity checked before/after; the tested candidate matches the public
  merge tree. Framework bytes and UUIDs checked after the build.

The separate eight-repair native dependency suite passes 2,363 C++ tests and
113 C cryptography checks. The paired result-state and signing-parser tests
retain their original failures and repaired passes. Apple framework archives
and packaging pass. Those dependency-native results are not extra app tests.

No app runtime, simulator/device launch, signed distribution archive or App
Store behavior was tested. The archive-symbol copy phase intentionally skips an
ordinary generic build; downloaded symbols and framework identity were checked
separately. A future distribution archive still requires its archive validator.

## CI and remaining scope

Historical full GitHub run
[41264051930](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41264051930)
finished with all 44 jobs successful. It covered app commit
`02a6e8ab66c7629dcb9dd36637c683457e821d98`, not this integration commit.
Do not transfer that full-matrix result to a later target. The updated target's
full GitHub matrix and fresh GitHub execution of the complete native/Apple
dependency preparation remain outstanding.

The review remains **in progress**. Dependency implementation coverage, standard
libraries, historical binary provenance, all required final-target checks and
the remaining app source dispositions still need work. Eight repaired findings
do not establish a vulnerability-free wallet or independent certification.

## Source-read dispositions

The new binary-target manifest, provenance configuration, complete debug-symbol
downloader and declared symbol inputs were read. Checksums bind public downloads;
the ZIP path handling rejects absolute and parent paths; expected UUIDs are
checked before cache installation. No signing credentials are introduced. The
ordinary build is kept offline for symbol copying, with public acquisition as
an explicit preparation step.

The complete `TronSendPlan.swift` was additionally read for its age, address,
amount, resource, block-reference and multisig guards. It remains partially
reviewed: producer/consumer binding, fee/reservation relationships, delegated
validators and adversarial cross-wallet use still need evidence. No new defect
is asserted for that file in this increment.
