# Oath Wallet security review progress report

**Checkpoint 18.** The shipped XRP JavaScript codec rebuilds byte-for-byte from its locked source. Six new actual-package request/signature boundary methods pass, including the isolated network-denied replay. The newly enumerated 170 upstream input files remain explicitly outstanding; a matching bundle does not certify their implementations. [Evidence and scope](XRPL-CODEC-BOUNDARIES.md).

**Checkpoint 17.** [OW-2026-061](../findings/OW-2026-061.md) repairs inconsistent XRP Connect simulation metadata in [PR #75](https://github.com/devdasx/oath-wallet/pull/75). The clean-checkout replay preserves two failing methods before and all six passing after; broader XRP tests, diagnostics and unsigned Release compilation pass. The earlier signing matrix now also passes on GitHub with verified artifact hashes. [Evidence and limits](XRPL-CONNECT-SIMULATION.md).

**Checkpoint 16.** Four offline production-package methods pass: 61 complete XRP signed transactions and hashes match the independent pinned SDK, 13 RIPEMD vectors match OpenSSL-backed results, and altered plans/envelopes/signer sets are rejected. Five source files gain partial coverage. No new application defect is confirmed by this matrix. [Scope, reproduction and remaining provider hypothesis](XRPL-SIGNING-MATRIX.md).


**Checkpoint 15.** [OW-2026-060](../findings/OW-2026-060.md) repairs an XRP issued-token quote failure for valid large amounts. The same 4,900 deterministic arithmetic cases change from 4,843 passes/57 failures to all passing. Targeted package regressions, diagnostics, source validation and unsigned iOS Release compilation pass. [Reproduction, scope and limits](XRPL-AMOUNT-ARITHMETIC.md) · [Checkpoint evidence](RELEASE-5.0.1-103.md#checkpoint-15). No live ledger or App Store result is claimed.


**IN PROGRESS. This is not a completed whole-wallet audit.**

**Active target — 5.0.1 (103).** The maintainer-commissioned Codex review now targets public source `c7acd23bb139864a40273f405d18b479589d2b20`. App Store Connect showed iOS version 5.0.1 Waiting for Review on 2 November 2026. [Current results and release-specific findings](RELEASE-5.0.1-103.md) · [Coverage inventory](../scope/inventory.json).

**Build 103 checkpoint 2.** Changing recovery format after an interrupted wallet import could return a different Bitcoin wallet. The error reproduced on the tagged source. [Finding and regression](../findings/OW-2026-046.md) · [Application and dependency checks](RELEASE-5.0.1-103.md) · [Direct input coverage](../evidence/5.0.1-build103/compiler/dispositions.json).

**Checkpoint 14.** GitHub reproduced both repairs: private-key cleanup changes from seven passes/four failures to eleven passes, and backup progress changes from twelve passes/three failures to fifteen passes. Downloaded artifact, log and source hashes were verified. Twenty-two new restore-model host checks pass and detect a deliberately broken guard; four more files have partial source coverage. [Evidence](RELEASE-5.0.1-103.md#checkpoint-14).

**Checkpoint 13.** A canceled backup-record read could overwrite a newer batch's error/progress. [OW-2026-059](../findings/OW-2026-059.md) is repaired in [PR #73](https://github.com/devdasx/oath-wallet/pull/73). The same fifteen production-model cases change from twelve passes/three failures to all fifteen passing. Diagnostics and unsigned iOS Release compilation pass; no backup corruption or key disclosure was demonstrated. Four additional files have partial source review dispositions with UI limits preserved. [Evidence](RELEASE-5.0.1-103.md#checkpoint-13).

**Checkpoint 12.** A synthetic runtime experiment confirmed that a revealed private key could survive into app-switcher snapshots with optional privacy disabled. [OW-2026-058](../findings/OW-2026-058.md) is repaired in [public PR #71](https://github.com/devdasx/oath-wallet/pull/71): the same host cases change from seven passes/four failures to eleven passes, 791 broader wallet checks pass, and unsigned iOS Release compilation succeeds. Actual OS snapshot evidence and all substitutions are preserved. This does not establish full export UI coverage, every OS transition, or App Store delivery. [Evidence and limits](RELEASE-5.0.1-103.md#checkpoint-12).

**Checkpoint 11.** Private-key ownership and leaf-export checks pass 305 assertions on the exact build 103 baseline. Source tracing covers the export adapter separately from the substituted host engine. Token-search and automatic-prompt GitHub reruns passed with verified artifact/log hashes. The retained-key app-switcher snapshot question remains open. [Scope and evidence](RELEASE-5.0.1-103.md#checkpoint-11).

**Checkpoint 10.** Recovery disclosure and passcode setup source tracing adds eleven scoped file dispositions. Nineteen automatic-prompt host checks and 245 audit helper tests pass. A single synthetic simulator experiment found no readable fixture text through the settled privacy cover; actual app-switcher snapshot timing remains open. No application change was needed for these hypotheses. [Scope and evidence](RELEASE-5.0.1-103.md#checkpoint-10).

**Checkpoint 9.** Token-search race tests now use controlled interleavings instead of timing guesses; they pass on unchanged production code and detect an intentionally broken variant. The final baseline workflow preserves five failed jobs and 105 verified result/log pairs. [Evidence, test repairs and remaining scope](RELEASE-5.0.1-103.md#checkpoint-9).

**Build 103 checkpoint 8.** Protocol-key constructors now reject malformed hex and invalid symmetric-key sizes. Eleven original failing methods and four valid controls are preserved; all fifteen pass after repair. The complete SDK suite passes 321 tests with two skips, and unsigned iOS Release compilation succeeds. [Finding and compatibility](PROTOCOL-KEY-HEX.md) · [Validation](../evidence/5.0.1-build103/key-hex/validation.json) · [Merged fix](https://github.com/devdasx/oath-wallet/pull/69). These are WalletConnect messaging keys; the tests do not demonstrate wallet-secret disclosure or a consent bypass.

**Build 103 checkpoint 7.** The address checksum helper now rejects malformed inputs before changing their bytes. Nine production-code methods pass, including 24 independent vectors. The full SDK suite passes 306 tests with two skips, and unsigned iOS Release compilation succeeds. The source API now throws. [Finding and scope](ADDRESS-CHECKSUMS.md) · [Validation](../evidence/5.0.1-build103/address-checksums/validation.json) · [Merged fix](https://github.com/devdasx/oath-wallet/pull/68). The helper's application reachability remains unproven.

**Build 103 checkpoint 6.** Signature constructors now reject malformed encodings safely, and contract verification uses actual signature lengths and exact supported replies. Five original traps and twelve failing methods are preserved; all twenty methods pass after repair. The full SDK suite passes 297 tests with two skips, and unsigned iOS Release compilation succeeds. [Findings and compatibility](SIGNATURE-CONTRACT-BOUNDARIES.md) · [Merged repair](https://github.com/devdasx/oath-wallet/pull/67) · [Validation](../evidence/5.0.1-build103/signature-contracts/validation.json). The dependency verifier's application reachability remains unproven.

**Build 103 checkpoint 5.** The bundled ENS response decoder trapped on malformed input and accepted several invalid encodings. The exact-release replay preserves seven crashing processes, four failing methods and five passing controls. All sixteen pass on the merged repair. Application reachability remains unproven. [Finding](../findings/OW-2026-053.md) · [Tests and review scope](ENS-CONTRACT-DECODING.md) · [CI evidence](../evidence/5.0.1-build103/ci-artifacts-checkpoint5.json).

**Build 103 checkpoint 4.** Public source repairs cover Bitcoin-family address discovery and backup file races. The original failures, fixed cases and build receipts are recorded separately from the submitted build. [Address issuance](../findings/OW-2026-049.md) · [Backup reads](../findings/OW-2026-051.md) · [Conflicting backup writes](../findings/OW-2026-052.md) · [Scalar arithmetic](SECP-SCALAR-ARITHMETIC.md).

**Build 103 checkpoint 3.** Synthetic authenticated vault and SQLite records reproduced three integer overflows. Public source repairs passed the focused tests, full database package and unsigned iOS builds. [Vault finding](../findings/OW-2026-047.md) · [Database finding](../findings/OW-2026-048.md) · [Exact-target CI evidence](../evidence/5.0.1-build103/ci-artifacts-checkpoint3.json).

## Historical 4.1.15 series

The original baseline was `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. Its last review target was `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`. The dated entries below describe that earlier work.

## Progress 57 · 2 November 2026

The complete native Wallet Core suites passed 2,363 C++ and 113 C cases. The extended-key corpus reproduced 21 original assertion failures and passed all 94 assertions with the repaired translation unit. At the historical app revision the provider package now passed 1,296 cases with 194 explicit skips. The earlier failing provider run remains valid evidence of an intermittent cache bug, and the later public repair remains necessary.

All 115 required checks now have at least one passing record at the pinned revision. That count includes historical runs; it is not a clean pass of one GitHub workflow or the latest merged wallet tree. Separately, seven original Swift path failures reproduced and eleven host controls passed with the source patch. Two dependency findings await integration into the public app. 16,578 entries remain open across the source, dependency and findings ledgers. [Swift findings and reproduction](CORE-SWIFT-PATH-VALUES.md) · [Provider retest](../evidence/progress57/provider/result.json) · [Original provider failure](../findings/OW-2026-043.md).

## Progress 56 · 2 November 2026

A synthetic signed transaction spending the same inputs but paying another recipient passed the original recovery check. A second defect kept a database with an interrupted reset from opening during the backup reminder upgrade. Four original failures reproduced. The same four tests and three additional compatibility checks all passed on the merged repair tree. The fixed database and Bitcoin packages passed 732 and 314 cases, respectively, with 72 and 60 explicit skips. The unsigned iOS Release build passed. The existing 5.0.1 (103) tag predates these fixes.

Four more validations now have evidence at the historical review target. Three required validations and 16,583 total ledger entries remain open. [Finding details, test commands, results and limits](BITCOIN-JOURNAL-AND-RESET.md) · [App changes](https://github.com/devdasx/oath-wallet/pull/56).

## Progress 55 · 2 November 2026

GitHub’s full run at this review target had three failed jobs. We recovered and checked all 84 artifact archive digests. Individual reports account for 98 recorded passes and one recorded failure with matching logs. The full package later passed on the fix commit for the duplicate metadata lookup in [app PR 55](https://github.com/devdasx/oath-wallet/pull/55). The fix commit and its public merge have identical source trees. The 5.0.1 (103) release tag predates the repair. A generic unsigned iOS Release build passed on the fixed tree.

The child-key comparison now runs identical test fixtures on both production revisions. Four original failures reproduced, the original rejection control passed, and all five cases passed on the review target. Separately, 458 directly compiled Stellar Swift files were regenerated byte for byte from 13 upstream schemas. Seven of the 115 required checks still lack a passing record at this exact app revision. The ledger retains 16,586 open entries. Outstanding work includes dependency review, historical binary provenance and adversarial checks of transaction recovery.

[Methods and limitations](PROVIDER-QUEUE-AND-STELLAR-GENERATION.md) · [Original CI records](../evidence/progress55/ci-artifacts.json) · [Compiled coverage](../evidence/progress55/compiled-inputs.json) · [Merged repair verification](../evidence/progress55/provider/merge-verification.json)

## Previous checkpoint · Progress 54

The Electrum two-factor repair restored both independently calculated Bitcoin addresses, and the encrypted-wallet run passed 205 checks. Full package runs passed 305 Bitcoin and 708 database cases, with 60 and 71 explicit skips respectively. Unsigned iOS Release compilation passed. Three isolated Bitcoin Cash Node chains confirmed 20 ordinary spends and 121 threshold-policy spends. The node rejected modified signatures, changed payments and spends missing a required multisignature. The CashTokens prefix reader matched all 22,960 expected outcomes.

Two additional planner issues were reproduced at this source and repaired afterward in [PR 53](https://github.com/devdasx/oath-wallet/pull/53). The identical named tests passed on that later source. At the reviewed source, two protected-startup assertions missed expected asynchronous diagnostics (25 of 27 assertions passed). This failed run is included in the validation evidence. OW-2026-002 remains open for historical archive provenance.

28 passing check records target this revision. 87 required checks lack a passing exact-revision record. There are 17,124 open entries across the inventories, findings and validation ledger. [Recovery and diagnostic evidence](ELECTRUM-TWO-FACTOR.md) · [Bitcoin Cash evidence](BCH-TOKENS-AND-SIGNING.md) · [Compiled source coverage](COMPILED-COVERAGE.md).

Previous target: `343046575c980b9091a4474f098878e920963492`.

Nine synthetic inputs or decisions reproduced import failures on their original revisions. All eleven repaired cases and positive controls passed, as did 1,667 existing assertions across 260 BIP39 vectors. Separate encrypted-storage integrations passed 30 aezeed checks and 201 Electrum checks. The original integration fixture failure is retained with its corrected test. The unsigned iOS Release build succeeded, and all 20,480 BIP39 word-list entries matched the pinned upstream files in both the source and the product. The bundled legacy Electrum resource also matched all 1,626 upstream word positions.

30 passing checks are recorded at this exact revision. 82 required checks lack passing exact-revision records. The full ledger has 17,119 open entries. OW-2026-002 remains open for historical binary provenance. A further confirmed CJK two-factor recovery issue, OW-2026-040, remains open at this reviewed revision. Two earlier database diagnostic assertions failed. The current database run passed 706 of 778 selected cases, skipped 71 and timed out in the TRON test transport. [Follow-up test repairs](https://github.com/devdasx/oath-wallet/pull/52) have separate results. [Recovery review](RECOVERY-IMPORT-ROUTING.md) · [Public fix](https://github.com/devdasx/oath-wallet/pull/50).

Previous target: `7ecfa2c163704d363ebe6dc16b60151dc8a7cd78`.

The complete BDK Swift 3.1.1 arm64 device archive matched the distributed bytes on GitHub Actions. All 902 members and the full archive SHA-256 matched. Two local traces identified the inputs of all 400 native archive members. A new ledger records 823 additional registry files rather than treating a binary match as source review. The pinned Rust/C curve passed 137 host scalar and point cases. The historical DER reader was exercised with positive and negative encodings, all 70 truncated prefixes, and 2,048 deterministic bounded inputs. [Scope, evidence and reproduction](BDK-NATIVE-INPUTS.md).

OW-2026-002 remains open for original archive provenance. All original C members across the three historical aezeed slices matched the earliest public bridge build. Every Go executable-section byte outside its embedded build ID matched, as did all section relocation records. Non-identical file hashes, differing debug and symbol data, and the original build's modified-checkout flag remain visible. [Historical finding](../findings/OW-2026-002.md).

The exact current app checkout now has 38 passing check records, with 68 required checks still lacking passing records in the published ledger. Additional checks belonging to an earlier test revision are retained under that earlier commit. [Acceptance checklist](ACCEPTANCE.md).


[OW-2026-036](../findings/OW-2026-036.md) fixes refusal of the final normal BIP32 address index. The same four positive tests failed before and passed after; the negative boundary control passed on both revisions. Independent P2PKH scripts cover four chains. Single-key and two-of-two Bitcoin transactions were signed offline. [PR 49](https://github.com/devdasx/oath-wallet/pull/49).

All seven Swift secp256k1 wrapper operations were read. Four independent-vector test cases exercised deterministic DER and recoverable signatures, rejection boundaries, scalar addition and sliced buffers against the shipped implementation. Native internals, emitted erasure behavior and side-channel properties remain open. The full Bitcoin host package passed 304 cases with 60 opt-in skips, and the generic unsigned iOS Release build passed. [paired address results](../evidence/child-boundary/oath51-paired-release/child/utxo-child-boundary.json) · [curve results](../evidence/child-boundary/oath51-paired-release/curve/secp-wrapper.json).

The SDK 18.5 GitHub build with the publisher’s recorded checkout and Cargo paths matched 835/902 whole members and 857/857 instruction digests. Full archive byte equality: false. The paired isolated layout matched 788/902 members and 856/857 instruction digests. Nonidentical same-name members in the publisher-path build: 67. [Hosted jobs](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41364048202) · [component-by-component differences](../evidence/child-boundary/oath51-paired-release/device/publisher/differences.json). All 857 instruction digests and all raw section relocation records match in the publisher-path pair. Each of the 67 differing members has different constant data, C strings, embedded bitcode, load commands and symbol tables. Those differences still matter to a complete library equivalence claim. This concerns one dependency slice.

An earlier public workflow completed all 70 jobs at application commit `25bcf5bd3418c574d92d63c7d5d5acef39d7d75c`. Its results have their own scope and identity. [Workflow](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41354459646) · [job and artifact index](../evidence/child-boundary/oath51-paired-release/ci/prior-hosted-run.json).

Previous target: `a13a88cb67fe9fa73c1a0bbb222a474b195e25eb`.

[OW-2026-035](../findings/OW-2026-035.md) fixes a private-key import that could turn a public point into the wrong spending wallet. Five synthetic cases reproduced the original failures. The repaired importer passed all seven cases, plus all 16 published BIP32 invalid vectors and their valid-root control. Three of those official invalid inputs were accepted before the fix. Four locally encrypted prior-format wallets preserved their independently calculated scripts across restore, cold reopen and re-backup. The [source repair](https://github.com/devdasx/oath-wallet/pull/47) distinguishes fresh private input from recovery of a scalar already held in protected storage. The tested and merged Git trees are identical.

The full Bitcoin package on the tested commit passed 299 cases with 60 skips. An earlier test run missed a Dogecoin diagnostic. Adding a delay to the fixture consumer reproduced the polling race in four network suites. The new event-driven assertions passed under the same delay. The unsigned generic Release build, 118 diagnostics cases (two skips), coverage, public release checks and 191 review-helper tests passed. The [evidence manifest](../evidence/typed-keys/manifest.json) includes the original failure, separate returning validation results at the prior commit, and current exact-source records.

The [BDK source and binary trace](EXTENDED-KEY-IMPORT.md) records 2,512 verified compiler inputs and 2,348 newly visible registry files. A [hosted SDK 18.5 rebuild](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41361917821) matched 788 of 902 archive members byte for byte, and 856 of 857 raw instruction-section digests. The entire remaining instruction digest can be reproduced by changing the immediate length of Cargo’s build-time executable path, from 70 to 146. The app’s link map retains the affected helper. No execution of that helper was demonstrated. Data, relocations and the full archives still differ. This is neither archive equality nor an App Store comparison.

Two subsequent assertions failed in the full provider run on `a13a88cb67fe9fa73c1a0bbb222a474b195e25eb`: the token-artwork test had received its catalog event but not its HTTP 401 event, and the TON test had received a malformed event but not its read-attempt event. The [original run](../evidence/typed-keys/oath50-release-evidence/pre-order-fix/OathAnkr.json) is preserved. [PR 48](https://github.com/devdasx/oath-wallet/pull/48) changed three test files to wait for the complete correlated event set. Injecting the same delay into the secondary event reproduced both previous failures; both repaired cases passed. On the test-only commit `5f92dc2a87334c0b4942dea1f6a47ad92770f4a3`, the full provider suite passed 1,296 cases with 194 opt-in skips. The unsigned generic iOS build and diagnostics tests passed at that revision. The public release validator correctly required review of the moved dummy-key lines. Their original text was verified, and only their two scanner metadata files changed in the published follow-up head. Its public scan and unsigned build passed. [Delayed-event comparison](../evidence/typed-keys/oath50-release-evidence/event-order/provider-event-order.json) · [Exact file diff](../evidence/typed-keys/oath50-release-evidence/test-followup/diff.json). These results are attributed to their own test revisions.

Previous target: `0e50b16ae1ced7934d57dba42d3e6e69ccf6cfc8`.

[OW-2026-034](../findings/OW-2026-034.md) documents continued downloads after the intended limit. The [source repair](https://github.com/devdasx/oath-wallet/pull/46) cancels oversized transfers while retaining status, retry and cancellation behavior. Fifteen cases exercised ordinary, oversized, interrupted or missing responses. Eight reproduced prior failures, seven were passing controls, and all fifteen passed after repair. This establishes response and cancellation behavior, without claiming a peak process memory figure.

Five [Stellar envelope tests](STELLAR-XDR-BOUNDARIES.md) exercised the shipped request decoder and pinned SDK. The valid control matched an independently generated testnet digest and signed locally. The parser rejected excessive recursion and a forged element count. Oath rejected a noncanonical optional flag and trailing bytes. Seven upstream files have partial, hash-bound dispositions for this path.

Host packages on the current app source: Bitcoin (289 passed, 60 skipped), diagnostics (118 passed, 2 skipped), rates (16 passed, 2 skipped), Ankr (1,296 passed, 194 skipped) and database (707 passed, 71 skipped). Token lookup passed 19 cases with four opt-in skips. The app update harness passed 23 assertions. [Historical failures](../evidence/provider-response/oath49-http-evidence/triage.json) map all 48 assertions from the original triage file to 23 passing current selectors or explicitly named successors.

The unsigned iOS Release build selected 2,354 distinct non-toolchain compiler inputs. The [network entry point index](../evidence/provider-response/oath49-http-evidence/build-inputs/transport-inputs.json) reports 73 files with lexical candidates among 2,347 text inputs. Seven compiled modules were hashed separately. These matches do not prove symbol reachability. The new [transport review](HTTP-RESPONSE-BOUNDARIES.md) states which paths were inspected. The actual embedded WalletCore and WalletCoreSwiftProtobuf executable files were byte-identical to the two resolved arm64 XCFramework slices in this build; this does not establish independent upstream-source reproduction. The independently rebuilt BDK iOS static archive was different to the published archive (525 of 902 published members had identical payloads). All 187 audit helper tests passed. Production source tree `d11801ba6ee09eda6083caac4ffe440854ed29ee` is identical at the tested fix and public merge.

Previous target: `0e611a5408cfa02c8463b4bcd74a0164522cf7a3`.

[OW-2026-033](../findings/OW-2026-033.md) documents a wallet signing-result integrity bug. A peer-supplied ECDSA or Taproot partial signature for a different transaction survived signing and the original journal verification. The [app repair](https://github.com/devdasx/oath-wallet/pull/45) regenerates the requested signature and asks BDK's script interpreter to verify the unlocking data against the approved transaction. The nine-case host corpus recorded eight specific failures and one passing control before the change. All nine passed afterward.

The independent [Bitcoin Core comparison](../evidence/core-signatures/oath-core48-evidence/walletconnect/bitcoin-connect-core-proof.json) rejected both contaminated spends before repair and mined both controls. It mined all four transactions from the fixed source. Five separately enabled Core tests also passed, covering 32 source/destination combinations, a 255-input sweep, multisig up to 15-of-15, aezeed recovery, and 11 Electrum fixtures across five seed kinds. The isolated funding and mining use regtest only.

The current exact app commit passed 280 Bitcoin tests (60 skips), 707 database tests (71 skips), 118 diagnostics tests (two skips), source and coverage checks, the previous two PSBT boundary corpora and unsigned iOS Release compilation. The [build ledger](../evidence/core-signatures/oath-core48-evidence/build-inputs/release-inputs.json) identifies 2,353 compiler and dependency inputs plus four processed XCFrameworks. The [dependency review](BITCOIN-SIGNER-AND-CORE.md) adds exact source inventories for the two relevant Rust crates. All 182 audit helper tests passed. The merge `bb3cc41a87d26ba299c27b1888d949e5c84ede5f` has the same tree as the tested source. Full CI, outstanding code and binary provenance remain open.

Previous target: `55f4e809ba46881b1d6d454cdce3ef62a627df85`.

[OW-2026-032](../findings/OW-2026-032.md) documents a Bitcoin WalletConnect request that expanded during review. Eight inputs referenced different outputs of one funding transaction. Review returned a 509,260-byte packet, then the signer rejected that same packet at its 500,000-byte limit. In a separate intercepted URLSession test, the original collector retained more than the limit across six unique funding transactions. The [public source fix](https://github.com/devdasx/oath-wallet/pull/44) bounds retained parents, accounts for repeated parents, and checks field prefixes and map terminators during serialization. All five paired host cases passed after the fix. The smaller request and two-parent control passed before and after.

The exact fixed app commit passed 271 Bitcoin tests (60 opt-in skips), 118 diagnostics tests (two skips), public-source validation, diagnostics coverage, the artwork URL and SVG regression corpora, and unsigned generic iOS Release compilation. All 177 audit helper tests also passed. One earlier compile attempt and one audit assertion matcher error are recorded separately from the accepted [evidence](../evidence/psbt-size/manifest.json). The [merged tree](../evidence/psbt-size-merge-identity.json) equals the tested app tree. The current full CI and source/dependency coverage remain incomplete.

Previous target: `eb8239ad3be4c0b0650e2e34334982ac54c15b42`.

[OW-2026-031](../findings/OW-2026-031.md) reproduced an unintended token-artwork destination. Darwin recognizes `0x7f.1` as loopback. Both initial loads and the redirect gate accepted this spelling before the repair. Six of eight offline cases failed before the change (16 specific assertions); all eight passed after it. The [app repair](https://github.com/devdasx/oath-wallet/pull/42) merged before the [Bitcoin fixture repair](https://github.com/devdasx/oath-wallet/pull/43). The latter merged as `865c41b3a56ff2c741ace8588a97394433adfbc7` with the same tree as the final tested commit. Resolving a permitted domain to a private IP remains an open boundary. No private endpoint was contacted.

The [SwiftDraw review](ARTWORK-HOSTS-AND-DOM.md) added 19 reviewed files and six partial dispositions. Its pinned DOM suite ran 167 tests across 22 suites. The [resolved package inventory](RESOLVED-PACKAGES.md) adds 5,692 work items across eleven other Xcode checkouts, including two nested repository pointers. All ten members of the compiled project's BitcoinDevKit framework matched the vendor's distribution archive. The [public build log](https://github.com/bitcoindevkit/bdk-swift/actions/runs/36735728184) records the Rust bridge input. Independent binary reproduction is outstanding.

The [Bitcoin fee fixture](BITCOIN-FEE-DIAGNOSTICS.md) had two intermittent assertion failures during the initial full package run. Its test now separates timeouts from malformed quotes and observes correlated background events. Both attempts are retained. The [PSBT review](BITCOIN-PSBT-REVIEW.md) traces request, input, fee and transaction checks and links twelve existing host cases. Exact-source host checks also covered the Bitcoin package (268 passed, 60 skipped) and provider package (1296 passed, 194 skipped), artwork (92 passed, ten skipped) and diagnostics (118 passed, two skipped). The earlier SVG crash regression still passed, all 174 audit helper tests passed, and the generic unsigned iOS Release build succeeded. [Logs and checksums](../evidence/artwork-host/manifest.json). Full GitHub CI and the whole-wallet review remain open.

Previous target: `1dbe6cbabb7397ad86be917e034fb88884fbca8d`.

[OW-2026-030](../findings/OW-2026-030.md) documents a process crash while rendering a synthetic token logo and a second depth-limit bypass. The paired isolated host corpus reproduced signal 11 and one failed assertion before the fix. All five cases passed after it. The full artwork suite passed 84 cases with ten opt-in skips, diagnostics passed 118 with two skips, and the unsigned generic iOS Release build passed (305.2 s). The [source repair](https://github.com/devdasx/oath-wallet/pull/41) merged as `e3c0bc5921492349dad1aaacb90d02eebe366a43` with a tree identical to the tested commit.

The [artwork review](TOKEN-ARTWORK.md) includes all 714 bundled catalog files and the new 353-file pinned SwiftDraw ledger. Forty launcher/preview resources have a cosmetic disposition. Checks on the other assets cover structural integrity and leave semantic identity and renderer behavior open.

[Run 41345235526](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41345235526) completed 64 successful jobs at the earlier application pin `a04bebfafd38f02a441c1a0ee81540882438a99c`. All 64 GitHub artifact ZIP digests and extracted members were verified. The [archived results](../evidence/ci-progress38/oath-ci-progress38-artifacts/verification.json) record 65 passes there, seven expected failures on historical baselines, and 72 verified result-log checksums. The bundler now preserves JSONL test transcripts, Package.resolved and the generated TWHRP header. A [seven-file supplement](../evidence/ci-progress31-supplement/manifest.json) restores these omitted file types from verified progress 31 artifacts. These runs retain their own application targets.

Previous target: `25bcf5bd3418c574d92d63c7d5d5acef39d7d75c`.

[OW-2026-029](../findings/OW-2026-029.md) repairs the loss of early relay replies. Publishing and both subscription paths timed out on the baseline after receiving the correct response. Three write-error controls passed. All six cases passed after the fix. The paired corpus uses the real response timers and a synthetic socket dispatcher. The SDK passed 260 tests with one skip, diagnostics passed 118 with two skips and 164 audit helper tests passed. Public-source checks, diagnostics coverage and generic unsigned iOS Release compilation (528.36 seconds) passed. [Merged source fix](https://github.com/devdasx/oath-wallet/pull/40). The merge tree matches the tested commit.

Four upstream [path/index interface files](CORE-PATH-C-API.md) have additional source dispositions and sanitizer evidence, including 512 deterministic typed/text path comparisons. Numeric and textual constructors have different upper-bound behavior. The pinned upstream test and its build setup failure are archived separately. Complete CI and dependency review at this application target remain outstanding.

Previous target: `4cb121a588583b9b0adef626c05cbedafce3a759`.
[OW-2026-028](../findings/OW-2026-028.md) binds send completion and rollback
to the original local history entry. Ten assertions across six stale-completion
cases reproduce before; eight controls pass and all 14 pass after. SDK checks
pass 254/one skip, diagnostics 118/two skips, 162 audit helper tests,
source/secret checks, diagnostics coverage and unsigned generic iOS Release
compilation (161.63 seconds) pass.

[Source repair](https://github.com/devdasx/oath-wallet/pull/39) merged as `da45a6b791a67f41073a85b4f1db67f9ca6318c5`. Application source matches the tested pin;
116 website and website-deployment differences are in [merge identity](../evidence/history-generation-merge-identity.json).
[Compatibility and scope](HISTORY-SEND-GENERATIONS.md) documents the optional
persisted generation, legacy-record controls and synthetic delivery endpoints.
The repair cannot recall accepted messages or establish every pre-send boundary;
relay acknowledgement bookkeeping and ordering remain open. Full current-target
CI remains unverified. No remote signing exploit or fund loss is claimed.

Previous target: `6d8fda366773726364b0cb8b389d793cd34bd0bd`.
[OW-2026-027](../findings/OW-2026-027.md) repairs duplicate history mutations
and stale cleanup across shared-store instances. Ten assertions across six
controlled races reproduce before; five controls pass, and all 11 pass after.
SDK checks pass 240/one skip, diagnostics 118/two skips, 158 audit helper tests,
source/secret checks, diagnostics coverage and unsigned generic iOS Release
compilation (237.68 seconds) pass.

[Source repair](https://github.com/devdasx/oath-wallet/pull/37) merged as `a853ab33e7739ab04003354d7992c33f0b07ef4b`. Tested application source matches;
97 website-only differences are in [merge identity](../evidence/history-atomicity-merge-identity.json).
[History scope](RPC-HISTORY-ATOMICITY.md) distinguishes individual synchronized
operations from async transport generations, separate processes and direct store
writes. The factory and runtime storage have explicit reviewed scopes; history
and CodableStore retain their unresolved areas. No duplicate app signature or
fund loss was established. Full current-target CI remains unverified.

Previous target: `8508d02deaf965dbe6f46b3c0ca637074234e5da`.
[OW-2026-026](../findings/OW-2026-026.md) binds session responses to the pending
remote request's topic and protocol method. Eighteen assertions across eight
invalid cases reproduce before; four controls pass and all 12 pass after.
SDK checks pass 229/one skip, diagnostics 118/two skips, 154 audit helper tests,
source/secret checks, diagnostics coverage and unsigned generic iOS Release
compilation (160.63 seconds) pass.

[Source repair](https://github.com/devdasx/oath-wallet/pull/36) merged as `0d0f31e4c1f2c77263742d3c796ceb3788634166`. Tested application source matches;
97 website-only differences are in [merge identity](../evidence/response-routing-merge-identity.json).
[Scope](SESSION-RESPONSE-ROUTING.md) documents endpoint substitutes and Oath's
original-topic callers. No remote signing exploit or fund loss is established.
Generic transport routing and concurrent history replacement remain partial;
RPCHistory and the relay responder are reopened for these remaining concerns.
Full current-target CI remains unverified.

Previous target: `57893f12d80eea8203a7e235733f055f5dbd7902`.
[OW-2026-025](../findings/OW-2026-025.md) repairs missing-link-metadata traps
and transport changes made before incoming request validation. Sixteen identical
production cases retain three nil-unwrap crashes, five state assertions and
eight passing controls before; all 16 pass after. SDK checks pass 217/one skip,
diagnostics 118/two skips, and source/secret checks, diagnostics coverage,
150 audit helper tests and unsigned generic iOS Release compilation
(159.85 seconds) pass.

[PR 35](https://github.com/devdasx/oath-wallet/pull/35) merged as `2c4c53ed752508102ea4a786cb3c12f878add3b7`.
The application source matches the tested pin; 97 website-only differences are
recorded in [merge identity](../evidence/link-metadata-merge-identity.json).
[Metadata review](LINK-SESSION-METADATA.md) explains optional persisted fields,
the host UIKit endpoint and the direct synchronous subscriber tests. These do
not establish actual URL association, async error delivery, all outgoing-topic
rules or a reachable Oath app trigger. Full new-target CI remains unverified.

Previous target: `f2019f3e752ee3fb1b57d7259abb8721779f0cc8`.
[OW-2026-024](../findings/OW-2026-024.md) repairs incoming Link Mode message
authentication and response-topic/local-origin binding. The same 16 production
cases record 18 assertions across eight failed cases and eight passing controls
before; all 16 pass after. SDK checks pass 201/one skip, diagnostics 118/two skips,
146 audit helper tests, source/secret validation and diagnostics coverage pass.
Unsigned generic iOS Release compilation passes in 452.21 seconds.

[PR 34](https://github.com/devdasx/oath-wallet/pull/34) merged as `888fa6f53e117bc8b2591c8a6643426d58fa2462`.
Application source matches the tested pin; 97 website-only differences are
recorded in [merge identity](../evidence/link-boundary-merge-identity.json).
[Link review](LINK-ENVELOPE-BOUNDARIES.md) discloses the host UIKit endpoint,
current Oath reachability limits and remaining outgoing/async/metadata boundaries.

The prior [GitHub run 41337776806](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41337776806)
finished 57 successful jobs. [Downloaded evidence](../evidence/ci-progress31/manifest.json)
retains 58 passing result records on `4cfeb14ce9bd85ca2d10017cb053ab421df30cf2`
and seven expected historical failures, with every result log hash verified.
It does not establish the full matrix on this checkpoint's new source pin.

Previous target: `a04bebfafd38f02a441c1a0ee81540882438a99c`.
[OW-2026-023](../findings/OW-2026-023.md) repairs authentication TTL decoding,
expiry conversion and legacy sender chain validation before side effects.
Twenty identical production cases retain 32 assertions across eight failed
cases, eight crashes and four passing controls before; all 20 pass after.
SDK checks pass 185/one skip, diagnostics pass 118/two skips, and source/secret
checks, diagnostics coverage, 142 audit helper tests and unsigned generic iOS
Release compilation (162.94 seconds) pass.

[PR 33](https://github.com/devdasx/oath-wallet/pull/33) merged as `fab9c23e02060aa5a9e98f5000808c85fd14f28e`.
Application source matches the tested pin; 97 concurrent website-only
differences are recorded in [merge evidence](../evidence/auth-boundary-merge-identity.json).

[Authentication review](AUTH-REQUEST-BOUNDARIES.md) records the test seams,
legacy outgoing reachability and unresolved link-response/failure cleanup.

Previous target: `eef7eeb2d46c74aa6528b9b34ef122f9a61ef8ed`.
[OW-2026-022](../findings/OW-2026-022.md) repairs queued session cleanup and
SequenceStore timer teardown. Eight identical production cases retain one
unowned-reference abort, one timer-validity assertion and six passing controls
before; all eight pass after. SDK checks pass 165/one skip, diagnostics pass
118/two skips, and source/secret checks, diagnostics coverage, 138 audit helper
tests and unsigned generic iOS Release compilation (168.75 seconds) pass.

[PR 32](https://github.com/devdasx/oath-wallet/pull/32) merged as `7745d22b8333b71ea57cd7896067128285d06d5d`.
Application source matches the tested pin; 97 concurrent website-only
differences are recorded in [merge evidence](../evidence/cleanup-lifetime-merge-identity.json).

[Cleanup review](CLEANUP-LIFETIME-REVIEW.md) discloses the default-preserving queue
injection, initial fixture-assumption error and reopened authentication review gaps.

Previous target: `d13c1979398ab3dc51d9af18f5bf23821e18262f`.
[OW-2026-021](../findings/OW-2026-021.md) repairs watcher timers and storage
callbacks that outlived their owners. Ten identical production cases retain
four unowned-reference aborts, two duplicate-timer assertions and four passing
controls before; all ten pass after. SDK checks pass 157/one skip, diagnostics
pass 118/two skips, and source/secret checks, diagnostics coverage, 134 audit
helper tests and unsigned generic iOS Release compilation (145.54 seconds) pass.

[PR 31](https://github.com/devdasx/oath-wallet/pull/31) merged as `413b70fbeca15b24e572f7c7f993a62d11a8184e`.
Application source matches the tested pin; 97 concurrent website-only
differences are recorded in [merge evidence](../evidence/watcher-lifetime-merge-identity.json).

[Review scope and remaining work](WATCHER-LIFETIME-REVIEW.md) preserve SDK
lifetime/reachability limits and separate cleanup/concurrency gaps.

Previous target: `05f1f349938c3281810241513bae8beceab35ffd`.
[OW-2026-020](../findings/OW-2026-020.md) repairs discarded relay TTL and skipped
wallet-service expiry validation. The identical eleven-case production corpus
retains six expected assertions across four cases before and seven passing
controls; all eleven pass after. SDK checks pass 147/one skip, diagnostics pass
118/two skips, and source/secret checks, diagnostics coverage, 130 audit helpers
and unsigned generic iOS Release compilation (30.72 seconds) pass.
[PR 30](https://github.com/devdasx/oath-wallet/pull/30) merged as
`5ff8506b87d8ac773d30cc8f38a4c3aa939cc99c`. The application source matches the tested commit;
97 concurrent website-only differences are excluded from the mobile-wallet
verdict and listed in [merge evidence](../evidence/request-lifetime-merge-identity.json).
[Review and remaining work](REQUEST-LIFETIME-REVIEW.md) distinguish the outgoing
SDK API from Oath's incoming request/response path.

Previous target: `8e5b6b0f565026951d7cef9435258daa0b02b9b2`.
[OW-2026-019](../findings/OW-2026-019.md) repairs the SDK's separate-field
account initializer. One case retains two expected assertions before; all seven
identical cases pass after. The corpus includes byte/Unicode mutations, Codable,
bounds and 4,096 seeded tuples. The original line-ending hypothesis did not
reproduce. SDK checks pass 136/one skip; diagnostics pass 118/two skips; source/
secret checks, diagnostics coverage, 127 audit helpers and unsigned generic iOS
Release compilation (152.44 seconds) pass.
[PR 29](https://github.com/devdasx/oath-wallet/pull/29) is merged as
`a92996a8830e39f8ee9cd2a58c41825aaba2e13d`. Its application source matches the tested
commit exactly. Nine concurrent website-only files differ; those changes are
outside the mobile-wallet verdict and are not represented as tested app source.
[Merge identity evidence](../evidence/caip-merge-identity.json) and
[review scope](CAIP-BOUNDARY-REVIEW.md) record that distinction.

Previous target: `2931f8d8f2e0f7dd3d737e2ee1aab32ba39683a4`.
[OW-2026-018](../findings/OW-2026-018.md) repairs namespace requirement loss,
malformed-key handling and optional-unwrapping traps. The identical 15-case
corpus retains 13 assertion failures, two errors rejecting valid inputs and
two crashes before repair, with four passing controls; all 15 pass after.
SDK checks report 118 passes/one skip, diagnostics report 118 passes/two skips,
and source/secret scanning, diagnostics coverage, unsigned generic iOS Release
compilation and 124 audit helpers pass. [Review scope and limitations](NAMESPACE-BOUNDARY-REVIEW.md)
keep parser, lifecycle and remote reachability work explicit.
[PR 26](https://github.com/devdasx/oath-wallet/pull/26) is merged with the
identical tested source tree.

The prior [expiry repair](../findings/OW-2026-017.md) at
`fd002d9272a767352c114e8b752a21f65f0694cc` retains its original 13-case
before/after record. [PR 25](https://github.com/devdasx/oath-wallet/pull/25)
merged that tested tree. Its evidence and limitations remain available.

The previous [event lifecycle repair](../findings/OW-2026-016.md) at
`4cfeb14ce9bd85ca2d10017cb053ab421df30cf2` retains its original nine-case proof
and 14 expected baseline assertions. Those evidence records remain bound to
that earlier source, with broader current SDK regression results recorded above.
[PR 24](https://github.com/devdasx/oath-wallet/pull/24) is merged with the
identical tested source tree. No App Store operation occurred.

The prior [relay metadata repair](../findings/OW-2026-015.md) at
`e7aed8c9d08357df10a4f85be7d069a66fad07f8` retains its separate four-case
before/after proof. Its full [GitHub run](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41291217273)
now has **56 successful jobs**, with downloaded artifacts preserved in
[the evidence manifest](../evidence/ci-progress30/manifest.json). These are
verified prior-target results, not final-target or whole-wallet completion.
[Event lifecycle review](EVENTS-LIFECYCLE-REVIEW.md) records the new source reads,
reproduction limits and prior CI source pins.

[Progress 29](SOLANA-VECTOR-ISOLATION.md) at
`f9cccef32d4508fca13ddbf52d3eb882b5d8f0f1` isolated all 76 unchanged Solana
multisig SDK vectors and regenerated their bytes with pinned SDK tools. Its
1,296 networking passes/194 skips, original CI timeout and tool advisories remain
bound to that earlier source. [PR 22](https://github.com/devdasx/oath-wallet/pull/22)
is merged. The final-target GitHub matrix is not yet verified.

The prior [router-approval repair](../findings/OW-2026-014.md) at
`e46fff5686db48a40103c9dbffe5e830cfc5548a` retains 30 expected assertions before,
nine passing executions after and ten ABI cross-checks. Its
[review and limits](SWAP-APPROVAL-REVIEW.md) and merged
[PR 21](https://github.com/devdasx/oath-wallet/pull/21) remain available.

The previous target `27fcf5f58f6169e1a40fb6afced883bc736d124d` was merged by
[application PR 11](https://github.com/devdasx/oath-wallet/pull/11), merge
`99742291d6124fd2628bbf1653ec0ba5f121456f`, with an identical source tree.
All eight confirmed Core findings have source-built Apple artifacts selected
by the public app; the three aezeed repairs remain included. Their original
[integration evidence](CORE-APP-INTEGRATION.md) stays bound to that earlier
commit. Results do not automatically transfer to later revisions.

## Scope and coverage

The intended scope is the full shipped app and reachable dependencies: custody,
creation/import, storage, authorization, backup, signing, transaction review,
swaps, WalletConnect, providers, diagnostics and build supply chain. Website
files are inventoried but excluded from the mobile-wallet verdict. No production
secrets, funded accounts, live financial transactions or physical devices are used.

The application ledger contains 4,814 files: 288 reviewed, 48 partially reviewed,
11 generated artifacts verified, 4,467 outstanding. The inventory also includes
website changes since the previous source pin; those are excluded from the mobile-wallet verdict. The Wallet Core upstream
ledger contains 3,941 files: 21 reviewed, 20 partially reviewed, 3,900 outstanding.
The selected aezeed Go dependency ledger adds 28 files: 27 reviewed and 1 wordlist verified as data. The source review records three
defects in Go dependency APIs outside the traced Oath call path; the
[original reproductions](AEZEED-DEPENDENCY-REVIEW.md) and
[verified source/archive repairs](AEZEED-DEPENDENCY-REPAIRS.md) remain public.
The Core findings retain their [child-derivation review](CHILD-DERIVATION-REVIEW.md),
[constructor/lifetime reproductions](CONSTRUCTOR-LIFETIME-RESULTS.md),
[first four source patches](CORE-SOURCE-REPAIRS.md),
[extended-key repair](CORE-NATIVE-AND-EXTENDED-KEY.md),
[buffer-alias repair](CORE-DATA-ALIAS.md),
[result-state repair](CORE-RESULT-STATE.md) and
[signing/parser repair](CORE-SIGNING-PARSE.md). No reachable Oath exploit was
established for these dependency APIs. The combined eight-repair native build
passes 2,363 C++ tests and 113 C cryptography checks; both generic Apple
framework archives and packaging also pass.

At the prior `27fcf5f` target, [public app integration](CORE-APP-INTEGRATION.md) passes unsigned generic
iOS Release compilation, 158 targeted security checks, diagnostics coverage,
public-source scanning, and 118 diagnostics tests with two explicit skips.
The two embedded Core framework executable files match the published repaired
artifacts byte-for-byte. This does not establish an App Store binary comparison
or a complete final-target test matrix. Historical failures and the original
integration-outstanding checkpoints remain available.
Standard-library implementation review remains a separate outstanding boundary.
These counts are dispositions, not a security score. Tests and scanners never
convert unread code into reviewed code. See the machine-readable ledgers under
[scope](../scope) and the exact [read notes](READ-NOTES.md).

The [TRON trace and production-code corpus](TRON-SEND-TRACE.md) adds six passing
property cases, nine existing authorization checks, and current-target package
results: OathAnkr 1,208 passed/194 skipped, OathDatabase 703 passed/71 skipped,
zero failures. These results do not establish live-provider or UI behavior.
No new production defect was confirmed. The new CI job is configured but its
GitHub execution remains unverified; no app source was changed.

## Findings and repair status

- [OW-2026-020](../findings/OW-2026-020.md), low: outgoing request lifetime was
  discarded for relay routing and unchecked for wallet-service routing. Fixed
  with eleven identical before/after cases. No incoming Oath bypass was shown.

- [OW-2026-019](../findings/OW-2026-019.md), low: an invalid separate chain argument
  could borrow its missing component from the address. Fixed and retested with
  seven identical cases. Oath's inspected approval path uses a typed chain;
  no app-level signing bypass was demonstrated.

- [OW-2026-018](../findings/OW-2026-018.md), low: namespace validation lost
  required entries or trapped on optional values. Fixed and retested with the
  identical 15-case corpus, including bounded dictionary-order testing. No
  end-to-end Oath exploit or unauthorized signature was demonstrated.

- [OW-2026-017](../findings/OW-2026-017.md), low: session expiry unit mismatch
  and unchecked conversion bounds. Seven expected assertions and three crashes
  before; all 13 cases pass after. Normal Oath session controller checks limit
  the demonstrated impact; no remote exploit or fund loss was established.

- [OW-2026-016](../findings/OW-2026-016.md), low: SDK telemetry opt-out missed
  initialization/message queues and unfinished deliveries. Fixed and retested:
  14 before assertions, nine passing cases after; no secret or fund-loss claim.

- [OW-2026-015](../findings/OW-2026-015.md), low: optional transaction metadata
  was relay-readable outside the encrypted peer message. Fixed at the final
  encoder and retested with 11 before assertions/four after passes. This does
  not demonstrate private-key exposure or resolve all SDK telemetry boundaries.

- [OW-2026-001](../findings/OW-2026-001.md), low: missing object-collection limit in
  the production WalletConnect JSON decoder. Baseline reproduction failed exactly
  one of 6,016 checks; the repaired decoder passed the same corpus. Fixed and retested.
- [OW-2026-002](../findings/OW-2026-002.md), assurance gap: the baseline omitted the
  bridge source needed to rebuild its aezeed archives. Source, pinned modules,
  generators and tests are published. The new replacement archives now reproduce byte-for-byte across two isolated
  builds with the recorded toolchain, while seed and import compatibility tests pass.
  Historical source-to-binary equivalence remains unresolved; its failed comparisons
  are preserved separately from the new artifacts.
- [OW-2026-003](../findings/OW-2026-003.md), informational coverage defect: four EVM
  public account-policy adapters were absent. Fixed with mocked chain-ID and policy
  tests. No direct app caller or fund-loss exploit was established.

- [OW-2026-004](../findings/OW-2026-004.md), medium: plaintext type-2 envelopes
  reached the encrypted relay request dispatcher without a topic key. The same
  four-case regression reports two failures before repair and zero after repair.
  Valid encrypted type-0/type-1 messages still dispatch; tampering is rejected.
  No end-to-end signing bypass or fund loss is demonstrated.

- [OW-2026-005](../findings/OW-2026-005.md), medium: an encrypted response on
  another topic could consume a pending request with the same ID. The identical
  four-case corpus has two failures before repair and four passes after repair.
  Eight additional tests cover separate authentication topics, persistence,
  legacy records and routing-field injection. Old pending Notify handshakes
  remain an unverified boundary of that unused product; no real peer test is claimed.

- [OW-2026-006](../findings/OW-2026-006.md), low: repeated URI decoding
  reinterpreted relay-data contents as a replacement pairing key. The app accepted
  the synthetic input. Eight identical cases give 3 pass/5 fail before and
  8 pass after. Query boundaries and serialization are repaired; this does not
  establish unauthorized signing or fund loss.

Original findings, failed runs and retests remain available. No finding is erased
or downgraded merely to produce a passing summary.

## Preserved f7441b8 validation

On `f7441b8`, seven OathAezeed host tests and 22 aezeed wallet-integration checks
passed. The targeted Bitcoin subset passed 27 tests with one explicit skip;
diagnostics passed 118 with two explicit skips. Public validation, secret scanning,
diagnostics coverage, Go race/vet/module checks, regenerated seed-fixture equality,
and unsigned generic iOS Release compilation passed. No full Bitcoin-suite or
whole-wallet result is inferred from these targeted checks.

The new [aezeed reproduction review](AEZEED-REPRODUCIBLE-BUILD.md) retains the
before/after timestamp and plist-order failures and two matching final builds.
Six additional Go files have source-review dispositions. Three independent ct64
tests passed: all 16,384 S-box lane comparisons, 768 AES differential samples,
a public known-answer vector, short-buffer rejection, and post-reset rejection.
The audit helper suite passes 46 cases. New CI steps check artifact hashes and
execute the primitive tests; the final-target full matrix has not yet completed.

## Preserved 90b5b28 validation

On `90b5b28`, all 14 send-status host tests and all five Solana property cases
passed. Diagnostics reports 118 passes and two explicit skips. Public source,
secret-scan and diagnostics-coverage checks passed, as did unsigned generic iOS
Release compilation. No runtime UI or App Store verification is claimed. The
new full CI matrix is pending; these targeted passes do not complete the audit.

## Preserved a65601b local validation

The [TON review increment](TON-BOUNDARIES.md) adds five production-module property
tests on the same `a65601b` source: 1,004 independent amount vectors, 256 cell
graphs, 4,096 byte mutations and dictionary/structural limits. All five cases
passed. [Final evidence](../evidence/ton-properties/final/ton-properties.json)
and the initial harness-reporting failure are both retained. No new application
vulnerability was confirmed in that increment. The audit-helper suite now has
36 passing tests; the new properties have a dedicated audit-only CI job.
The amount oracle uses Python integer arithmetic; cell round trips are not
independent consensus verification or exhaustive fuzzing.

[Results](../evidence/uri-boundary/results.json),
[identical-corpus reproduction](../evidence/uri-boundary/reproduction/results.json),
[app entry trace](../evidence/uri-boundary/reproduction/app-boundary.json), and
[published hashes](../evidence/uri-boundary/manifest.json) identify `a65601b`:

- Pairing URI: five failed cases before, eight passed after; production app-parser
  trace passes five assertions without pairing or opening any connection.
- SDK: 56 passed, one intentional skip, including 13 existing upstream URI cases.
  The skipped Verify fixture passes in its own process.
- Scanner: 13,635 assertions, 715 synthetic QR image round trips, 42 chains,
  260 public BIP39 vectors in ten languages. Link checks: 145 assertions;
  recognizer/capture-state lifecycle checks: 2,021 assertions.
- Diagnostics: 118 passed, two explicit skips. Source-boundary validation,
  root secret scan and diagnostics coverage passed.
- Generic unsigned iOS Release build passed in 36.29 seconds using the existing
  isolated cache. Source identity was checked before and after compilation.

See [input review notes](INPUT-BOUNDARIES.md) for exact read dispositions and
remaining runtime/dependency boundaries. The audit runner now exposes only the
three offline scanner modes, validates their final assertion summaries, and
adds these checks to CI. The 31 helper tests pass. Actionlint passes with only
its unknown `xcode-27` runner-label diagnostic explicitly excluded; the standard
invocation does report that label and is not claimed to pass unmodified.
The new 90b5b28 full GitHub matrix has not completed. No simulator, phone,
real pairing peer or App Store operation was used.

## Authorization and CI-failure follow-up

The TON application trace now adds **19 passing authorization assertions** on
`a65601b`, including lock/reopen and cancellation during unfinished preparation.
The exact dependency-pinned result and adapter limitations are documented in
[TON boundaries](TON-BOUNDARIES.md#application-authorization-and-recovery-increment).

The full GitHub run `41248923305` exposed an app-parser compilation timeout
and a database deadline-observation `invalidTransition`. Original failures are
retained. The runner records timeout failures and kills only its own children;
its cold-build allowance increased from 360 to 900 seconds. The cold GitHub
boundary rerun [41250799019](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41250799019)
now passes inventory, parser, relay boundary and TON jobs. Full host, dependency,
entropy and Release-build jobs were deliberately skipped in that boundary-only
run; it is not a successful full matrix. See its [exact result records and durable
archive hash](../evidence/ci-41250799019-boundaries.json).

The database test fixture raced a running worker: signed rows are already eligible
for confirmation, but the fixture attempted a later synthetic signed-to-broadcast
transition. Production correctly rejected that stale transition. Test-only commit
`90b5b28a6f3852319a24d74143863f2b57837c4d` stops the synthetic transition while
the worker is active and adds an explicit confirmation-before-broadcast case.
All 14 send-status host tests pass. The new test checks that stale broadcast cannot
undo confirmation, change signed bytes or recreate a job. No production transition
rule was relaxed. [Before/after evidence](../evidence/status-fixture/results.json)
keeps the original CI failure distinct from the corrected local test run.
Its unsigned generic iOS Release build, public-source validation, secret scan
and diagnostics checks passed. The test-only source is merged in [PR 7](https://github.com/devdasx/oath-wallet/pull/7).
Its branch commit is the new review target. Earlier a65601b results remain pinned
to that source; a new full matrix is required for the test-fixed target.

The [a65601b full matrix](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41248923305)
finished with 37 successful jobs and three failures:
raw Go advisories, the old app-parser timeout and the database fixture race.
[Final metadata](../evidence/ci-run-41248923305-final.json) and
[34 hash-verified result records](../evidence/ci-41248923305-results.json) preserve
the completed outcome and durable evidence archive.
The raw Go vulnerability scan remains a failing check with documented
reachability/provenance gaps. Passing compilation cannot override those gaps.

## Solana source and adversarial-test increment

The [Solana review](SOLANA-BOUNDARIES.md) traces wallet binding, native/SPL plans,
multisig serialization and WalletConnect parsing/signature preservation through
fourteen complete source files. The initial four production-module tests pass:
528 independent Python Base58 vectors, all truncations of three public SDK
transaction fixtures, signature-slot preservation and 2,048 deterministic
mutations (703 accepted with checked invariants, 1,345 rejected during parsing).
The extended five-case run also passes 1,038 independent modular-arithmetic
checks of the public-input curve predicate. All 39 audit-helper unit tests pass.
The audit-only workflow adds a dedicated source-pinned Solana job. This is
bounded host evidence, not consensus verification or a completed Solana review.

## Preserved e352f56 local validation

[Results](../evidence/response-topic/results.json),
[identical-corpus reproduction](../evidence/response-topic/reproduction/results.json),
and [published hashes](../evidence/response-topic/manifest.json) identify
`e352f56d0fb3be035c3600e646e3f9133adb9ef4`:

- Cross-topic response corpus: two expected baseline failures; four fixed passes.
- Eight new routing/restart/legacy/injection checks pass.
- Full SDK: 35 passed, one intentional skip. The skipped case passes separately.
- Diagnostics: 118 passed, two explicit skips, zero failures.
- Generic iOS Release compilation passed without signing, using an isolated
  incremental cache; no source changes occurred during that build.
- Source-boundary validation, root secret scan and diagnostic coverage pass.

The reply-topic field is local routing metadata, excluded from JSON-RPC. Legacy
ordinary records decode unchanged; legacy authentication records recover their
expected topic from the stored requester public key. No wallet storage identity,
transaction encoding or signing secret was migrated. The full current-source
GitHub matrix remains incomplete, and no simulator or actual peer was used.

## Preserved f506dd8 local validation

[OW-2026-004 evidence](../evidence/relay-envelope/results.json), the
[reproduction](../evidence/relay-envelope/reproduction/results.json), and its
[hash manifest](../evidence/relay-envelope/manifest.json) identify source
`f506dd8b820476296a6348c0ccbbdc42164c21f5`:

- Four relay boundary regressions: two expected baseline failures, four fixed passes.
- Full SDK host tests: 23 passed, one intentional skip. The skipped case passes separately.
- Diagnostics: 118 passed, two explicit skips, zero failures.
- Stable-source generic iOS Release compilation passed without signing.
- Public-source boundary, root secret scan and diagnostics coverage passed.

One runner attempt undercounted a case because a known SwiftPM warning was
interleaved in a test-result line; its failure is preserved alongside the tested
parser repair and later successful run. A build overlapping an early reproduction
is explicitly excluded as final-source identity evidence; the subsequent stable
build is used. The current full GitHub matrix is not yet complete.

The earlier d2fccbe8 CI run [41241757605](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41241757605)
finished with 31 successful jobs and three failures: the retained raw module
advisory scan, the subsequently corrected OathAnkr test expectations/timeout, and
a Sui host job whose detailed artifact failed to upload (ENOTFOUND). A subsequent
local Sui check passed nine cases on f23413c; the CI command failure's cause is
not established. These are not silently converted to successful CI outcomes.

The later [f23413c CI rerun](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41244250116)
finished with **33 successful jobs and one failure**. Every host job, inventory,
parser, aezeed-source and unsigned generic iOS build job succeeded. The failure
is the retained raw Go module advisory scan: 40 unique advisories. The separate
selected-source triage does not prove the historical binary is unaffected.
[Final metadata](../evidence/ci-run-41244250116-final.json),
[29 hash-verified result records and durable archive identity](../evidence/ci-41244250116-results.json)
retain this outcome; the prior progress snapshot remains unchanged. OathAnkr
reports 1,208 passed and 194 explicitly skipped, with no failures. This does not
establish the cause of the older Sui failure or validate the current a65601b
source. Its separate full matrix is still incomplete.

## Preserved validation on the previous source commit

[Exact results](../evidence/diagnostic-repair-results.json) and per-case logs for
`f23413c848d202c2b3c7061bdb349e07144ab0a2` (not relabeled as current-target results):

- OathAnkr host package: **1,208 passed, 194 explicitly skipped, zero failed**.
- OathDiagnostics host package: **118 passed, 2 explicitly skipped, zero failed**.
- Generic iOS **Release compilation passed without signing**.
- Public-source boundary validation, Gitleaks root scan and the diagnostic
  coverage guard passed. The latter observed 713 catch sites; it is not an
  independent review of all those sites.

Eighteen old diagnostics tests expected excluded availability failures to enter
the local outbox. The repairs retain real recovery/cancellation assertions and
add retained validation-error controls, chain/correlation checks and privacy
checks. Production diagnostic behavior was not changed to satisfy tests. The
76 official Squads vectors now run in four bounded 19-vector cases, retaining
all message, signature, serialization and size assertions. The original single
case exceeded the audit runner's 120-second limit; its failed log is preserved.

Earlier commits have additional host and GitHub evidence, including parser,
backup, database, authentication, lifecycle, signing and security checks. Those
passes are **not relabeled as final-commit passes**. Every new full GitHub matrix
must independently run on its exact pin; queued or cancelled jobs are not passes.
The required final matrix is not yet complete. Each run records its real toolchain.

## Dependency evidence

Wallet Core 4.8.4 release ZIP hashes match the app manifest; its source tag pins
`d40d24a63d92619167903369308bf0e2f7eb3a59`. This verifies downloaded archive
integrity, not source-to-binary identity.

The aezeed source graph was resolved for arm64 macOS, iOS and iOS Simulator
compilation targets with Go 1.26.5. No simulator was launched. Forty retained
module advisory records identify affected packages absent from all three selected
graphs. Exact import metadata, explicit advisory aliases, module versions and
regression-tested triage are retained. Raw OSV failures remain visible; this is
source-level non-reachability evidence, **not clearance of historical binaries**.

Five RFC 7914 known-answer vectors and 1,000 deterministic bitstream cases pass
against the pinned production dependency implementations. Existing upstream AEZ,
BStream, scrypt, PBKDF2 and Blake2b tests also pass with the race detector. All
2,048 aezeed words and their order match the app and pinned Wallet Core resources.
The 1 GiB RFC vector, timing/side-channel measurements, complete memory-erasure
proof, and unread cryptographic implementations remain outside these results.

## Evidence boundaries and outstanding work

The host harnesses substitute selected OS, networking, hardware and derivation
boundaries. Generic compilation does not exercise Face ID, real iOS Keychain,
WalletConnect peers or transaction broadcasts. The only simulator runtime checks in progress 12 exercise Core C ABI derivation
with public fixtures; full-app runtime and visual checks were not performed. Opt-in live tests remain skipped.

Swift 6.4 parallel XML omitted skip markers in an earlier run. The audit now
retains a separate XCTest process log and classifies its actual result, with
Swift Testing reported separately. Earlier misleading XML remains as historical
evidence with this qualification. Initial build-environment failures are also
retained; they are not called production vulnerabilities.

Remaining work includes outstanding application/chain source, reachable Reown and
cryptographic code, dependency/binary provenance, additional adversarial tests,
and the exact final-source CI matrix. The completion checker rejects these gaps.
There is **no whole-wallet successful-completion verdict**.

## Progress 10 — selected Go dependency review

The remaining 14 selected Go files were read in full and their hashes reverified.
The expanded harness separates ten positive validation cases from three reproduced,
unrepaired hazards in APIs outside Oath's traced call path. See
[the dependency review](AEZEED-DEPENDENCY-REVIEW.md). This increment changes audit
evidence, not application code; progress-9 exact-pin build evidence still applies.
The full review and current-target CI matrix remain incomplete.

## Progress 11 — mnemonic and derivation boundaries

The actual pinned C/C++ mnemonic, derivation parser, HMAC and PBKDF2 implementations
passed the new macOS AddressSanitizer/UndefinedBehaviorSanitizer harness. It covers
150 seed vectors, 2,048 word indices, 40,000 bounded malformed inputs, 242 HMAC
vectors and 288 PBKDF2 vectors. Eleven Swift checks passed against Oath's actual
passphrase guard without sanitizers. Forty-nine audit-helper tests passed.

Eleven upstream files and the application passphrase guard now have explicit
source-review dispositions; HDWallet/PrivateKey and BIP32 leads remain partial.
The result retains low-level zero-round and passphrase-truncation behavior as
characterizations, not newly repaired wallet bugs. See
[the complete scope and reproduction notes](MNEMONIC-DERIVATION-REVIEW.md).
The review harness's initial extraction/header failures are retained alongside
the subsequent passing results. No application source changed in this increment;
the prior exact f7441b8 generic-iOS Release build remains the compilation evidence.

There are 7,692 outstanding items in the current completion ledger. The older
CI run and final-target matrix are not replaced by these local boundary passes.
No successful whole-wallet conclusion or App Store equivalence is claimed.

## Progress 12 — restoration path repair

[OW-2026-007](../findings/OW-2026-007.md) is fixed and merged. The identical
host regression fails before the fix and passes 140 checks afterward. A separate
minimal process using the actual Core 4.8.4 simulator framework confirms 112 key
equalities across seven chains, eight paths and two public seeds. Host derivation
is substituted; the framework experiment and application host tests are distinct.
The recovered key is preserved, including root-path backup round trips.

On the current target, diagnostics passed 118 tests with two explicit skips;
public-source and secret scans, diagnostics coverage, and unsigned generic iOS
Release compilation passed. Fifty-two audit-helper tests passed. The full
current-target GitHub matrix has not yet completed. See [the review and exact
reproduction commands](RESTORED-PATHS.md) and [results](../evidence/restored-path/results.json).

The earlier GitHub run 41250786693 finished with 40 successful jobs and one failed
scanner job: raw OSV module advisories keep that check red. This is evidence for
its older a65601b source, not the new target. The progress-11 upstream mnemonic
job passed on GitHub against f7441b8; that full matrix remains in progress.
No successful whole-wallet verdict is issued. Remaining derivation, secret-lifetime,
application/dependency review and provenance gaps stay explicit.

## Progress 13 — upstream child derivation and API failures

The production C derivation harness passed 52 official SLIP-0010 vectors,
1,920 independent hardened-path cases, 33 public/private child comparisons,
20,000 malformed extended-key calls and two unchanged-on-failure checks with
ASan/UBSan. Fifty-five audit-helper tests passed. Its static-library runner,
fixture provenance, compiler identity, input hashes, logs and initial unsuccessful
direct-link attempt are retained in [the evidence](../evidence/child-derivation).
The harness is now part of the pinned GitHub workflow; its new CI run must be
evaluated independently from the completed local result.

Two separate subprocesses reproduce a null dereference for an invalid curve and
a missing Nano public-key-generation branch. These dependency API failures are
**unrepaired**, not successful fix regressions. The traced app path does not
establish reachability; ordinary Core Nano public-key generation uses a different
implementation. See [scope, source lines and reproductions](CHILD-DERIVATION-REVIEW.md).

The 32-byte HDWallet constructor lead was narrowed by inspecting all matched
application constructor calls and the explicit upstream specialization uses.
No application patch was justified by that trace. Secret lifetime, transitive
cryptography and other caller contracts remain open. No new application source
change, simulator/device use, App Store upload or submission occurred in this
increment. The completion ledger still reports 7,695 outstanding items; it does
not convert passing derivation tests into complete file coverage.

## Progress 14 — multisig recovery and constructor lifetime

Twenty-three additional files now have hash-bound source-review dispositions,
covering the multisig recovery documents, wallet adapters, dispatch and two
backup test files. Three already-reviewed files received additional scope notes.
The current-target backup package passed 58 XCTest cases plus one Swift Testing
case, with zero skips. The new production-package mutation harness passed 197
serialization checks across eleven recovery families. It does not substitute
fake identities for crypto validation and then claim signing was tested; its
scope is strictly serialization. See [review notes](MULTISIG-RECOVERY-REVIEW.md).

An isolated compilation of exact upstream constructor/destructor bodies, their
real class header and production mnemonic/KDF implementations passed 22 positive
checks in each of two assertion configurations. Separate deterministic cases
reproduce the invalid 32-byte mnemonic/entropy API behavior and an entropy
allocation that remains unwiped immediately before free. These unrepaired
dependency limitations are not newly fixed app vulnerabilities. Source call
tracing still selects the safe 64-byte specialization for Oath's creation paths.
See [method and qualifications](CONSTRUCTOR-LIFETIME-RESULTS.md) and
[complete retained results](../evidence/constructor-multisig).

No application source changed; the existing exact-target generic iOS build
remains the build evidence. The new audit workflows need their own GitHub run.
The full matrix, transitive dependency review, broader secret lifetime and
binary-provenance gaps remain open. The completion ledger now has 7,671
outstanding items. No simulator, device or App Store operation occurred in this
audit increment.

## Progress 15 — dependency source repairs and paired retests

The four Core defects documented in progress 13/14 now have a published patch
and paired before/after host evidence. Invalid curves reject safely, Nano key
caching matches the separate public-key primitive, unsupported 32-byte mnemonic
expansion rejects before the KDF writes, and the observed entropy allocation is
zeroed before deallocation. Positive derivation and constructor compatibility
checks pass on both sides. The 62 audit-helper tests pass; an initial path-alias
fixture failure is preserved. [Scope, commands and limitations](CORE-SOURCE-REPAIRS.md).

These are source repairs, not replacement Apple frameworks or a changed Oath
application. Each dependency finding is now explicitly included in the
machine-readable findings index with integration outstanding. Source coverage
counts are unchanged: testing does not establish review of unread components.
Full dependency compilation, final-target CI, broader secret lifetime and
binary provenance remain unfinished. No simulator/device or App Store use.

## Progress 16 — full native suites, fifth dependency patch and honest scanner gate

Complete native Core/Trezor/Rust/protobuf implementations were built from the
pinned source with the four earlier repairs. The real upstream suites pass
2,363 C++ tests (613 suites) and 113 C cryptography checks. This optimized host
build is separate from the previous isolated sanitizer harnesses and from the
distributed Apple frameworks. Build logs, tool versions, input hashes and failed
setup/test attempts are preserved in [native evidence](../evidence/core-native).

DEP-CORE-005 repairs a public/private extended-key type confusion in an unused
C++ API. The unchanged 94-case regression reports 21 failures before and zero
after; the full 2,363-case upstream suite also passes with that production
translation unit repaired. The key incorrectly returned before repair is not
the private key corresponding to the supplied xpub. No Oath application call or
fund-loss exploit was established. [Detailed scope and recipe](CORE-NATIVE-AND-EXTENDED-KEY.md).

The completed historical GitHub run 41257431422 has 41 successful jobs and one
scanner failure on `f7441b8`. Its raw 40 advisory occurrences are retained.
An exact-source gate now separates that raw output from selected-source
classification; the historical replay has zero unresolved classifications.
Wrong source/locks, malformed reports, execution errors and affected compiled
packages remain failures. Ten added tests bring the helper suite to 72 passes.
This replay does not turn the historical workflow green or prove a current-target
CI pass. [Gate repair and evidence](ADVISORY-GATE.md).

One additional upstream file has a manual hash-bound disposition. Compilation
does not expand manual coverage. Three previously documented unused Go API
defects are now also explicitly open in the findings index. The completion
ledger has **7,679 outstanding items**; the increase includes these recorded
findings and the required advisory gate, rather than hidden or waived work.
The final-target matrix is still active at publication. Native CI preparation,
Apple framework integration, dependency provenance and full source review remain
unfinished. No simulator, physical device or App Store operation occurred.


## Progress 17: integrated aezeed repairs

Application PR 10 integrates DEP-AEZEED-001 through DEP-AEZEED-003 in public source.
The identical paired regression corpus reports four failing top-level tests on
original dependencies and all five passing after repair (25 nested cases; 30
pass events total). The 512 MiB GCM tests exercise each truncated length field
against standard Go GCM. Ten independent positive tests pass, including 24,576
S-box lane comparisons, 1,536 AES differential samples, 514 GHASH lengths and
220 independent BLAKE2b vectors.

On the exact current target, seven aezeed host tests pass; diagnostics has 118
passes and two explicit skips. Public-source and secret checks, diagnostics
coverage, the prepared Go race/vet/vector script, and unsigned generic iOS
Release compilation pass. Six new integrity-helper tests bring the helper
suite to 78 passes. Original failures, preflight pin rejections, and actual
before/after logs remain under `evidence/aezeed-repairs` with original and
published hashes.

Two isolated builds at `0d41065b` match all ten framework files. The final
metadata-only commit has identical sixteen bridge inputs and ten framework
hashes; that comparison is separate evidence, not a relabeled rebuild run.
The previous 02a6e8a validation does not count as a complete matrix for this
new target. Whole-wallet review and Core Apple integration remain incomplete.


The fresh raw OSV scan retains 40 advisory occurrences. Their affected import
paths are absent from all three selected target graphs, so the exact-source
gate passes with zero unresolved dispositions. `govulncheck` separately exits
zero on the prepared patched source. This is source-reachability evidence, not
module-wide or historical-binary clearance. The complete raw responses remain
under `evidence/aezeed-repairs/advisories`.

The earlier corrected gate also passed in GitHub run
[41264140940](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41264140940)
on target 02a6e8a. That prior-target result is preserved separately. The current
completion gate reports 7,679 outstanding items; new required exact-target
checks remain pending even where an earlier target passed them.


## Progress 22: cancellation repair and offline diagnostic coverage

[OW-2026-008](../findings/OW-2026-008.md) closes a queued refresh admission race.
The identical regression failed in ten of ten baseline runs and passed in ten
of ten fixed runs, with network denied and public synthetic responses. The
original CI failure, exploratory non-reproduction and compiler-cache path-alias
failure remain published. The final production fix is merged in app PR 12.
A separate TRON test wait-predicate correction preserves both assertions and
the original time budget; ten additional isolated repetitions pass.

On exact final target `2eef5a4912ce1680cd174c7596471620ffcf129e`, OathAnkr has
1,210 passes/194 skips, OathDatabase 704 passes/71 skips, and OathDiagnostics
118 passes/two skips. Unsigned generic iOS Release compilation, source/Gitleaks
validation and diagnostic coverage pass. The final checks explicitly reuse
isolated build directories. The preceding fresh build at `66e60330` and proof
that only a test predicate changed are retained separately. Nine failures in
the first networking run and one in the second are not erased or relabeled.

Eight enabled offline diagnostic modes and eight control skips pass under a
network-denial profile; all eight also ran on the final target. Ninety audit
helper tests pass. [Diagnostic source dispositions](DIAGNOSTIC-MODES.md) mark
privacy filtering and runtime integration partial, not universally verified.
The completion checker still reports 7656 outstanding items. Full source/dependency
review, remaining final-target checks, historical binary provenance and fresh
GitHub execution remain gaps. Run 41270221065 on `92423215` finished 42 jobs
successfully and failed two; the report distinguishes its cancellation failure
from its protected-startup prerequisite DNS error. Local passes are not a
claim of a successful current-target GitHub matrix.

No simulator, physical device or App Store operation occurred. See the
[durable raw evidence](../evidence/refresh-cancellation) and acceptance checklist.

## Progress 23: EVM send trace and response boundary repair

The new informational finding [OW-2026-009](../findings/OW-2026-009.md) shows
that the standalone pre-broadcast chain check omitted the EVM client's 8 MiB
response bound. The default transport already limits streaming to 64 MiB;
this is not an unbounded download or a demonstrated fund-loss vulnerability.
The same regression fails in three baseline processes and passes in three
fixed processes. Two controls pass in each process before and after. Raw logs,
fixture/binary hashes and original source revisions are preserved.

On the exact current target, OathAnkr passes 1,213 cases with 194 explicit skips;
OathDiagnostics passes 118 with two skips. All 22 EVM authorization host checks,
public-source/Gitleaks validation, diagnostic coverage and generic unsigned
iOS Release compilation pass. The build reuses an isolated directory. Ninety-two
audit-helper tests pass. The [EVM trace](EVM-SEND-TRACE.md) records what was
read and keeps nonce-helper API, chain-protocol, Safe bytecode and broader
integration questions partial. No new property-fuzzing or live-chain proof is
claimed by this increment.

The completion checker reports **7,655 outstanding items**. Current-target
GitHub execution remains pending behind earlier queued work; previous-target
successes do not establish a fresh full matrix. All historical failures remain
in the evidence. No simulator, physical-device or App Store operation occurred.

## Progress 24 — delegation nonce boundary and Safe cross-check

Application target `2e51f0bcd3e710c35a1d78ee93746f6a8f202fdc` is published in
[PR 14](https://github.com/devdasx/oath-wallet/pull/14). Merge
`76072b2a33bfa3a56ec295c60ed5e39c5bb6a955` has the same tree,
`f96f482c8cf0355ed5b8bc89741b12560a854747`.

[OW-2026-010](../findings/OW-2026-010.md) confirms an unchecked increment in the
public delegation-sizing helper. Three baseline processes trap at the maximum
nonce; LLDB identifies the production arithmetic-overflow line. Three more
baseline runs accept the next invalid boundary, failing the rejection assertion.
All six control executions pass. With the three-line guard, the identical four
cases pass in each of three processes (12 passes). No reachable app exploit is
established: existing quote/signing/verification callers already validate this
bound. The helper remains usable for provisional, unfunded fee estimates.

The [Safe source cross-check](SAFE-CONTRACT-CROSSCHECK.md) compares the app's
policy, client and receipt behavior with selected Safe 1.4.1 contract semantics
at an exact source commit. A suspected event-indexing mismatch was ruled out.
The cross-check is not contract compilation, deployed-code verification, or
local/mainnet EVM execution. Permission-batch follow-up reads and remaining
connected authorization questions are recorded in READ-NOTES.

Current-target local checks:

- OathAnkr: 1,411 selected, 1,217 passed, 194 explicit skips, zero failures;
  334.42 seconds including isolated host-package compilation.
- OathDiagnostics: 118 passed, two explicit skips, zero failures; 7.59 seconds.
- App EVM authorization harness: 22 checks passed, 67.80 seconds; production
  vault/PIN/imported signer with substituted biometrics, no HD derivation.
- Public/Gitleaks and diagnostic coverage checks passed.
- Generic unsigned iOS Release build passed in 116.17 seconds using the
  existing isolated build directory; OathAnkr was recompiled. This is not a
  fresh-from-empty iOS build or a runtime test.
- 95 audit-helper tests passed. Workflow lint passes when filtering only the
  existing unknown `xcode-27` runner-label warning; both lint outputs are saved.

The previous GitHub run
[41272454184](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41272454184)
completed with 44 successful jobs and one failed artifact-upload job. Its Aptos
host test passed, then GitHub's artifact request failed with DNS ENOTFOUND. Raw
job logs and metadata are preserved. It remains a failed run, not a source test
failure or a green matrix. Current-target GitHub results remain pending and
must be assessed separately from these local checks.

Durable logs, fixture/binary/toolchain hashes and before/after results are in
[`evidence/evm-delegation-nonce`](../evidence/evm-delegation-nonce). The application
ledger now has 4,678 files: 192 reviewed, 29 partial, 10 generated-verified and
4,447 outstanding. The completion gate still reports 7,654 outstanding items,
including older-source-only required checks. No whole-wallet completion,
independent certification or App Store binary-equivalence claim is made.


## Progress 25 — permission batch revocation during signing preparation

[OW-2026-011](../findings/OW-2026-011.md) confirms that ending, replacing or
expiring a consumed batch grant did not stop a signer waiting on preparation.
Locking and task cancellation already rejected it. The fix rechecks the grant
immediately before synchronous signing and before returning bytes on EVM, TRON
and Solana. Existing single-use scope/fee checks and durable journal semantics
remain intact. This is a low-severity lifetime defect for an already approved
removal, not a demonstrated arbitrary-transfer bypass or live fund loss.

Regression baseline: `976971f0ca3362cfba8c63bc738bd80d15abf096` includes the
controllable monotonic grant clock and completed host adapters, with production
authorization behavior still unfixed. Fix: `da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b`.
[PR 15](https://github.com/devdasx/oath-wallet/pull/15) is merged as
`00e803665a6b030ed1c035939866e739b2196d57`; both commits have tree
`25b706f9c136e26c850c1204fee974f33b57b5dd`.

- The same 21-scenario, 84-assertion corpus runs three times per phase with
  networking denied. Before: 27 expected failures and 225 passing controls.
  After: all 252 assertions pass. Actual returned signatures are verified by
  the production crypto paths. Fixture hashes match and binary hashes differ.
- Existing host authorization checks pass: batch 11, EVM 22, TRON 9, Solana 27
  (69 total). They use synthetic credentials and production vault/imported-key
  signers with substituted biometrics/HD paths; no broadcast or device is used.
- OathDiagnostics: 118 passed, two explicit skips, zero failures (7.72 seconds).
  Public-source/Gitleaks and diagnostic coverage checks pass.
- Generic unsigned iOS Release compilation passes in 150.54 seconds, reusing
  the isolated build directory and recompiling the changed vault. This is not
  a fresh-from-empty build, simulator test or physical-device check.
- Audit tooling: 97 helper tests pass. Workflow lint reports only the known
  `xcode-27` label warning; filtering that exact warning passes. Both outputs
  are retained. The new paired CI job is pinned, read-only and has no deployment
  credentials; it has not yet supplied a completed GitHub result.

The initial test fixture failed because its host mode selected incomplete
TRON/Solana adapters. A later build failed because Clang's cached module paths
mixed `/var` and `/private/var`; the successful pair used a fresh canonical
scratch directory. Both failed attempts remain in the bundle and are not
counted as reproduced security findings. The wrong-source-pin preflight was
rejected before execution. Earlier GitHub run 41281531851 remained pending with
no jobs at the recorded check; this is not a green full-matrix result.

[Permission source review](PERMISSION-BATCH-REVIEW.md) gives explicit read scope
for nine production files and the new fixture. The large vault actor and host
generator remain partial. The app ledger now contains 4,679 files: 202 reviewed,
29 partial, 10 generated-verified, 4,438 outstanding. The completion gate reports
**7,644 outstanding items**, including required checks not run on this exact
revision and upstream source/provenance gaps. Prior results keep their pins.

The 169-file evidence bundle is under
[`evidence/permission-batch-races`](../evidence/permission-batch-races), with
sanitized logs, original/published hashes, seeds implicit in the synthetic
fixtures, source pins, durations and toolchain/binary hashes. No App Store
upload, submission, simulator or physical device operation occurred. The whole
wallet review remains incomplete and is not independent certification.


## Progress 26 — permission readback consistency and discovery review

[OW-2026-012](../findings/OW-2026-012.md) is an informational API consistency
finding. A late opposite readback preserved verified history but overwrote the
batch result, potentially misleading a presentation that trusts both. The fix
requires the same successful pending-history transition before batch/job writes.
No normal-app duplicate callback sequence, signing bypass or fund loss was
established. The status worker already excludes overlapping checks for a send.

Regression-only baseline: `b7ff1f5eab70b244ba64a68da10addf3a4d8c4c4`.
Fix: `8f5c27c030fdd85e1d5c3c18d9da8aa92ac04c79`. [PR 16](https://github.com/devdasx/oath-wallet/pull/16)
merged as `fd84ae5679a5833fa7fc294bff5cf657fff603f5`; both have tree
`c735d78f179e78a1138efe86d9566609bd842cc7`. No database migration or stored identity changed.

- Paired host regression: three methods, each in three network-denied processes.
  Before: six exact batch/history failures and three passing reorganization
  controls. After: all nine pass. Fixture hashes match; binaries differ.
  Production SQL, imported-key signing, durable journals and database restart
  are exercised. Reorganization permits a fresh result in both directions.
- Final-target OathDatabase: **707 passed, 71 skipped, zero failures** (324.35 s).
  OathDiagnostics: **118 passed, two skipped, zero failures** (19.14 s).
  Public-source/Gitleaks and diagnostics coverage checks pass.
- Generic unsigned iOS Release build passes in **411.78 seconds**, reusing the
  isolated build cache. This is not a fresh-from-empty build or runtime test.
- Earlier-target `da7a88a` broad suites also completed: database 704 passed/71
  skipped; OathAnkr 1,217 passed/194 skipped; zero failures. Their results retain
  their earlier source pin and are not counted as validation of the new commit.
- Audit tooling: 99 helper tests pass. Workflow lint has only the known custom
  `xcode-27` runner-label warning; filtering that exact warning passes. The new
  paired CI job pins inputs/actions and has no deployment credentials.

[Discovery/source review](PERMISSION-DISCOVERY-REVIEW.md) records 22 whole-file
reads, including eight production discovery/history/UI/status-worker files and
related fixtures. Optional provider and local-chain fixtures were inspected but
not enabled. The local-chain generators' external dependency lock/provenance
and deployed-contract equivalence remain gaps, not silently passed checks.

A live GitHub metadata refresh now records run
[41277015374](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41277015374)
as successful with 49 jobs, for the earlier target `6124254d43ee7a98d4a364639671ccfc52155396`.
This is workflow metadata, not a transfer of its results to the current commit.
Run 41281531851 is cancelled with zero jobs; run 41282913488 was queued with
50 jobs at the recorded check. Their records supersede the earlier status
observations without erasing them. New-target CI remains separately assessed.

The application ledger contains **4,680 files: 224 reviewed, 29 partial,
10 generated-verified and 4,417 outstanding**. The completion gate reports
**7,627 outstanding items**, including old-target-only required checks and
upstream/provenance gaps. The review remains in progress.

The 3,153-file evidence bundle is under
[`evidence/permission-discovery`](../evidence/permission-discovery), with original
and published hashes, sanitized logs, source/fixture/binary pins, durations and
explicit skips. No simulator, device, funded account, broadcast, App Store
upload or submission occurred. This is not independent certification or a
whole-wallet completion verdict.

## Progress 27 — swap destination identity and review boundaries

The canonical EVM-chain mapping now supplies progress destination comparison,
fixing the omitted Polygon case. This is informational/reliability: false pending
presentation, not signing bypass or demonstrated fund loss. The original fixture
commit is `8fa6ee3bf99caf78ab71997b5642e323cccb95da`; the fixed commit is
`8dcc9c4c50eae2010b648782c0582c3db70c6357`. PR 17 merged as
`db7f3340e652160f1b5eefa16afb9817f395786e`, with identical tree
`84cadb5882dbde25ee921d7a2858c4ac172ef603`.

- Same three methods in three network-denied host processes: three failing Polygon
  executions with four exact assertion failures each, six passing control executions
  before; all nine pass after. Fixture hash is identical; binary hash changes.
- OathAnkr: **1,220 passed, 194 explicitly skipped**, zero failures.
- OathDiagnostics: **118 passed, two explicitly skipped**, zero failures.
- Public-source scan and diagnostic coverage pass.
- Generic unsigned iOS Release build passes in **434.42 seconds**, reusing an
  isolated build cache. This is compile-only, not a clean-from-empty or runtime check.
- Audit tooling: **101 helper tests passed**. Workflow lint passes with only the
  existing custom runner-label warning filtered; the original warning is retained.

[Swap review](SWAP-REVIEW.md) records whole-file and partial reads. Mixed
swap-and-transfer first-screen visibility remains an unconfirmed review lead.
Its related files remain partial; the Polygon fix does not resolve that question.
Live provider settlement, current pool availability and UI rendering were not tested.

The ledger contains **4,681 application files: 236 reviewed, 34 partial,
10 generated-verified, 4,401 outstanding**. Core remains 21 reviewed, 20 partial
and 3,900 outstanding. The completion gate reports **7,617 outstanding items**.
Earlier tests retain their original source pins. Current-target full CI is not
verified: the retained metadata records progress25's run with 10 successful,
five active and 35 queued jobs, and progress26 pending with zero jobs.

The **1,589-file** bundle [evidence/swap-review](../evidence/swap-review) preserves
source/fixture/binary hashes, sanitized logs, actual durations, skips and paired
results. No local Oath/Vault edits, simulator, physical device, production
transaction, App Store upload or submission occurred in this increment.


## Progress 28 — complete router operations before approval

The final source `e46fff5686db48a40103c9dbffe5e830cfc5548a` passes 1,224 networking
host cases with 194 explicit skips, 118 diagnostics cases with two skips, source
and secret checks, diagnostic coverage, and unsigned generic iOS Release build.
The paired approval-model corpus passes all nine process executions after the
repair; the before source retains 30 assertion failures across six executions
and three passing controls. All ten ABI vectors pass the independent pinned
ethers verifier. Audit helper tests: 104 passed.

The initial broader run on `3e553d5` had one failure because a decoder test used
a positional recipient index. The final test selects recipient/source/amount
by labels; both runs remain in the evidence. The SDK vector timeout in older
GitHub run 41282913488 is preserved separately and remains unresolved. No UI
runtime, live contract, physical-device or App Store result is claimed.
See [the finding](../findings/OW-2026-014.md), [source trace](SWAP-APPROVAL-REVIEW.md)
and [durable evidence](../evidence/swap-approval/manifest.json).
