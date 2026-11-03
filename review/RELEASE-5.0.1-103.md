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


## Checkpoint 9

The exact-baseline workflow has now finished: 80 jobs succeeded and five failed. The final artifact snapshot verifies 85 archive digests and 105 result/log pairs: 102 successes and three failed reports. Separate job logs preserve the Arc diagnostic failure and Electrum checkout failure. The baseline still has 104 of 115 required passing validations; individual passes do not make this failed workflow successful. [Final CI receipt](../evidence/5.0.1-build103/ci-artifacts-checkpoint9.json).

The token-search failure was a test timing assumption: it allowed only 200 milliseconds for a 150-millisecond debounce plus asynchronous work. [PR 70](https://github.com/devdasx/oath-wallet/pull/70) is merged with a tree identical to tested commit `b57d05196be319d1f0530e28f667eb89023a1c4a`. The revised test waits for a controlled refresh signal and holds the old result until the new wallet's search finishes. A reset case verifies the same boundary. Both pass against unchanged production code. Deliberately removing two generation guards makes them fail with six assertions, so the tests demonstrably reject stale publication. The complete token suite passes 20 cases with four optional live checks skipped. Diagnostics passes 119 tests with two skips; source scanning, diagnostic coverage and generic unsigned iOS Release compilation pass on the exact fixture-repair commit. [Validation receipt](../evidence/5.0.1-build103/token-search-order/validation.json). [Fixture repair and exact scope](TOKEN-SEARCH-ORDER.md) · [Replay evidence](../evidence/5.0.1-build103/token-search-order/result.json).

The Electrum job never reached its tests because its Git clone timed out. Audit source preparation now isolates incomplete downloads, retries at most three times and validates the exact clean revision before publication. Eight temporary-repository tests pass; the full audit helper suite passes 240 tests. The dedicated GitHub retest passed 205 Electrum host integration checks on the exact baseline, with verified archive and log digests. [Checkout failure and repair](CHECKOUT-RECOVERY.md).

Source review covers application entry, scene lifecycle and biometric presentation. Privacy-overlay rendering remains partial because source inspection cannot prove snapshot unreadability. The token model also retains integration gaps beyond its tested search-state boundaries. The direct compiler ledger records 240 reviewed, 111 partially reviewed, 1,526 outstanding, 460 verified generated and 20 generated inputs needing trace evidence, out of 2,357 inputs. The completion gate retains 16,599 open items across its combined ledgers; this is not a vulnerability count. [Entry/scene review](APP-ENTRY-AND-SCENES.md) · [Compiler dispositions](../evidence/5.0.1-build103/compiler/dispositions.json).

The envelope boundary follow-up also passed on GitHub. Its archive digest and all twenty case/log pairs were verified. These are negative hypotheses with unchanged envelope code, not a newly fixed vulnerability. [Hosted receipt](../evidence/5.0.1-build103/ci-retests/envelope-github.json).

No simulator, physical-device, App Store upload or submission was performed. The whole-wallet review remains in progress.


## Checkpoint 10

Eleven further files have hash-linked source-review dispositions. Four narrow
components are reviewed; seven retain partial dispositions. Recovery material
publication is wallet-scoped and generation-checked; settings and backup-offer
owners were traced through lock, background and navigation cleanup. The apparent
absence of a lock observer inside the backup-offer sheet is covered by its
parent's dismissal path. No vulnerability was confirmed from that suspicion.
[Source tracing and limits](RECOVERY-DISCLOSURE-LIFETIME.md).

The production automatic-biometric prompt fixture passes 19 host checks with
network access denied and no Keychain, Face ID or simulator use. The pinned
[replay runner](../scripts/automatic-biometric-prompt.py) also passes locally;
its dedicated GitHub workflow is pending this publication. [Receipt](../evidence/5.0.1-build103/recovery-lifetime/replay.json).

A separate, explicitly scoped runtime experiment rendered the unchanged privacy
cover over synthetic labels in one isolated iPhone 17 Pro simulator on iOS 27.0.
The control was readable; settled light/dark covers obscured the fixture text.
Vision recognized ten control labels, none in covered hierarchy renders and only
status-bar content in the dark compositor image. The simulator was shut down and
deleted. The full wallet app was not launched. Real app-switcher snapshot timing,
other OS/accessibility combinations and resistance to reconstruction remain open.
No production fix was justified. [Captures and hashes](../evidence/5.0.1-build103/privacy-cover/result.json)
· [Reproduction and limitations](../fixtures/privacy-cover/README.md).

The audit checkout helper ignored command-line arguments, so asking for help
started a download. Two mocked-download tests fail before argument validation;
all ten checkout tests pass afterward, within the 245 passing audit helper tests.
This is an audit-tool correction, not a wallet vulnerability. The interrupted
setup attempt and failed-before log are preserved. [Validation](../evidence/5.0.1-build103/privacy-cover/validation.json).

The complete review remains open with 16,595 combined ledger items. Of 2,357
direct compiler inputs, 244 are reviewed, 118 partial, 1,515 outstanding, 460
generated-and-verified and 20 need a generated-input trace. These are coverage
counts, not vulnerability counts. Application source remains unchanged from the
previous tested public repair tree; no new app build or App Store operation is
claimed for this evidence-only checkpoint. No physical device was used.


## Checkpoint 11

Private-key disclosure source tracing covers account ownership, authentication,
late-response invalidation, address-bound derivation, warning/reveal and cleanup.
Two previously outstanding compiler inputs are now partially reviewed; remaining
UI and dependency obligations are explicit. No new wallet vulnerability or
application fix is claimed in this checkpoint.
[Detailed review and limits](PRIVATE-KEY-DISCLOSURE.md).

The existing, previously unlisted private-key browser fixture passes **305 host
assertions** at the exact build 103 baseline. It executes production vault/SQL
and Bitcoin-family leaf derivation with a substituted application key engine.
It does not execute the application's non-UTXO export adapter, UIKit or OS
biometric authorization. The audit runner now requires a single final summary
with at least the pinned fixture's 305 assertions; successful compilation alone,
missing/duplicate summaries and reduced assertion counts cannot pass. Five
parser tests cover this gate. All 250 audit helper tests pass.
[Host result](../evidence/5.0.1-build103/private-key-disclosure/private-keys.json)
· [Audit helper validation](../evidence/5.0.1-build103/private-key-disclosure/validation.json).

The token-search hosted replay passed the full suite and the controlled mutation
checks; its production code is unchanged by the earlier test repair. The
production automatic-biometric prompt fixture also passed all 19 host checks on
GitHub. Downloaded archives match GitHub digests, and report/log pairs were
independently verified. Two scanner matches were recomputed artifact checksums,
not credentials; the narrow exceptions and final zero-match scan are preserved.
[Token replay](../evidence/5.0.1-build103/ci-retests/token-search-order-github.json)
· [Prompt replay](../evidence/5.0.1-build103/ci-retests/privacy-prompt-github.json).
These supersede the respective pending-workflow statements in earlier checkpoints.
The newly added dedicated private-key GitHub workflow remains pending at publication.

A revealed private key intentionally remains in its model on cancellation, while
the app-switcher blur is optional. The root's foreground lock presentation does
not by itself establish background snapshot safety. Actual app-level snapshot
behavior with privacy disabled remains an unresolved runtime concern; the earlier
explicitly attached blur probe does not settle it. No new simulator or physical
device check was performed for this checkpoint.

There are **105 of 116** required exact-baseline checks with passing hash-linked
records. The direct compiler ledger has 244 reviewed, 120 partial, 1,513
outstanding, 460 generated-and-verified and 20 generated inputs needing trace,
out of 2,357 inputs. The combined gate remains at 16,595 open items. These are
coverage counts, not vulnerability counts. The whole-wallet review remains
in progress. No application code, App Store upload or submission changed.


## Checkpoint 12

The open retained-private-key snapshot concern from checkpoint 11 reproduced.
With App Switcher Privacy disabled, a revealed key stayed in the model after the
session locked and entered actual OS-created scene snapshots. The key in the
experiment was deliberately invalid synthetic text. The fixture retained the
production root, scene, disclosure model and value page while substituting initial
wallet loading, home content and the secret reader. It is a bounded component
experiment, not a full export UI run. All substitutions and failed setup attempts
are preserved. [Finding](../findings/OW-2026-058.md) ·
[Reproduction](../fixtures/private-key-snapshot/README.md).

[PR #71](https://github.com/devdasx/oath-wallet/pull/71) makes every lock/background
cancellation discard the revealed and pending value and require fresh authorization.
The same model patch removed the synthetic value from all four after snapshots;
both foreground controls remained readable. The model bytes match tested commit
`b5621109b64d606dcf6cd906d2c4f2c2f9e78686`. The runtime experiment otherwise uses
the baseline plus the documented fixture substitutions. The production repair
was separately compiled in unsigned generic iOS Release configuration. Its merge
`00d26c005fbc3f811615b23b865bb50ef7b6619f` has the identical tested tree.

The identical eleven host cases yield **seven passes/four failures before**, and
**eleven passes/zero failures after**. The broader host harness passes **791 checks**.
Diagnostics pass **119 tests, two skipped**. Public source validation, diagnostic
coverage and the zero-match secret scan pass. Native Back during an active session
continues to work; old acknowledgement cannot revive a cleared disclosure.
[Machine-readable evidence](../evidence/5.0.1-build103/private-key-snapshot/manifest.json).
The new read-only GitHub workflow replays pinned before/after production models;
its execution is recorded separately from local results.

The previously pending private-key browser GitHub run completed successfully with
**305 assertions** at the exact baseline. Its archive digest and report/log hashes
were verified and the archive is attached durably to this checkpoint.
[Hosted receipt](../evidence/5.0.1-build103/ci-retests/private-key-browser-github.json).
This does not expand the substituted host adapter's scope.

The isolated simulator used for the unresolved snapshot question was shut down
and deleted. No physical device or App Store operation occurred. The baseline's
remaining validation and source/dependency gaps remain open. This is a progress
release, not a whole-wallet completion verdict or independent certification.

Checkpoint 12 audit-helper validation: **262 tests passed**. The combined gate
retains **16,596 open items**; the extra finding remains counted against the
unchanged historical baseline despite its later public repair. Direct compiler
coverage counts are unchanged. These counts are not counts of vulnerabilities.


## Checkpoint 13

The all-wallet backup model rechecked operation ownership after a successful
record read, but omitted that check when the read threw. A controlled host replay
confirms an old canceled read can set a newer batch's failure and increment its
counter. [OW-2026-059](../findings/OW-2026-059.md) is a low-severity backup-status
integrity/reliability defect; no persisted backup corruption, key disclosure or
authorization bypass was demonstrated.

[PR #73](https://github.com/devdasx/oath-wallet/pull/73) adds the same ownership and
cancellation check to the error path. The identical **15 cases** yield **12 passes,
three failures before**, and **15 passes, no failures after**. The test extracts
the real production model unchanged; synthetic boundaries hold/release database
callbacks using continuations and explicit completion barriers. It does not run
SwiftUI, iCloud, actual storage failures or cryptography. Current legitimate
failures remain visible. The initial 12-case exploration and failed output remain
in evidence. [Reproduction](../fixtures/backup-presentation/README.md).

At `a904515793b087289140e4411924f030b3fe61ff`, public release validation,
diagnostics coverage, a zero-match secret scan, **119 diagnostics tests (two
skipped)** and unsigned generic iOS Release compilation pass. Merge
`cfd43d36f6e1ee58845005bd817b069096843030` includes concurrent Website-only changes;
all non-Website tracked files match the tested commit. The manifest lists the
actual delta rather than claiming whole-tree identity.
[Checks and hashes](../evidence/5.0.1-build103/backup-presentation/manifest.json).

Full source reads covered the all-wallet backup model/page, backup-password form,
secure-input bridge and native entry field. These now have **partial** dispositions:
keyboard, accessibility, autofill, system snapshot and complete UI integration
remain outside this host run. The field's deactivation concealment is a source
observation, not a new runtime result. [Review limits](BACKUP-PRESENTATION.md).

**266 audit-helper tests pass.** Direct compiler input dispositions now include
244 reviewed, 124 partial, 1,509 outstanding, 460 generated-and-verified and 20
needing trace. The combined completion gate retains **16,597 open items**, including
later-fixed defects still present in the unchanged historical baseline. These
are coverage counts, not vulnerability counts. The whole-wallet review remains
incomplete. The audit-only hosted callback replay is recorded separately; no
hosted success is inferred from the local replay. No simulator, physical-device
or App Store operation was performed for this backup follow-up.


## Checkpoint 14

Two hosted reproductions now complete the previously pending receipts. The
[private-key cleanup run](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41564389687)
records **7 passes / 4 failures before**, **11 passes / 0 failures after**.
The [backup progress run](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41566034707)
records **12 passes / 3 failures before**, **15 passes / 0 failures after**.
Archive sizes and GitHub SHA256 digests, result/log hashes, exact case outcomes,
source model bytes and overlaid fixture hashes were independently checked after
download. Both original archives accompany this checkpoint's release.
[Private-key receipt](../evidence/5.0.1-build103/ci-retests/private-key-disclosure-github.json)
· [Backup receipt](../evidence/5.0.1-build103/ci-retests/backup-presentation-github.json).
These hosted tests are model/host evidence, not a new OS snapshot test.

**22 controlled restore-model checks pass locally** on unchanged production
source. Removing one ownership guard from a temporary copy yields exactly three
failures, demonstrating sensitivity to the tested stale callbacks. Continuation
barriers cover account changes, duplicate requests, cancellation-resistant read
errors and late save completion. Cloud, cryptography and persistence are
synthetic boundaries; this is not live iCloud, full vault or UIKit coverage.
[Reproduction](../fixtures/cloud-restore-lifecycle/README.md) ·
[Source review and limitations](CLOUD-RESTORE-LIFECYCLE.md).
The [hosted restore replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41567766015)
is queued at this checkpoint; local success is not a hosted result.

**273 audit-helper tests pass.** Four newly documented partial dispositions
leave direct compiler coverage at **244 reviewed, 128 partial, 1,505 outstanding,
460 generated-and-verified and 20 needing trace**. The combined completion gate
still has **16,597 open items**. These are coverage/validation entries, not a count
of vulnerabilities. No new application defect was confirmed in this follow-up.
The app source is unchanged; its prior unsigned Release build is retained, not
reported as a new build. No simulator, physical device or App Store operation was
performed. The whole-wallet review remains in progress.
