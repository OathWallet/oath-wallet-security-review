# Acceptance checklist — in progress

Current supplemental checkpoint: **5.0.3 (105)**, typed-data consent review at
`32701474fefbed3840878e35f6111e8d494e1f02`. The [checkpoint 32 evidence](TYPED-CONSENT.md)
covers its explicit source ranges and host corpus; it does not requalify the
entire application. The earlier nonce-response repair at
`6a8bfcfcf6aeabdd858c9f3316ff4bdaeaf245a1`, merged as
`658245d197592c89c071a946fda0baf8bf93fb41` in PR #105, retains its separate
[paired regressions and builds](SOLANA-NONCE-VALUE.md).

The completion gate still reads the frozen **5.0.2 (104)** inventory at
`0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d` from [scope](../scope/source.json).
Later fixes and evidence retain their exact commit identities. Earlier results
below are historical and are not retroactively results of build 105.

Historical 5.0.1 (103) target: `c7acd23bb139864a40273f405d18b479589d2b20`.
[Version-specific findings and exact-target checks](RELEASE-5.0.1-103.md).

Checkpoint 9 retains 16,599 open ledger items, including 1,526 outstanding direct compiler inputs and 111 partial inputs. The completed baseline workflow failed five jobs; 104 of 115 required checks have passing exact-baseline records across the evidence ledger. Later source fixes and test-harness repairs have separate commit-specific receipts. The whole-wallet acceptance criteria remain unmet.

Checkpoint 10 reduces the combined gate to 16,595 open items: direct compiler inputs now include 244 reviewed, 118 partial, 1,515 outstanding, 460 generated-and-verified and 20 generated inputs needing trace. The new source reads and limited synthetic runtime result do not change the full-review acceptance status.

Checkpoint 11 records 105 of 116 passing required exact-baseline checks and 250 passing audit helper tests. Direct compiler inputs include 244 reviewed, 120 partial and 1,513 outstanding; generated counts and the 16,595 combined open-item count remain unchanged. Private-key snapshot behavior and the application export adapter runtime coverage remain open. [Private-key evidence limits](PRIVATE-KEY-DISCLOSURE.md).

Checkpoint 12 resolves the specific retained-key snapshot hypothesis as OW-2026-058 and publishes its tested source repair. The historical baseline still contains that defect; fixes after the reviewed commit remain separate in the gate. Runtime evidence uses one synthetic production-component fixture, not a complete export UI or every OS. No existing outstanding source/dependency entry is promoted merely because this test passed. The whole-wallet review remains in progress.

Checkpoint 14 verifies two hosted before/after repair replays and adds 22 passing local restore-model cases with a three-failure mutation control. Four further partial dispositions leave 244 reviewed, 128 partial and 1,505 outstanding direct inputs, with generated counts unchanged. The gate remains at 16,597 open items. 273 audit-helper tests pass; live cloud, full restore persistence and UI coverage remain open. [Restore review](CLOUD-RESTORE-LIFECYCLE.md).

Checkpoint 13 records OW-2026-059's tested source repair and fifteen controlled model cases (three expected failures before, none after). Four new partial dispositions leave 244 reviewed, 124 partial and 1,509 outstanding direct inputs, with generated counts unchanged. The gate retains 16,597 open items, and 266 audit-helper checks pass. Model tests do not complete UIKit, live-cloud or cryptographic coverage. [Backup review](BACKUP-PRESENTATION.md).

Checkpoint 15 adds the verified public-source repair OW-2026-060 and 4,900 paired arithmetic cases. Four partial dispositions leave 244 reviewed, 132 partial and 1,501 outstanding direct compiler inputs; generated counts are unchanged. The combined gate retains 16,598 entries. The complete signing/serialization paths, dependency provenance and full-wallet coverage remain open. [XRP arithmetic scope](XRPL-AMOUNT-ARITHMETIC.md).

Checkpoint 16 adds 61 independent signed-transaction vectors, 13 RIPEMD vectors and negative signature/plan tests. Five more partial file dispositions leave 244 reviewed, 135 partial and 1,498 outstanding direct inputs. Generated counts and the 16,598-entry completion gate are unchanged. Provider-response hypotheses and all full-review acceptance gaps remain open. [Signing matrix](XRPL-SIGNING-MATRIX.md).

## Historical acceptance snapshot

