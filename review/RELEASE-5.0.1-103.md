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


## Checkpoint 5

The bundled ENS response decoder reproduced seven isolated process traps and four failing methods on the exact build 103 source. Five controls passed before repair. All sixteen methods passed after repair, including the production resolver contract response path. The complete SDK harness passed 277 tests with two skips. Diagnostics passed 119 tests with two skips, and the generic iOS Release build succeeded. [OW-2026-053](../findings/OW-2026-053.md) · [Reviewed scope and reproducible fixture](ENS-CONTRACT-DECODING.md).

Source inspection found no application call into this ENS resolver. The recorded defect is confined to its tested dependency API. ENS name processing and other signer implementations remain open review areas.

The updated CI snapshot verifies 52 archive digests and 73 report/log pairs. Seventy-one report success and two preserve failures. The separate Arc failure receipt remains in the record. Eighty-eight of 115 required validations have a passing hash-linked record on the exact build 103 tag. Five newly reviewed compiler inputs reduce outstanding direct inputs to 1,554. [CI snapshot](../evidence/5.0.1-build103/ci-artifacts-checkpoint5.json) · [Compiler coverage](../evidence/5.0.1-build103/compiler/dispositions.json).

GitHub also completed the Bitcoin address-window and backup-file reproductions. Their receipts identify the original and repaired source for each run. [Address-window results](../evidence/5.0.1-build103/ci-retests/bitcoin-indices-github.json) · [Backup-file results](../evidence/5.0.1-build103/ci-retests/backup-files-github.json).

Three scanner matches in the newer CI bundle were public source-file SHA-256 values. Each was recomputed against its source before scanning with exact-value exceptions. [Checksum review](../evidence/5.0.1-build103/ci-checkpoint5-checksum-review.json).

The full review remains open. App Store availability of later fixes and binary equivalence remain unverified.

## Checkpoint 6

