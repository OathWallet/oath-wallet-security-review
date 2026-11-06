# Oath Wallet security review

Checkpoint 39 adds 27 passing local Solana/TON message-signing methods, with zero skips, and one expected failure when TON domain binding is deliberately removed. Five source/range dispositions remain partial; no new app vulnerability or app change is claimed. Hosted replay is pending. [Exact evidence and limitations](review/MESSAGE-DOMAINS.md).

Checkpoint 38 confirms Medium finding OW-2026-077: a Solana stake authority change could receive a fee-only preview. [Open PR #117](https://github.com/OathWallet/oath-wallet/pull/117) rejects unsupported staking requests and simulated stake changes. Two controls pass and seven methods fail before repair (44 expected assertions); all 67 selected methods pass afterward. The unsigned generic iOS Release build passes at exact repair commit `f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e`. Hosted replay is pending; this repair is not yet merged or claimed distributed by Apple. [Evidence and limitations](review/SOLANA-STAKE-AUTHORITY.md).

Checkpoint 37 adds 13 multisignature methods passing locally and on GitHub: 527 Aptos policies, 54 Sui policies, all 65,536 Sui signer bitmaps and 27 THORChain policies. A separately weakened threshold check produces three expected assertions. Twenty-two source/range dispositions remain partial; no new app defect or app change is claimed. The terminal GitHub artifact and every case log are hash-verified. [Evidence and limitations](review/MULTISIG-AUTHORITY.md).

Checkpoint 36 adds 40 Sui, NEAR and Polkadot consent methods passing locally and on GitHub with zero skips: altered requests, authority actions, message domains and consent lifetime boundaries. A deliberately weakened control produces three expected assertions. Fourteen source/range dispositions remain partial; no new app defect or app change is claimed. The terminal GitHub artifact and every case log are hash-verified. [Evidence and remaining scope](review/MULTICHAIN-CONSENT.md).

Checkpoint 35 adds 28 EVM methods passing locally and on GitHub with zero skips: cross-chain replay, signed intent, wire tampering, every supported Safe threshold and delegation-removal binding. The deliberately weakened control produces four expected assertions. Fifteen source/range dispositions remain partial; no new app defect or app change is claimed. [Evidence and remaining scope](review/EVM-CONSENT.md).

Checkpoint 34: locally, 56 inherited and 2,647 new installation-key assertions pass. On GitHub, the inherited file-backup-exclusion assertion fails; the separate 2,647 cryptographic assertions pass. The hosted aggregate is failed and unresolved. The 12-failure purpose-binding mutation control behaves as expected on both hosts. Twelve hash-bound source/range dispositions remain partial. No new app defect or app change is claimed. [Production trace, evidence and limitations](review/INSTALLATION-BINDING.md).


Checkpoint 33 adds 27 passing Bitcoin signing/consent methods: 1,040 signature-mode combinations, mixed owned/foreign inputs, signed-wire mutations and consent-plan checks. A separate weakened control fails exactly four assertions; the first harness expectation error is preserved. Eleven source dispositions remain partial. No new app defect or app change is claimed. [Evidence and remaining gaps](review/BITCOIN-CONSENT.md).

Checkpoint 32 adds 20 passing typed-data/sign-in host methods, including 616 independently generated hash/signature vectors and 192 invalid-value cases. A deliberately broken domain-binding build fails the expected assertions. Nine file/range dispositions remain partial; no new app vulnerability or app change is claimed. [Reproduction, evidence and limitations](review/TYPED-CONSENT.md).

Checkpoint 31 adds 25 passing offline Aptos signing and provider-intent methods, with an expected failed-method control when exact-byte binding is deliberately removed. Eight source files have hash-bound partial dispositions. No new application defect or app change is claimed. Original fixture-build failure and remaining lifecycle/dependency gaps are preserved. [Evidence and limitations](review/APTOS-INTENT.md).

Checkpoint 30 records the missing Solana nonce-response value repair in [PR #105](https://github.com/OathWallet/oath-wallet/pull/105). Four controls pass and two methods fail before repair; all 58 selected Solana methods pass afterward with networking denied. Diagnostics, publication checks and separate unsigned iOS Release builds at the repair and merge commits pass. [Hosted replay](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42217601211) reproduces these same scoped test results on another runner; its downloaded logs and checksums are preserved. These are scoped results; the whole-wallet audit remains incomplete. [Evidence and limitations](review/SOLANA-NONCE-VALUE.md).

Checkpoint 29 repairs stale or malformed Solana WalletConnect response contexts in [PR #100](https://github.com/OathWallet/oath-wallet/pull/100). The same eleven methods change from three passing controls and eight expected failures to all passing; all 52 selected Solana methods pass after repair. Diagnostics, publication scans and unsigned generic iOS Release compilation pass. Hosted replay succeeded and its downloaded artifact is hash-verified; the whole-wallet audit remains incomplete. [Evidence and limitations](review/SOLANA-RPC-CONTEXT.md).

Checkpoint 28 repairs Solana transaction buffer indexing in [PR #97](https://github.com/OathWallet/oath-wallet/pull/97). The same five methods change from two passing controls and three expected failures to all passing; 41 selected Solana methods pass after repair. Diagnostics and unsigned generic iOS Release compilation pass. The repair and merged source trees are identical. Hosted replay succeeded and its downloaded artifact is hash-verified; the whole-wallet audit remains incomplete. [Evidence and limitations](review/SOLANA-BUFFER-ORIGIN.md).

Checkpoint 27 records Solana delegation-consent finding OW-2026-073, reported against build 104 and already repaired in public source. An identical regression fails on the reported commit and passes on pinned 5.0.3 (105) source; all 36 selected Solana host tests pass. The GitHub replay also passed and its downloaded evidence is hash-verified. Original failures, the excluded discovery attempt and partial source dispositions remain visible. The whole-wallet audit remains incomplete. [Evidence and limitations](review/SOLANA-CONSENT.md).

Build 104 checkpoint 26 validates the scanner state machine with 137,256 bounded transition prefixes, 6,400 concurrent capture claims and 106 existing handoff checks. All five deliberately broken controls fail the expected groups. Two additional files gain partial source review; no new production defect or app change is claimed. The earlier backup-settings GitHub replay is downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](review/SCANNER-STATE-BOUNDARIES.md).

Build 104 checkpoint 25 adds 52 passing single-wallet backup-model checks and 15 current-source all-wallet regression checks. Removing the completion-ownership guard in a disposable copy produces 12 expected failures. Two more files gain partial source review; no new app defect or app change is claimed. The whole-wallet audit remains incomplete. [Evidence and remaining scope](review/BACKUP-SETTINGS-LIFECYCLE.md).

Build 104 checkpoint 24 retests the existing backup file-boundary repairs against current source: three historical failing methods become three passes. A separate pristine backup package passes 64 XCTest methods plus one Swift Testing reset-barrier test. Two source files gain partial dispositions and the package manifest gains a scoped reviewed disposition. No new app change is claimed; the whole-wallet audit remains incomplete. [Evidence and remaining scope](review/CLOUD-FILE-RECHECK.md).

Build 104 checkpoint 23 adds twelve passing Stellar provider/contract and WalletConnect methods, with 20 malformed-state cases and 12 malformed simulations. A disposable authorization mutation causes the expected assertion failure. One additional file gains partial source review; no new app defect or change is claimed. Earlier decoding and multisignature GitHub replays are downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](review/STELLAR-PROVIDER.md).

Build 104 checkpoint 22 adds ten passing Stellar multisignature methods, covering all 209 supported threshold combinations and SDK-decoded atomic setup. A disposable threshold mutation produces 627 expected assertion failures. Three files gain partial source review; no new defect or app change is claimed. Timestamp repair and persistence GitHub replays are downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](review/STELLAR-MULTISIG.md).

Build 104 checkpoint 21 adds seven passing production-parser methods backed by deterministic independent Stellar vectors and 1,776 truncation cases. A disposable checksum mutation produces 64 expected assertion failures. Two files gain partial source review; no new app defect or implementation change is claimed. The whole-wallet audit remains incomplete. [Evidence and remaining scope](review/STELLAR-DECODING.md).

Build 104 checkpoint 20 adds 31 passing offline Stellar persistence and generic refresh-worker methods, including database reopening, signature preservation, duplicate-wallet isolation and retries. Seven files have hash-bound partial read evidence; four were previously outstanding. No application implementation changes or new confirmed defect are claimed. The earlier XDR/SCALE hosted replay is downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](review/STELLAR-PERSISTENCE.md).

