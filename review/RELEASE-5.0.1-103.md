# Security review of Oath Wallet 5.0.1 (103)

The active release under review is [v5.0.1-build103](https://github.com/devdasx/oath-wallet/releases/tag/v5.0.1-build103), source commit `c7acd23bb139864a40273f405d18b479589d2b20`. The maintainer's App Store Connect screen showed iOS version 5.0.1 Waiting for Review on 2 November 2026. The screen establishes the version status. The source tag establishes the GitHub build number. The [release verification receipt](../evidence/5.0.1-build103/release-verification.json) records the checks performed when the source release was created.

The 4.1.15 series is [historical](https://github.com/devdasx/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress57). Earlier before/after tests keep their source revisions. We compared the new tag against the prior inventory, retained 1,129 identical file dispositions, and returned 47 changed or removed entries for reassessment. The new inventory covers 4,839 tracked files. The primary Xcode dependency lock matches the recorded lock hash. [Transition and Git ancestry for each recorded fix](../evidence/5.0.1-build103/transition.json).

## Findings by release

- The two Bitcoin planner fixes in [PR 53](https://github.com/devdasx/oath-wallet/pull/53) are included in the 5.0.1 tag. Both regressions passed in the tagged release's [Bitcoin suite](../evidence/5.0.1-build103/checks/OathBitcoin/OathBitcoin.xml).
- The duplicate provider lookup repair in [PR 55](https://github.com/devdasx/oath-wallet/pull/55) and the payment recovery and interrupted reset repairs in [PR 56](https://github.com/devdasx/oath-wallet/pull/56) were merged after the build 103 tag. All three [interrupted-reset upgrade cases](../evidence/5.0.1-build103/interrupted-reset/result.json) failed on the exact release tag with SQLite’s reset write fence. The same three cases passed on the subsequent repaired tree. Later changes to main cannot modify that tag or a submitted build.
- The Swift path dependency repairs were integrated after this tag in [wallet PR 57](https://github.com/devdasx/oath-wallet/pull/57). Both executables in the [tested iOS archive](CORE-SWIFT-PATH-ARTIFACTS.md) matched their published packages. Build 103 selects the earlier framework. Historical archive provenance is tracked in [OW-2026-002](../findings/OW-2026-002.md).

- An interrupted import can select the wrong Bitcoin wallet when the same words are retried under a different format. Two false successes reproduced on the release tag. [OW-2026-046](../findings/OW-2026-046.md) records the repair and the preserved retry behavior.

## Checks on this tag

The full Bitcoin host package passed 314 tests and skipped 60. Diagnostics passed 119 and skipped two. The wallet-security harness passed 158 assertions. The clipboard harness passed 33. The public source scan and diagnostics coverage check also passed. These fresh runs used the tagged source. A fresh [unsigned generic iOS Release build](../evidence/5.0.1-build103/checks/build/result.json) also passed. The resulting app declares version 5.0.1 and build 103. [Per-check results and logs](../evidence/5.0.1-build103/checks).

Application and dependency review continues. Historical results do not count as fresh results on build 103. This checkpoint makes no comparison to an Apple-distributed binary.

## Further evidence on build 103

The Electrum host suite passed 205 checks across five recovery formats. The wallet-envelope suite passed 80 checks and the restore suite passed 140. Released-app host evidence, instrumented reproductions, and checks on later repairs are recorded separately. [Host results](../evidence/5.0.1-build103/checks) · [Custody and restore code rechecked](BUILD103-CUSTODY-RECHECK.md).

The compiler trace identified 2,357 direct inputs in 47 commands. Of these, 1,570 are outstanding and 96 are partially reviewed. Eight generated secp256k1 table files were reproduced. An independent integer implementation checked 18,144 points. The public CI digest records which individual jobs were collected. [Compiler dispositions](../evidence/5.0.1-build103/compiler/dispositions.json) · [Table reproduction](SECP-TABLE-PROVENANCE.md) · [CI artifact snapshot](../evidence/5.0.1-build103/ci-artifacts.json).

Two GitHub jobs failed in the initial matrix. The [diagnostic failure investigation](BUILD103-DIAGNOSTIC-RETESTS.md) distinguishes an extra Arc diagnostic in build 103 from a timing issue in a historical test replay. Both original failures are retained.

At this checkpoint, 51 of the 115 required validations have a passing, hash-linked record on the exact release revision. The snapshot covers 24 GitHub artifact archives and 28 matched report/log pairs, including one failed replay. The Arc matrix failure has an additional receipt because its report references individual test logs. A later passing result retains its own source revision.

A separate synthetic vault fixture reproduced [OW-2026-047](../findings/OW-2026-047.md) during authenticated reopening. The repaired source passed the encrypted-envelope tests. The Arc repair also passed the complete [isolated provider package](../evidence/5.0.1-build103/ci-retests/arc-repair/OathAnkr.json).

## Checkpoint 3

Three original processes trapped on exhausted display metadata. PR 60 repaired vault family reconciliation and PR 61 repaired SQL name and sort allocation. Their final public trees matched the tested candidates. The Arc fix also passed the full provider package. All three unsigned iOS Release builds succeeded. [Wallet identity and numbering](BUILD103-WALLET-IDENTITY-AND-NUMBERING.md) · [Size and scope of the original failures](../findings/OW-2026-048.md).

The newer CI snapshot verifies 35 archive digests and 41 individual report/log pairs. Forty report success and one preserves the original failed replay. The separate Arc failure remains recorded. At this checkpoint, 61 of 115 required validations have at least one passing receipt on build 103. Of 2,357 direct compiler inputs, 1,566 remain outstanding. [CI receipts](../evidence/5.0.1-build103/ci-artifacts-checkpoint3.json) · [Compiler dispositions](../evidence/5.0.1-build103/compiler/dispositions.json).

## Checkpoint 4

Both Receive and change could issue index 99,980 before discovering that payment to it would leave fewer than the required 20 unused HD addresses. Three additional host processes trapped on damaged stored indices. [PR 62](https://github.com/devdasx/oath-wallet/pull/62) repaired both issuance paths and the state reader. The Bitcoin package passed 315 cases with 60 skips. The database package passed 739 with 72 skips. [Discovery window](../findings/OW-2026-049.md) · [Original crash frames](../findings/OW-2026-050.md).

The backup reader returned a temporary sibling file's bytes after final-entry replacement. The backup writer lost a competing file between its absence check and publication. Controlled tests reproduced the underlying errors. The repaired package passed 65 XCTest cases plus one Swift Testing case. The final source tree compiled for generic iOS Release without signing. No live iCloud run was performed. [Read finding](../findings/OW-2026-051.md) · [Write finding](../findings/OW-2026-052.md) · [Controlled results](../evidence/5.0.1-build103/backup-file-identity/deterministic-replay.json).

The ordinary and ZKP secp256k1 scalar modules passed 4,649 input pairs under each of six compiled configurations on both Apple and Ubuntu hosts. Four complete scalar representation headers were manually reviewed and eight additional headers have partial dispositions. Timing behavior and generated device code remain open. [Scalar methods and coverage](SECP-SCALAR-ARITHMETIC.md).

On the exact tag, 76 of 115 required validations now have a passing hash-linked record. The snapshot covers 44 verified CI archives and 59 matched result/log pairs. It includes two failed reports. A separate Arc job reported a third failure with per-case logs. The database job's three failed tests all reproduced the pending-reset migration defect. Each passed on the repaired public source identified in its receipt. The merged Arc diagnostic fix also required a narrow checker update. Two mutation controls verified that other unreported catches remain rejected. Of 2,357 direct compiler inputs, 1,559 remain outstanding. [CI receipts](../evidence/5.0.1-build103/ci-artifacts-checkpoint4.json) · [Migration case receipts](../evidence/5.0.1-build103/ci-retests/database-migration.json) · [Coverage checker and final build](../evidence/5.0.1-build103/ci-retests/coverage-followup.json).

Separate GitHub runs confirmed the earlier [import and diagnostic reproductions](../evidence/5.0.1-build103/ci-retests/github-confirmation.json) and [wallet-numbering reproductions](../evidence/5.0.1-build103/ci-retests/numbering-github.json).