Original 4.1.15 (100) baseline `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. Reviewed app `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`.

The Electrum two-factor repair restored both independently calculated Bitcoin addresses, and the encrypted-wallet run passed 205 checks. Full package runs passed 305 Bitcoin and 708 database cases, with 60 and 71 explicit skips respectively. Unsigned iOS Release compilation passed. Three isolated Bitcoin Cash Node chains confirmed 20 ordinary spends and 121 threshold-policy spends. The node rejected modified signatures, changed payments and spends missing a required multisignature. The CashTokens prefix reader matched all 22,960 expected outcomes.

Two additional planner issues were reproduced at this source and repaired afterward in [PR 53](https://github.com/devdasx/oath-wallet/pull/53). The identical named tests passed on that later source. At the reviewed source, two protected-startup assertions missed expected asynchronous diagnostics (25 of 27 assertions passed). This failed run is included in the validation evidence. OW-2026-002 remains open for historical archive provenance.

28 passing check records target this revision. 87 required checks lack a passing exact-revision record. There are 17,124 open entries across the inventories, findings and validation ledger. The combined source and App Store binary equivalence have separate evidence requirements. [Manifest](../evidence/two-factor-and-bch/manifest.json).

Checkpoint 12 audit-helper validation: **262 tests passed**. The combined gate
retains **16,596 open items**; the extra finding remains counted against the
unchanged historical baseline despite its later public repair. Direct compiler
coverage counts are unchanged. These counts are not counts of vulnerabilities.

Checkpoint 17: OW-2026-061 has a verified later-source repair and paired replay.
The unchanged baseline keeps it counted in the gate: **16,599 open entries**.
Direct compiler coverage remains 244 reviewed, 135 partial, 1,498 outstanding,
460 generated-and-verified and 20 needing trace. These are coverage/validation
entries, not vulnerability counts. No App Store availability claim is made.

Checkpoint 18: byte-identical XRP codec reproduction closes its generated-asset
trace. Adding its previously unenumerated upstream closure increases the combined
gate to **16,768 open entries**. The 170 upstream input files remain outstanding.
Direct compiler inputs: 244 reviewed, 137 partial, 1,496 outstanding,
460 generated-and-verified and 20 needing trace. JavaScript assets are outside
that direct Swift/C compiler trace. No overall completion claim is made.

Checkpoint 20 adds 38 passing production-vault/EVM imported-key host checks and
a two-failure deliberate stale-envelope control. Three partial file dispositions
leave 244 reviewed, 140 partial, 1,493 outstanding direct compiler inputs; generated
counts are unchanged. The combined gate remains 16,769 open entries. Signing-to-
journal/removal atomicity and the full review remain incomplete.

Checkpoint 21 confirms OW-2026-063 and repairs it in later public source. The
historical baseline remains unchanged; the combined gate now reports **16,770
open coverage/validation entries**, not 16,770 vulnerabilities. Direct compiler
coverage counts remain unchanged. The controlled journal/removal overlap is
repaired; other asynchronous signing and full integration paths remain open.

## Frozen inventory target: 5.0.2 (104)

The target is `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`. Six checks now have
passing exact-target records, including generic iOS compilation and compiler
input tracing. The combined completion gate reports **16,908 open entries**.
Earlier tests are not counted as new-revision passes. File-hash changes reopen
review coverage; unchanged bytes retain their original scoped evidence.
No whole-review completion or App Store operation is claimed.

Build 104 checkpoint 2 fixes OW-2026-064 in later public source. The baseline
source pin and all previous gaps remain explicit. 80 focused and 616 broader
host assertions pass; 330 audit helper tests pass after repairing the historical
count assumption. The completion gate retains 16,908 outstanding review items.
This is not a count of vulnerabilities or a completion verdict.
[Repair and scope](CONNECT-REMOVAL-READ.md).

Build 104 checkpoint 8 leaves **16,918 outstanding review/validation entries**.
The adapted native contract replay records nine passes, five SDK abort blockers
and one invalid inherited fixture pass; it does not establish shipped-WASM
execution or a complete contract review. The earlier ten-method hosted app replay
is now downloaded and verified. 358 audit-helper tests pass. Existing reviewed
and partial dispositions remain scoped to their original evidence; no outstanding
implementation is promoted by test success. [Contract scope and open questions](NEAR-CONTRACT-NATIVE.md).

Build 104 checkpoint 9 leaves **16,918 outstanding review/validation entries**.
The identical native fixture now has 18 valid passes and two excluded inherited
fixture passes after an audit-only SDK mock ABI repair; ten original aborts are
retained. A deliberate member-admission mutation causes exactly four failures.
362 audit-helper tests pass. Hosted signing vectors and the pinned-toolchain
native replay have downloaded, hash-verified evidence. No implementation review
is promoted by those results; shipped-WASM execution, source-to-binary rebuild
and remaining dependency review stay open. [Repair and limitations](NEAR-CONTRACT-REJECTIONS.md).

Build 104 checkpoint 10 adds six passing production-package lifecycle methods
and one expected failed-method mutation control. The paired native-contract
hosted replay is now verified. The gate retains 16,918 open entries: these tests
do not promote source coverage or establish full database restart, shipped-WASM
execution or dependency review. [Exact scope](NEAR-MULTISIG-LIFECYCLE.md).

Build 104 checkpoint 11 adds six passing activation methods and one expected
failed-method mutation control. Two source files move from outstanding to
partially reviewed; the gate retains **16,918 outstanding review/validation
entries**. Full service/model/database integration, shipped-WASM reproduction
and the remaining implementations stay open. [Exact scope](NEAR-MULTISIG-ACTIVATION.md).
The 366 audit-helper tests pass. The prior lifecycle workflow is in progress;
no final hosted activation or lifecycle result is claimed in this checkpoint.

Build 104 checkpoint 12 adds nine passing database journal methods. One existing
test file receives a reviewed test-code disposition, while the two production
files remain partial. The gate has **16,917 outstanding review/validation entries**.
The tests do not close all crash recovery, full app integration, authentication,
contract execution or dependency provenance. [Scope](NEAR-JOURNAL-RACES.md).
The scratch sender-reservation mutation is detected by three methods, while six
controls pass. All 368 audit-helper tests pass. The original application checkout
is unchanged, and earlier hosted jobs remain separately tracked.

Build 104 checkpoint 15 repairs OW-2026-067 on a later public source revision.
The controlled host tests do not close the full adapter/worker integration or
live-provider freshness gaps. No complete file-review dispositions are added
by test success. [Evidence](INVENTORY-FLIGHT-TIME.md).

## Checkpoint 27: Solana delegation consent

OW-2026-073 has paired host evidence against released build 104 and repaired
5.0.3 (105) source. This is an additive, scoped review; the frozen inventory and
whole-wallet completion requirements remain unchanged. See [results and gaps](SOLANA-CONSENT.md).

## Checkpoint 28: Solana buffer origins

OW-2026-074 is fixed through PR #97 and retested at the exact repair. The merged
source tree is identical. The frozen inventory remains unchanged; three
source/test entries receive scoped hash-bound dispositions in the supplemental
ledger. The five paired cases and 41 passing Solana methods do not establish
whole-wallet coverage, ordinary dApp exploitability, UI runtime correctness or
App Store delivery. Hosted replay succeeded and its downloaded artifact is hash-verified. [Evidence](SOLANA-BUFFER-ORIGIN.md).

## Checkpoint 29: Solana RPC response contexts

OW-2026-075 is repaired through PR #100. The merged application inputs match
the tested repair; only separate website changes differ. Eleven paired methods
and 52 passing Solana cases do not establish provider honesty, full pending-
journal runtime coverage, all instruction semantics or whole-wallet completion.
The frozen inventory is unchanged; the supplemental source ledger remains scoped.
Hosted replay succeeded and its downloaded artifact is hash-verified. [Evidence](SOLANA-RPC-CONTEXT.md).


## Checkpoint 30: Solana nonce-response presence

Checkpoint 30 records the missing Solana nonce-response value repair in [PR #105](https://github.com/OathWallet/oath-wallet/pull/105). Four controls pass and two methods fail before repair; all 58 selected Solana methods pass afterward with networking denied. Diagnostics, publication checks and separate unsigned iOS Release builds at the repair and merge commits pass. Hosted replay succeeded and its downloaded artifact is hash-verified. These are scoped results; the whole-wallet audit remains incomplete. [Scoped evidence](SOLANA-NONCE-VALUE.md).

Checkpoint 31 adds 25 passing Aptos host methods and an expected failed-method
mutation control at `32701474fefbed3840878e35f6111e8d494e1f02`. Eight supplemental
source dispositions remain partial. No app defect, app change, new generic iOS
build or whole-review completion is claimed. The frozen inventory remains
unchanged. Hosted replay succeeded and its downloaded artifact is hash-verified.
[Exact scope and limitations](APTOS-INTENT.md).

## Checkpoint 32: typed-data signing and consent

At `32701474fefbed3840878e35f6111e8d494e1f02`, 20 production host methods pass
with no skips. They include 616 independent encoding/signature vectors and 192
invalid-value rejections. A separate domain-binding mutation produces exactly the
expected four assertions in one failed method. Nine source dispositions remain
partial; the frozen inventory is unchanged. No new app defect, app change, new
generic iOS build or whole-review completion is claimed. Full application
authentication, rendered consent and dependency provenance remain separate gaps.
[Exact scope and limitations](TYPED-CONSENT.md).