Build 104 checkpoint 19 fixes malformed Stellar plan timestamps that could crash structural validation during saved-send verification. Fresh before/after builds reproduce three crashes and then six passing methods; 40 adjacent methods pass. Valid saved transactions retain their bytes and signatures. Earlier Sui/XRP history and Sui signing GitHub replays are downloaded and hash-verified. The full audit remains incomplete. [Evidence and remaining gaps](review/STELLAR-PLAN-TIMESTAMPS.md).

Build 104 checkpoint 18 repairs nonzero-origin buffer crashes in the Stellar XDR and Polkadot SCALE readers. The identical nine-method fixture changes from three passes/six SIGTRAPs to nine passes; 40 adjacent send and WalletConnect methods pass. Diagnostics and generic unsigned iOS Release compilation pass. Public API/internal parser robustness is demonstrated, not a remote exploit. The full audit remains incomplete. [Evidence and remaining gaps](review/XDR-SCALE-BUFFERS.md).

Build 104 checkpoint 17 repairs a Sui transaction-parser crash on nonzero-origin Data. The identical fixture changes from one passing control/two SIGTRAPs to three passes. All 34 signing and WalletConnect methods pass, including 336 independent hash vectors; diagnostics and generic unsigned iOS Release compilation also pass. This is parser API robustness, not a demonstrated remote app exploit. [Evidence and remaining gaps](review/SUI-SIGNING-BOUNDARIES.md).

Build 104 checkpoint 16 repairs a Sui history restart overflow and missing Sui/XRP cursor-account checks. The same four host cases change from one passing control, two assertion failures and one SIGTRAP to all passing. All 22 adjacent offline methods pass. Earlier NEAR and TRON/TON hosted repair runs are now downloaded and hash-verified. [Evidence and remaining limits](review/HISTORY-RESTART-BOUNDARIES.md).

Build 104 checkpoint 15 repairs delayed TRON/TON inventory freshness: the same five host cases change from two passes/three failures to five passes. Old in-flight balance responses no longer satisfy the post-send freshness check. The earlier NEAR journal-race hosted replay is downloaded and hash-verified. [Exact checks and remaining gaps](review/INVENTORY-FLIGHT-TIME.md).

Build 104 checkpoint 14 adds four scoped partial source dispositions for TRON/TON ledger refreshes and 27 passing existing offline ledger/journal methods. The earlier activation/bootstrap GitHub replay is downloaded and hash-verified. No new app defect or app-source change is claimed; snapshot freshness and full adapter integration remain open. [Evidence and limitations](review/TRON-TON-LEDGER-BOUNDARIES.md).

Build 104 checkpoint 13 repairs [OW-2026-066](findings/OW-2026-066.md): NEAR post-send refresh no longer completes when the sent token read failed or returned a pre-execution block. The same six methods change from two passes/four failures to all passing; 24 adjacent methods and unsigned iOS Release compilation pass. [Evidence and remaining gaps](review/NEAR-BALANCE-FRESHNESS.md).

Build 104 checkpoint 12 adds nine passing database-journal methods, including controlled duplicate-wallet races, reopened terminal records and malformed-receipt rollback. Two production files gain partial source review, and the existing journal test file is reviewed as test code. [Scope and remaining work](review/NEAR-JOURNAL-RACES.md).