The signature and contract-verification review confirmed two dependency defects. Original host cases produce five traps, twelve failing methods and three passing controls. All twenty methods pass on the repair merged in [PR #67](https://github.com/devdasx/oath-wallet/pull/67). Ten independently generated ethers vectors verify variable-length contract signatures. The public signature constructors now throw on malformed input; valid serialization is retained. [Review scope, API compatibility and findings](SIGNATURE-CONTRACT-BOUNDARIES.md).

The complete SDK suite passes 297 tests with two skips. Diagnostics passes 119 tests with two skips. The public-source scan, diagnostic coverage guard, 216 audit helper tests and unsigned generic iOS Release compilation pass. The merged tree exactly matches the tested source. The dedicated GitHub replay is pending publication of this checkpoint. [Validation receipt and logs](../evidence/5.0.1-build103/signature-contracts/validation.json).

The baseline CI snapshot now verifies 60 archive digests and 81 report/log pairs: 79 successes and two retained failures. The separate Arc failure remains recorded. Ninety of 115 required checks have passing hash-linked evidence on the exact build 103 tag. The workflow is still incomplete. Its new archive was scanned with the same independently checked source-checksum exceptions recorded in checkpoint 5. [CI receipt](../evidence/5.0.1-build103/ci-artifacts-checkpoint6.json). The earlier ENS replay has also [passed on GitHub](../evidence/5.0.1-build103/ci-retests/ens-github.json).

Twelve additional direct compiler inputs have source-hash-linked review dispositions. Of 2,357 direct inputs, 1,542 remain outstanding, 105 partially reviewed and 20 require a generated-source trace. The completion gate reports 16,621 open items across its combined ledgers. Counts include different evidence categories and are not a vulnerability count. [Compiler dispositions](../evidence/5.0.1-build103/compiler/dispositions.json).

These later source fixes have not been checked in an App Store binary. The internal verifier's current application reachability, ENS normalization, other message-signing interfaces and dependency provenance remain open. No simulator, physical-device or App Store operation was performed.

## Checkpoint 7

The checksum helper accepted malformed addresses through permissive hex conversion and could truncate output with invalid lengths. [OW-2026-056](../findings/OW-2026-056.md) records the repair and compatibility boundary. Seven of nine methods fail on the exact build 103 source; two valid controls pass. All nine pass on the repaired source. The fixture includes 24 independently generated checksum/hash vectors and verifies exact hashing input. The original failure count includes the newly explicit uppercase-prefix and malformed-provider contracts.

The merged source matches tested commit `b128544044a5d3043fca99c7d4c94af1af3b511c`. SDK tests pass 306 cases with two skips, diagnostics passes 119 with two skips, and 220 audit helper tests pass. Source scanning, the diagnostic coverage guard and unsigned generic iOS Release compilation pass. [Validation and logs](../evidence/5.0.1-build103/address-checksums/validation.json).

Five additional compiler inputs have complete narrow review dispositions and three have partial dispositions. The direct-input ledger has 1,534 outstanding, 108 partially reviewed and 20 generated inputs needing trace evidence. The full completion gate retains 16,617 open entries. ENS normalization, reverse/forward ownership checks, MessageSigner semantics and shared hex-decoder callers need further review. [Scope and API notes](ADDRESS-CHECKSUMS.md).

GitHub replay for this repair is pending publication. No App Store upload, simulator or physical-device operation was performed. The full review remains in progress.

The preceding signer checkpoint has now completed its GitHub replay successfully. All forty original/repaired case logs match their recorded checksums, and the downloaded archive matches GitHub's digest. [Hosted signer receipt](../evidence/5.0.1-build103/ci-retests/signatures-github.json). Its original traps and assertion failures remain expected replay outcomes, not missing tests.

## Checkpoint 8

The protocol-key wrappers accepted malformed hex after permissive decoding changed its bytes. They now reject incomplete/non-ASCII hex pairs before key construction, and symmetric-key constructors require exactly 32 bytes. The identical production-code fixture reproduces 153 assertions across eleven failing methods on build 103, with four valid controls. All fifteen pass after repair. One valid X25519/HKDF result matches an independent Node/OpenSSL generator, and valid 64-byte agreement records restore unchanged. The public CryptoKit symmetric-key initializer now throws. [Finding OW-2026-057](../findings/OW-2026-057.md) · [Review and compatibility](PROTOCOL-KEY-HEX.md).

[PR 69](https://github.com/devdasx/oath-wallet/pull/69) merged with a tree identical to final tested revision `235a730de504e47fb961c34f68f9426ffdbdfe6d`. SDK tests pass 321 with two skips, diagnostics passes 119 with two skips, and 224 audit helper tests pass. The public-source scan, diagnostic coverage guard and generic unsigned iOS Release build pass. The first source scan failed because two file hashes changed; the unchanged matched declarations were rechecked and only those hashes renewed. That failed check remains published. [Validation and sanitized logs](../evidence/5.0.1-build103/key-hex/validation.json).

The earlier checksum replay also passed on GitHub. Its archive digest and all eighteen result/log pairs were verified. [GitHub checksum receipt](../evidence/5.0.1-build103/ci-retests/checksums-github.json). The new protocol-key GitHub replay awaits publication of this checkpoint; local results above are separate evidence.

The direct-input ledger now records 1,531 outstanding, 109 partial, 237 reviewed, 460 generated-and-verified and 20 generated inputs needing trace evidence, out of 2,357 inputs. The full gate retains 16,616 outstanding items. The key parsing error was missed in an earlier KMS review; that earlier record remains intact and the new finding explicitly corrects it. Shared data utilities, proposal lifecycle paths, dependency provenance and the remaining application code still require review. No simulator, physical device or App Store operation was performed.

### Checkpoint 8 follow-up

The next baseline snapshot verifies 80 GitHub artifact digests and 101 report/log pairs (99 passing, two retained failures). The earlier separate Arc failure remains recorded. 104 of 115 required validations have a passing hash-linked record at the exact build 103 source. This is still a partial snapshot of an active workflow. The extracted evidence scanned clean using the three independently recomputed checksum exceptions from checkpoint 5. [Snapshot and archive digest](../evidence/5.0.1-build103/ci-artifacts-checkpoint8.json).

Two further source hypotheses were not confirmed: the session public-key optional cannot be nil through its inspected model, and empty envelopes are safely rejected on the tested host. Ten identical envelope methods pass on each of two revisions with unchanged envelope source; this is not a before/after fix. The provisional source edit was discarded. [Scope, tests and limitations](ENVELOPE-AND-SESSION-FOLLOWUP.md). No additional application change was published for these hypotheses.

The [protocol-key replay has now passed on GitHub](../evidence/5.0.1-build103/ci-retests/key-hex-github.json). The downloaded archive matches GitHub's SHA-256 digest, all thirty case/log pairs match, and the independent Node/OpenSSL reference agrees with the host fixture. The extracted artifact passed scanning with the same independently recomputed source-file checksum exceptions. This supersedes the earlier pending-CI status; it does not change the app release tag or prove App Store availability.