Build 104 checkpoint 11 adds six passing activation/bootstrap-authority host methods and an expected failing bootstrap-key mutation. Two application files gain scoped partial source review; full app integration remains open. [Results and remaining gaps](review/NEAR-MULTISIG-ACTIVATION.md).

Build 104 checkpoint 10 adds six passing staged-submission host methods and an expected failing request-binding mutation. The preceding paired native-contract GitHub replay is now downloaded and verified. [Scope and remaining gaps](review/NEAR-MULTISIG-LIFECYCLE.md).


This is a **maintainer-commissioned, Codex-led security review** of the public
Oath Wallet application. It is not independent certification, a guarantee of
zero vulnerabilities, or a comparison with the installed App Store binary.

**Current application release:** [Oath Wallet 5.0.2 (104)](https://github.com/OathWallet/oath-wallet/releases/tag/v5.0.2-build104), released source commit `7ffd0f449c3312d9fafd01eda59c6b9eb813f9ca`. Apple approval was confirmed on 5 November 2026. [Current publication status](review/CURRENT-PUBLICATION.md) distinguishes that release from the exact source commits tested in this review. The build-104 series began at `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`; its inventory and historical results remain pinned. [Review series and validation](review/RELEASE-5.0.2-104.md) · [Pinned source manifest](scope/source.json) · [Historical build-103 checkpoints](review/RELEASE-5.0.1-103.md).

**The whole-wallet review is not complete.** Test success does not turn
outstanding source into reviewed source. Consult the [report](review/REPORT.md),
[coverage ledger](scope/inventory.json), [findings](findings), and
[Actions runs](https://github.com/OathWallet/oath-wallet-security-review/actions) and
[acceptance checklist](review/ACCEPTANCE.md) together.

**Build 104 checkpoint 9.** A native-only SDK mock ABI repair makes contract rejections testable on the pinned compiler. The identical 20-method fixture changes from nine valid passes/ten abort blockers/one invalid fixture pass to eighteen valid passes/two invalid fixture passes; both bad inherited tests remain excluded. A member-admission mutation causes exactly four failures. GitHub also passed the independent multisig vectors and verifier controls, with downloaded hashes verified. [Paired evidence and remaining scope](review/NEAR-CONTRACT-REJECTIONS.md).

**Build 104 checkpoint 8.** Native contract-source tests now run in a documented adapted harness: nine methods pass, five remain blocked by the old SDK panic boundary, and one inherited false-positive fixture is excluded. Exact mock transfer actions and retained confirmations after authorized membership removal are recorded without claiming WASM execution. The separate ten-method GitHub app replay is downloaded and hash-verified. [Results, reproduction and open questions](review/NEAR-CONTRACT-NATIVE.md).

**Build 104 checkpoint 7.** Fifty independent NEAR multisig bundles cover 188 transaction parts; three host methods and five verifier controls pass. An isolated nonce mutation is detected. The original signature-byte fixture assumption and its correction remain visible. GitHub has also reproduced the earlier reader crash and repair, with downloaded evidence verified. [Results and remaining scope](review/NEAR-MULTISIG-VECTORS.md).

**Build 104 checkpoint 6.** Ten existing NEAR multisig methods pass with runtime networking denied. Four bundled contract/source/license copies match pinned upstream bytes. Two application files gain partial source dispositions. Upstream Rust tests failed to compile in older dependencies; contract runtime and source-to-WASM reproduction remain unresolved. [Evidence and remaining scope](review/NEAR-MULTISIG-BOUNDARIES.md). No new app defect or app change is claimed.

**Build 104 checkpoint 5.** [OW-2026-065](findings/OW-2026-065.md) repairs a NEAR transaction-reader crash on Data slices. The same fixture changes from four passes and one SIGTRAP to five passes; 82 signatures verify independently and 26 adjacent NEAR methods pass. Diagnostics and unsigned iOS Release compilation pass. [Reproduction and remaining scope](review/NEAR-SIGNING-VECTORS.md). Three more source files have partial dispositions. Hosted signing-removal and journal replays are now verified; the new reader replay is tracked separately.

**Build 104 checkpoint 4.** Eight database journal/removal methods pass with runtime networking denied; four more files have partial source coverage. GitHub also passed the earlier 24 NEAR provider/request methods and unsigned iOS Release compilation at the merged repair. Downloaded artifact and log hashes are verified. Signing-race hosted results were subsequently verified in checkpoint 5. [Scope and remaining gaps](review/NEAR-JOURNAL-BOUNDARIES.md). No new application defect was confirmed by this selection.

**Build 104 checkpoint 2.** [OW-2026-064](findings/OW-2026-064.md) fixes signing and permission consent that could survive wallet removal. Local tests record 66 account-read and 14 pending-consent passes, 616 broader assertions, diagnostics and unsigned iOS Release compilation. Original failures and intermediate regressions remain visible. [Repair, reproduction and remaining scope](review/CONNECT-REMOVAL-READ.md) · [Merged PR81](https://github.com/OathWallet/oath-wallet/pull/81). Hosted replay is verified in checkpoint 5; the whole-wallet review remains incomplete.

**NEAR follow-up.** Twenty-four existing production-package methods pass locally and on GitHub with runtime networking denied; downloaded receipts and logs are hash-verified. Three provider/plan/request files receive partial source dispositions; no new application defect is confirmed. [Exact scope, evidence and remaining work](review/NEAR-PROVIDER-BOUNDARIES.md).

Four chain wallet adapters now have hash-bound partial source coverage. The compiler ledger is reproducible from the canonical inventory, including 16 preserved historical partial dispositions. [Read scope and remaining work](review/CHAIN-WALLET-ADAPTERS.md) · [Coverage reconciliation](review/COMPILER-DISPOSITION-RECONCILIATION.md). This does not close the whole-wallet review.

**Historical build-104 prerelease checks.** The source includes the public fixes through PR #77. Its exact-target checks pass: 748 database tests (72 skips), 119 diagnostics tests (two skips), source/secret checks and unsigned iOS Release compilation. The built app reports 5.0.2 / 104. [Current audit, carried evidence and gaps](review/RELEASE-5.0.2-104.md). Earlier checkpoints below remain historical.

**Checkpoint 21.** A controlled encrypted-write pause reproduced a race between wallet removal and a newly signed transaction journal. The same fixture changes from 19 passes/four failures to all 23 passing after the durable reservation repair; 30 restart checks cover interrupted persistence. Earlier delayed-authentication results are now verified on GitHub. [Reproduction, validation and remaining scope](review/CONNECT-REMOVAL-RACE.md).

**Checkpoint 20.** Delayed authentication across removal, restore, failed persistence and locking passes 38 checks with production vault and EVM imported-key signers. A deliberately stale envelope produces exactly two failures, demonstrating sensitivity to that guard. No new app defect is confirmed by this matrix. [Scope, evidence and remaining races](review/CONNECT-REMOVAL-AUTHORIZATION.md).

**Checkpoint 19.** Pending dApp submissions now block removal of an active wallet in [PR #76](https://github.com/OathWallet/oath-wallet/pull/76). Original and intermediate compatibility failures are preserved; all five final methods pass. Full database tests, diagnostics and unsigned iOS Release compilation pass. Legacy cleanup remains compatible; signing/removal concurrency remains open. [Evidence and limits](review/CONNECT-REMOVAL.md).

**Checkpoint 18.** The shipped XRP JavaScript codec rebuilds byte-for-byte from its locked source. Six new actual-package request/signature boundary methods pass, including the isolated network-denied replay. The newly enumerated 170 upstream input files remain explicitly outstanding; a matching bundle does not certify their implementations. [Evidence and scope](review/XRPL-CODEC-BOUNDARIES.md).

**Checkpoint 17.** XRP Connect simulation validation is repaired in [PR #75](https://github.com/OathWallet/oath-wallet/pull/75): eight assertions fail across two methods before; all six provider methods pass afterward. Broader XRP tests, diagnostics and unsigned iOS Release compilation pass. The earlier signing matrix also passes on GitHub with verified archive hashes. [Evidence and limits](review/XRPL-CONNECT-SIMULATION.md). The full review remains incomplete.

**Checkpoint 16.** Four offline production-package methods pass: 61 complete XRP signed transactions and hashes match the independent pinned SDK, 13 RIPEMD vectors match OpenSSL-backed results, and altered plans/envelopes/signer sets are rejected. Five source files gain partial coverage. No new application defect is confirmed by this matrix. [Scope, reproduction and remaining provider hypothesis](review/XRPL-SIGNING-MATRIX.md).

**Checkpoint 15.** [OW-2026-060](findings/OW-2026-060.md) repairs an XRP issued-token quote failure for valid large amounts. The same 4,900 deterministic arithmetic cases change from 4,843 passes/57 failures to all passing. Targeted package regressions, diagnostics, source validation and unsigned iOS Release compilation pass. [Reproduction, scope and limits](review/XRPL-AMOUNT-ARITHMETIC.md) · [Checkpoint evidence](review/RELEASE-5.0.1-103.md#checkpoint-15). No live ledger or App Store result is claimed.

**Checkpoint 14.** GitHub reproduced both repairs: private-key cleanup changes from seven passes/four failures to eleven passes, and backup progress changes from twelve passes/three failures to fifteen passes. Downloaded artifact, log and source hashes were verified. Twenty-two new restore-model host checks pass and detect a deliberately broken guard; four more files have partial source coverage. [Evidence](review/RELEASE-5.0.1-103.md#checkpoint-14).

**Checkpoint 13.** A canceled backup-record read could overwrite a newer batch's error/progress. [OW-2026-059](findings/OW-2026-059.md) is repaired in [PR #73](https://github.com/OathWallet/oath-wallet/pull/73). The same fifteen production-model cases change from twelve passes/three failures to all fifteen passing. Diagnostics and unsigned iOS Release compilation pass; no backup corruption or key disclosure was demonstrated. Four additional files have partial source review dispositions with UI limits preserved. [Evidence](review/RELEASE-5.0.1-103.md#checkpoint-13).

**Checkpoint 12.** A synthetic runtime experiment confirmed that a revealed private key could survive into app-switcher snapshots with optional privacy disabled. [OW-2026-058](findings/OW-2026-058.md) is repaired in [public PR #71](https://github.com/OathWallet/oath-wallet/pull/71): the same host cases change from seven passes/four failures to eleven passes, 791 broader wallet checks pass, and unsigned iOS Release compilation succeeds. Actual OS snapshot evidence and all substitutions are preserved. This does not establish full export UI coverage, every OS transition, or App Store delivery. [Evidence and limits](review/RELEASE-5.0.1-103.md#checkpoint-12).

**Checkpoint 11.** Private-key ownership and leaf-export checks pass 305 assertions on the exact build 103 baseline. Source tracing covers the export adapter separately from the substituted host engine. Token-search and automatic-prompt GitHub reruns passed with verified artifact/log hashes. The retained-key app-switcher snapshot question remains open. [Scope and evidence](review/RELEASE-5.0.1-103.md#checkpoint-11).

**Checkpoint 10.** Recovery disclosure and passcode setup source tracing adds eleven scoped file dispositions. Nineteen automatic-prompt host checks and 245 audit helper tests pass. A single synthetic simulator experiment found no readable fixture text through the settled privacy cover; actual app-switcher snapshot timing remains open. No application change was needed for these hypotheses. [Scope and evidence](review/RELEASE-5.0.1-103.md#checkpoint-10).

**Checkpoint 9.** Token-search race tests now use controlled interleavings instead of timing guesses; they pass on unchanged production code and detect an intentionally broken variant. The final baseline workflow preserves five failed jobs and 105 verified result/log pairs. [Evidence, test repairs and remaining scope](review/RELEASE-5.0.1-103.md#checkpoint-9).

**Build 103 checkpoint 8.** Protocol-key constructors now reject malformed hex and invalid symmetric-key sizes. Eleven original failing methods and four valid controls are preserved; all fifteen pass after repair. The complete SDK suite passes 321 tests with two skips, and unsigned iOS Release compilation succeeds. [Finding and compatibility](review/PROTOCOL-KEY-HEX.md) · [Validation](evidence/5.0.1-build103/key-hex/validation.json) · [Merged fix](https://github.com/OathWallet/oath-wallet/pull/69). These are WalletConnect messaging keys; the tests do not demonstrate wallet-secret disclosure or a consent bypass.

**Build 103 checkpoint 7.** The address checksum helper now rejects malformed inputs before changing their bytes. Nine production-code methods pass, including 24 independent vectors. The full SDK suite passes 306 tests with two skips, and unsigned iOS Release compilation succeeds. The source API now throws. [Finding and scope](review/ADDRESS-CHECKSUMS.md) · [Validation](evidence/5.0.1-build103/address-checksums/validation.json) · [Merged fix](https://github.com/OathWallet/oath-wallet/pull/68). The helper's application reachability remains unproven.

**Build 103 checkpoint 6.** Signature constructors now reject malformed encodings safely, and contract verification uses actual signature lengths and exact supported replies. Five original traps and twelve failing methods are preserved; all twenty methods pass after repair. The full SDK suite passes 297 tests with two skips, and unsigned iOS Release compilation succeeds. [Findings and compatibility](review/SIGNATURE-CONTRACT-BOUNDARIES.md) · [Merged repair](https://github.com/OathWallet/oath-wallet/pull/67) · [Validation](evidence/5.0.1-build103/signature-contracts/validation.json). The dependency verifier's application reachability remains unproven.

**Build 103 checkpoint 5.** The bundled ENS response decoder trapped on malformed input and accepted several invalid encodings. The exact-release replay preserves seven crashing processes, four failing methods and five passing controls. All sixteen pass on the merged repair. Application reachability remains unproven. [Finding](findings/OW-2026-053.md) · [Tests and review scope](review/ENS-CONTRACT-DECODING.md) · [CI evidence](evidence/5.0.1-build103/ci-artifacts-checkpoint5.json).

**Build 103 checkpoint 4.** Public source repairs cover Bitcoin-family address discovery and backup file races. The original failures, fixed cases and build receipts are recorded separately from the submitted build. [Address issuance](findings/OW-2026-049.md) · [Backup reads](findings/OW-2026-051.md) · [Conflicting backup writes](findings/OW-2026-052.md) · [Scalar arithmetic](review/SECP-SCALAR-ARITHMETIC.md).

**Build 103 checkpoint 3.** Synthetic authenticated vault and SQLite records reproduced three integer overflows. Public source repairs passed the focused tests, full database package and unsigned iOS builds. [Vault finding](findings/OW-2026-047.md) · [Database finding](findings/OW-2026-048.md) · [Exact-target CI evidence](evidence/5.0.1-build103/ci-artifacts-checkpoint3.json).

**Build 103 checkpoint 2.** Changing recovery format after an interrupted wallet import could return a different Bitcoin wallet. The error reproduced on the tagged source. [Finding and regression](findings/OW-2026-046.md) · [Application and dependency checks](review/RELEASE-5.0.1-103.md) · [Direct input coverage](evidence/5.0.1-build103/compiler/dispositions.json).

Latest dependency work: [result-wrapper state transitions](review/CORE-RESULT-STATE.md)
and [malformed signing/planning inputs](review/CORE-SIGNING-PARSE.md), with real
before/after tests. All eight source repairs pass the full native C/C++ suites.
[Apple artifact reproduction](review/CORE-APPLE-REPRODUCTION.md) is recorded
separately. [Public app integration and its checks now pass](review/CORE-APP-INTEGRATION.md).
That is not an App Store update or a whole-wallet completion verdict.

**Latest checkpoint.** [Two-factor recovery and fixture repairs](review/ELECTRUM-TWO-FACTOR.md) · [Bitcoin Cash transactions and token-bearing outputs](review/BCH-TOKENS-AND-SIGNING.md) · [Acceptance](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Provider response limits](findings/OW-2026-034.md), [Stellar decoder checks](review/STELLAR-XDR-BOUNDARIES.md) and [remaining scope](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Bitcoin signature integrity](findings/OW-2026-033.md), [Bitcoin Core results and compilation inputs](review/BITCOIN-SIGNER-AND-CORE.md), and [remaining coverage](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Bitcoin WalletConnect packet and parent limits](findings/OW-2026-032.md), [host evidence](evidence/psbt-size/manifest.json), and [remaining review work](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Artwork URL admission and redirects](findings/OW-2026-031.md), [SwiftDraw document model](review/ARTWORK-HOSTS-AND-DOM.md), and [resolved package and BitcoinDevKit provenance](review/RESOLVED-PACKAGES.md).

**Earlier checkpoint.** [Token logo crash and depth bypass](findings/OW-2026-030.md), [bundled asset and SwiftDraw review](review/TOKEN-ARTWORK.md), and [historical CI evidence](evidence/ci-progress38/manifest.json).

**Earlier checkpoint.** [Early relay replies](findings/OW-2026-029.md) and [Wallet Core path API boundaries](review/CORE-PATH-C-API.md). The three relay operations timed out before the repair and completed after it.

Earlier dependency finding: [history identity across sends](findings/OW-2026-028.md).
Six stale-completion cases reproduce 10 assertions before; eight controls pass,
and all 14 pass after. SDK checks pass 254/one skip; diagnostics 118/two skips.
[Generation review](review/HISTORY-SEND-GENERATIONS.md) explains the optional local
field, legacy decoding, synthetic relay ACKs and remaining delivery limits.

Earlier dependency finding: [RPC history atomicity](findings/OW-2026-027.md).
Six races reproduce 10 assertions before; five controls pass, and all 11 pass
after. SDK checks pass 240/one skip and diagnostics 118/two skips.
[History review](review/RPC-HISTORY-ATOMICITY.md) explains shared-store instances,
controlled interleavings and the remaining cross-process/async-generation limits.

Earlier dependency finding: [session response routing](findings/OW-2026-026.md).
Eight invalid cases reproduce 18 assertions before; four controls pass, and all
12 pass after. SDK checks pass 229/one skip and diagnostics 118/two skips.
[Routing review](review/SESSION-RESPONSE-ROUTING.md) distinguishes link encryption
and history effects from relay endpoint recording and Oath app reachability.

Earlier dependency finding: [link metadata and transport state](findings/OW-2026-025.md).
Three nil-unwrap crashes and five rejected-input state assertions reproduce
before repair; eight controls pass and all 16 cases pass after. SDK checks pass
217/one skip and diagnostics 118/two skips. [Metadata review](review/LINK-SESSION-METADATA.md)
discloses restored optional fields, the host opening callback and synchronous
subscriber-test limits.

Earlier dependency finding: [incoming Link Mode boundaries](findings/OW-2026-024.md).
Eight cases reproduce 18 assertions before repair; eight controls pass and all
16 cases pass after. SDK checks pass 201/one skip and diagnostics 118/two skips.
[Link review](review/LINK-ENVELOPE-BOUNDARIES.md) distinguishes protocol dispatch
and history mutation from app reachability and complete peer authorization.

Earlier dependency finding: [authentication request input boundaries](findings/OW-2026-023.md).
Eight crashes and 32 assertions across eight cases reproduce before repair;
four controls pass and all 20 cases pass after. SDK checks pass 185/one skip
and diagnostics pass 118/two skips. [Authentication review](review/AUTH-REQUEST-BOUNDARIES.md)
documents decoder bounds, rejection before side effects, interface-only test
seams and the distinction from Oath's incoming approval path.

Earlier dependency finding: [queued cleanup and store timer lifetime](findings/OW-2026-022.md).
One controlled cleanup crash and one timer assertion reproduce before repair;
six controls pass and all eight cases pass after. SDK checks pass 165/one skip
and diagnostics pass 118/two skips. [Cleanup review](review/CLEANUP-LIFETIME-REVIEW.md)
discloses the queue test seam, preserves an initial fixture error, and reopens
three authentication input-review gaps without changing prior evidence.

Earlier dependency finding: [session watcher and callback lifetimes](findings/OW-2026-021.md).
Four isolated crashes and two duplicate-timer assertions reproduce before;
four controls pass and all ten cases pass after. SDK checks pass 157/one skip,
diagnostics pass 118/two skips and unsigned iOS Release compilation passes.
[Lifetime review](review/WATCHER-LIFETIME-REVIEW.md) records actual timer/storage
behavior and keeps remaining cleanup and concurrency work visible.

Earlier dependency finding: [outgoing request lifetime routing](findings/OW-2026-020.md).
Six assertions across four cases fail before repair; seven controls pass and
all eleven cases pass after. SDK checks pass 147/one skip, diagnostics pass
118/two skips and unsigned iOS Release compilation passes.
[Transport review](review/REQUEST-LIFETIME-REVIEW.md) traces the outgoing SDK
path and keeps link-mode, timer, service-response and cancellation gaps visible.

Earlier dependency finding: [separate-field CAIP account validation](findings/OW-2026-019.md).
Two expected assertions fail in one case before repair; all seven identical
cases pass after. SDK checks pass 136/one skip; diagnostics pass 118/two skips;
unsigned iOS Release compilation passes. [Parser review](review/CAIP-BOUNDARY-REVIEW.md)
records the rejected line-ending hypothesis, independent character oracle,
seeded corpus, preserved TON extension and limited app reachability.

Earlier dependency finding: [chain-scoped namespace validation](findings/OW-2026-018.md).
The same 15 production cases retain two crashes and 15 expected test failures
before repair, with four passing controls; all 15 pass after. SDK checks pass
118/one skip, diagnostics pass 118/two skips and unsigned iOS Release compilation
passes. [Review notes](review/NAMESPACE-BOUNDARY-REVIEW.md) distinguish these
SDK model results from an end-to-end Oath exploit and retain parser/lifecycle gaps.

Earlier dependency finding: [session expiry bounds](findings/OW-2026-017.md).
The same 13 production cases reproduce seven expected assertions and three
conversion crashes before repair, with six passing controls; all 13 pass after.
SDK checks pass 82/one skip, diagnostics pass 118/two skips, and unsigned iOS
Release compilation passes. [Review notes](review/SESSION-EXPIRY-REVIEW.md)
explain the limited Oath reachability and outstanding namespace/lifecycle work.

Earlier application finding: [SDK event opt-out lifecycle](findings/OW-2026-016.md).
All nine identical production tests pass after reproducing 14 expected assertions
before. Initialization, collection, cancellation and stale acknowledgements are
covered. [Review notes](review/EVENTS-LIFECYCLE-REVIEW.md) also preserve the prior
56-job successful GitHub run and distinguish it from the new target.

Earlier application finding: [optional relay transaction metadata](findings/OW-2026-015.md).
The encoder now preserves routing and encrypted peer content while omitting four
optional metadata fields. The same four host cases retain 11 expected assertions
before and pass afterward. [The source review](review/RELAY-METADATA-REVIEW.md)
keeps SDK initialization and other privacy boundaries explicitly outstanding.

Latest test repair: [Solana multisig vector isolation](review/SOLANA-VECTOR-ISOLATION.md).
All 76 unchanged vectors pass as separate network-denied cases, and the pinned
SDK reproduces the entire fixture byte-for-byte. The original CI timeout,
audit-tool dependency advisories and remote-validation gaps remain visible.

Earlier application finding: [router operations omitted from first approval](findings/OW-2026-014.md).
The identical production-model corpus retains 30 expected assertion failures
before and nine passing executions after. Ten ABI fixtures also pass an
independent ethers cross-check. [Approval source review](review/SWAP-APPROVAL-REVIEW.md)
distinguishes host-model tests and compilation from UI or on-chain execution.
The previous [Polygon swap destination repair](findings/OW-2026-013.md) and
[swap review](review/SWAP-REVIEW.md) retain their original evidence.
The prior [duplicate permission readback finding](findings/OW-2026-012.md) and
[discovery review](review/PERMISSION-DISCOVERY-REVIEW.md) retain their evidence.
The previous [permission-grant revocation fix](findings/OW-2026-011.md) and
[batch source review](review/PERMISSION-BATCH-REVIEW.md) remain available.
The previous [delegation nonce serialization finding](findings/OW-2026-010.md) remains,
with retained arithmetic-trap evidence and identical passing post-fix tests.
The [Safe contract cross-check](review/SAFE-CONTRACT-CROSSCHECK.md) records
source comparisons and remaining contract provenance gaps. The previous
[response-size repair](findings/OW-2026-009.md) retains its exact-limit controls. The [EVM source trace](review/EVM-SEND-TRACE.md)
keeps its remaining protocol, dependency and helper-API questions explicit.
The earlier [refresh cancellation repair](findings/OW-2026-008.md) retains its original CI failure.
[Offline diagnostic modes](review/DIAGNOSTIC-MODES.md) also cover eight cases
that previously skipped under the normal package environment. The earlier
[TRON trace](review/TRON-SEND-TRACE.md) remains available separately.

## Reproduce

Use an isolated machine with Xcode 27.1, Swift 6.4 and Python 3.14.7.
Local exploratory runs used Xcode 27.0; each run records its actual toolchain.
The optional aezeed `--rebuild` proof requires Xcode 27.0 (27A266a), matching
the archive provenance. Omitting that flag verifies recorded hashes only.
Package downloads require network access; opt-in live-chain tests are not enabled.
No signing certificate, provider credential, real wallet or App Store access is needed.

```sh
python3 scripts/checkout.py
python3 scripts/request-lifetime.py .work/source --output .work/request-lifetime --scratch .work/request-build
python3 scripts/watcher-lifetime.py .work/source --output .work/watcher-lifetime --scratch .work/watcher-build
python3 scripts/cleanup-lifetime.py .work/source --output .work/cleanup-lifetime --scratch .work/cleanup-build
python3 scripts/auth-boundary.py .work/source --output .work/auth-boundary --scratch .work/auth-build
python3 scripts/link-boundary.py .work/source --output .work/link-boundary --scratch .work/link-build
python3 scripts/link-metadata.py .work/source --output .work/link-metadata --scratch .work/link-metadata-build
python3 scripts/response-routing.py .work/source --output .work/response-routing --scratch .work/response-routing-build
python3 scripts/history-atomicity.py .work/source --output .work/history-atomicity --scratch .work/history-atomicity-build
python3 scripts/history-generation.py .work/source --output .work/history-generation --scratch .work/history-generation-build
python3 scripts/relay-early-replies.py .work/source --output .work/early --scratch .work/early-build
python3 scripts/svg-reference-graph.py .work/source --output .work/svg --scratch .work/svg-build
python3 scripts/artwork-host-policy.py .work/source --output .work/hosts --scratch .work/hosts-build
python3 scripts/bitcoin-psbt-size.py .work/source --output .work/psbt --scratch .work/psbt-build
python3 scripts/bitcoin-parent-budget.py .work/source --output .work/fetch --scratch .work/fetch-build
python3 scripts/bundled-artwork.py .work/source --output .work/resources
python3 scripts/caip-boundary.py .work/source --output .work/caip-boundary --scratch .work/caip-build
python3 scripts/namespace-boundary.py .work/source --output .work/namespace-boundary --scratch .work/namespace-boundary-build
python3 scripts/session-expiry.py .work/source --output .work/session-expiry --scratch .work/session-expiry-build
python3 scripts/swap-approval.py .work/source --output .work/approval-after --scratch .work/approval-after-build
python3 scripts/swap-progress.py .work/source --output .work/swap-after --scratch .work/swap-after-build
python3 scripts/permission-batch-races.py .work/source --output .work/batch-after --scratch .work/batch-after-build
python3 scripts/permission-readback.py .work/source --output .work/readback-after --scratch .work/readback-after-build
python3 scripts/evm-response-boundary.py .work/source --output .work/evm-evidence/after --scratch .work/evm-after-build
python3 scripts/inventory.py .work/source --output scope/inventory.json
python3 -m unittest discover -s tests -p 'test_*.py'
sh scripts/parser-check.sh .work/source .work/parser
python3 scripts/run.py .work/source OathCloudBackup
python3 scripts/run.py .work/source OathDiagnostics
python3 scripts/run.py .work/source OathDatabase
python3 scripts/run.py .work/source OathBitcoin
python3 scripts/run.py .work/source OathAnkr
python3 scripts/run.py .work/source OathAezeed
python3 scripts/run.py .work/source OathWalletHandoff
python3 scripts/relay-envelope-check.py .work/source --output /tmp/relay-evidence
python3 scripts/response-topic-check.py .work/source --output /tmp/topic-evidence
python3 scripts/uri-boundary-check.py .work/source --output /tmp/uri-evidence
python3 scripts/pairing-link-check.py .work/source --output /tmp/uri-evidence
python3 scripts/ton-properties.py .work/source --output /tmp/ton-evidence --scratch .work/ton-properties
python3 scripts/solana-properties.py .work/source --output /tmp/solana-evidence --scratch .work/solana-properties
python3 scripts/tron-properties.py .work/source --output /tmp/tron-evidence --scratch .work/tron-properties
python3 scripts/diagnostic-modes.py .work/source --package OathAnkr --output .work/diagnostic-ankr --scratch .work/diagnostic-build/ankr
python3 scripts/diagnostic-modes.py .work/source --package OathDiagnostics --output .work/diagnostic-trace --scratch .work/diagnostic-build/trace
python3 scripts/refresh-cancellation.py .work/source --output .work/cancellation-after --scratch .work/cancellation-after-build
python3 scripts/aezeed-primitives.py .work/source --expected-commit 2eef5a4912ce1680cd174c7596471620ffcf129e --output /tmp/aezeed-primitives
python3 scripts/aezeed-provenance.py .work/source --expected-commit 2eef5a4912ce1680cd174c7596471620ffcf129e --output /tmp/aezeed-provenance
python3 scripts/ton-authorization.py .work/source --output /tmp/ton-authorization --scratch .work/ton-authorization
python3 scripts/run.py .work/source scanner
python3 scripts/run.py .work/source wallet-links
python3 scripts/run.py .work/source scanner-lifecycle
python3 scripts/run.py .work/source walletconnect-sdk
python3 scripts/run.py .work/source walletconnect-verify
python3 scripts/run.py .work/source security
python3 scripts/run.py .work/source cloud-restore
python3 scripts/run.py .work/source build
```

`scripts/run.py --help` lists the additional authorization harnesses. Those
harnesses replace hardware, networking and some derivation adapters with
fixtures: their outcomes do not establish end-to-end iOS signing behavior.
Read the original harness headers and the report before interpreting a pass.

For the baseline parser reproduction, check out the baseline commit separately
and run `parser-check.sh` against it. The object-limit assertion must fail there;
it must pass on the repaired revision. The parser harness compiles the actual
production files, without rewriting them.

## Evidence and claims

Findings retain the original defect, reproduction and fix; they are not deleted
to create a clean-looking report. Results record exit status and skipped-test
summaries. A passing command may include explicitly skipped live/runtime tests.
Local logs are sanitized for paths before publication. GitHub artifacts are
retained for 90 days; release bundles preserve selected evidence longer.

No workflow deploys the app, uses production secrets or runs on a self-hosted
runner. Public PR checks use disposable GitHub-hosted machines and read-only
tokens. Changes after a reviewed commit require another review.

## Responsible use

All test credentials are public synthetic fixtures. Never fund them or supply
real credentials to these tests. Report newly discovered exploitable issues
through the application's [private reporting channel](https://github.com/OathWallet/oath-wallet/security/advisories/new).
Technical details should accompany tested fixes; a public source fix is not
proof that App Store users have received it.

## Progress evidence release

The [historical progress 26 snapshot](https://github.com/OathWallet/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress26)
is a prerelease, not a completed audit. It identifies the original baseline and
fixed source target and attaches sanitized logs, result records and SHA-256
checksums. Failed attempts remain included. Workflow runs after the snapshot
are additional evidence; they do not retroactively change its coverage claims.

Package runs isolate each XCTest case in its own host process and retain its
actual skipped/passed/failed output. Swift Testing runs separately. Earlier
Swift parallel xUnit files remain in evidence, but their missing skip markers
must not be read as zero skipped tests; see the reporting correction in
`review/READ-NOTES.md`. No passing command converts an opt-in skip into evidence.


## Aezeed dependency reproduction

The workflow pins Go 1.26.5. From the audit root after checkout:

```sh
reviewed=$(python3 -c "import json; print(json.load(open('scope/source.json'))['reviewed_commit'])")
python3 scripts/go-source-inventory.py .work/source "$reviewed" .work/aezeed-source-inputs.json
python3 scripts/go_advisory_triage.py evidence/bridge/osv-go.json .work/aezeed-source-inputs.json .work/advisory-triage.json
python3 scripts/aezeed-repairs.py .work/source --expected-commit "$reviewed" --output .work/aezeed-paired
python3 scripts/aezeed-primitives.py .work/source --expected-commit "$reviewed" --output .work/aezeed-primitives
bash .work/source/Tools/AezeedBridge/test.sh
```

The committed OSV snapshot makes that classification replayable; CI also obtains
and preserves a fresh snapshot. Any new unresolved affected import fails triage.
For wordlist comparison, clone the pinned Wallet Core revision in
`scope/upstream-wallet-core.json`, then run
`python3 scripts/compare-aezeed-wordlists.py .work/source <WALLET_CORE> .work/wordlists.json`
from the audit root. The module inventory does not establish historical archive
identity or manually-reviewed coverage.

## Child-derivation reproduction

The [upstream child-derivation review](review/CHILD-DERIVATION-REVIEW.md) includes
actual C tests under memory/undefined-behavior sanitizers, an independently written
HMAC/integer oracle, and pinned public SLIP-0010 vectors. It separates passing
derivation cases from two API hazards (source repairs added in progress 15) and gives a clean-checkout
command. Neither source tests nor constructor reachability establish distributed
binary equivalence or a completed wallet audit.

Progress 14 adds [multisig recovery review and mutations](review/MULTISIG-RECOVERY-REVIEW.md)
and [constructor/entropy-lifetime experiments](review/CONSTRUCTOR-LIFETIME-RESULTS.md).
Their original dependency failures remain preserved and distinct from later
source-repair regressions and the passing positive tests.

## Dependency source-repair follow-up

Four confirmed Core API/lifetime defects now have [tested source patches and
identical before/after evidence](review/CORE-SOURCE-REPAIRS.md). They are not yet
incorporated into Oath’s shipped frameworks; integration and the whole-wallet
review remain incomplete. No App Store upload was performed.

Progress 16 adds a [fifth tested Core repair and full native suites](review/CORE-NATIVE-AND-EXTENDED-KEY.md):
the same 94-case extended-key corpus has 21 failures before repair and none after;
2,363 upstream C++ tests and 113 C checks pass. Apple framework integration is
still outstanding. The [advisory gate correction](review/ADVISORY-GATE.md) retains
raw scanner findings and binds classification to the exact selected build graph.
That progress-16 snapshot recorded 7,679 outstanding items.

Progress 17 adds [three repaired aezeed dependency APIs and rebuilt archives](review/AEZEED-DEPENDENCY-REPAIRS.md),
merged in application PR 10. Identical before/after regressions, independent
primitive checks, host tests and generic iOS compilation pass. Current coverage
and missing exact-target checks remain explicit in the completion ledger.
