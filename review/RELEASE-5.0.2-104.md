# Oath Wallet 5.0.2 (104) — active prerelease audit

Build 104 checkpoint 24 retests the existing backup file-boundary repairs against current source: three historical failing methods become three passes. A separate pristine backup package passes 64 XCTest methods plus one Swift Testing reset-barrier test. Two source files gain partial dispositions and the package manifest gains a scoped reviewed disposition. No new app change is claimed; the whole-wallet audit remains incomplete. [Evidence and remaining scope](CLOUD-FILE-RECHECK.md).

Build 104 checkpoint 23 adds twelve passing Stellar provider/contract and WalletConnect methods, with 20 malformed-state cases and 12 malformed simulations. A disposable authorization mutation causes the expected assertion failure. One additional file gains partial source review; no new app defect or change is claimed. Earlier decoding and multisignature GitHub replays are downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](STELLAR-PROVIDER.md).

Build 104 checkpoint 22 adds ten passing Stellar multisignature methods, covering all 209 supported threshold combinations and SDK-decoded atomic setup. A disposable threshold mutation produces 627 expected assertion failures. Three files gain partial source review; no new defect or app change is claimed. Timestamp repair and persistence GitHub replays are downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](STELLAR-MULTISIG.md).

Build 104 checkpoint 21 adds seven passing production-parser methods backed by deterministic independent Stellar vectors and 1,776 truncation cases. A disposable checksum mutation produces 64 expected assertion failures. Two files gain partial source review; no new app defect or implementation change is claimed. The whole-wallet audit remains incomplete. [Evidence and remaining scope](STELLAR-DECODING.md).

Build 104 checkpoint 20 adds 31 passing offline Stellar persistence and generic refresh-worker methods, including database reopening, signature preservation, duplicate-wallet isolation and retries. Seven files have hash-bound partial read evidence; four were previously outstanding. No application implementation changes or new confirmed defect are claimed. The earlier XDR/SCALE hosted replay is downloaded and hash-verified. The whole-wallet audit remains incomplete. [Evidence and remaining scope](STELLAR-PERSISTENCE.md).

The current target is `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`,
[tag v5.0.2-build104](https://github.com/devdasx/oath-wallet/releases/tag/v5.0.2-build104).
It includes the public repairs merged through PR #77. It is a GitHub prerelease;
no upload, submission, withdrawal or other App Store Connect action is included.
The separate 5.0.1 (103) submission is unchanged.

## Continuity of evidence

The earlier [build-103 series](RELEASE-5.0.1-103.md) and its release assets remain
historical evidence. Before/after failures, source pins, tags and checksums have
not been changed to pretend they tested a later version. Earlier report pages
and release descriptions point to this current target.

The target transition compares file hashes: 1,158 identical file dispositions
carry their original scoped evidence forward; 36 changed files are reopened
for review. Their old dispositions remain archived. New and otherwise unreviewed
files remain outstanding. Dependency and network-entry inventories are regenerated.
Existing compiler-input traces remain pinned to the builds that produced them;
a fresh build-104 trace is separate. Fix ancestry is recorded per finding and
is not treated as a test result.

[Transition details](../evidence/5.0.2-build104/target-transition.json) ·
[Current source inventory](../scope/inventory.json) ·
[Archived build-103 inventory](../scope/history/5.0.1-build103/inventory.json).

## Review status

The whole-wallet review remains incomplete. All unresolved findings, coverage,
dependency provenance and runtime limitations remain explicit. Passing new
release checks does not certify zero vulnerabilities or equivalence with an
Apple-distributed binary. Tests below describe only the checks actually run.

## New exact-target validation

On `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`:

- Database: 748 passed, 72 explicit skips, zero failures.
- Diagnostics: 119 passed, two explicit skips, zero failures.
- Public-source/secret checks and diagnostic coverage passed.
- Generic unsigned iOS Release build passed; the built Info.plist reports
  version 5.0.2 and build 104. An existing isolated build cache was reused.
- Compiler trace: 2,358 non-toolchain inputs and 47 compilation units. Its
  source hashes are bound to this build. This is not full symbol reachability.
- Audit helpers: 319 passed. Three initial helper failures exposed historical
  assertions using the current inventory; they now read the archived build-103
  inventory. Original failures remain in the evidence.

[Validation and logs](../evidence/5.0.2-build104/validation/manifest.json) ·
[Compiled inputs](../evidence/5.0.2-build104/compiler/release-inputs.json) ·
[Compiled-input dispositions](../evidence/5.0.2-build104/compiler/dispositions.json).

The compiler ledger has 227 reviewed, 136 partially reviewed, 1,515 outstanding,
460 generated-and-verified and 20 generated inputs needing trace. These reflect
exact hash matches and reopened changed files, not a completed audit.

The four additional partial entries are the [chain wallet adapters](CHAIN-WALLET-ADAPTERS.md).
[Coverage reconciliation](COMPILER-DISPOSITION-RECONCILIATION.md) preserves 16
previously documented partial compiler dispositions in the canonical inventory.
Three further partial entries cover [NEAR provider and request boundaries](NEAR-PROVIDER-BOUNDARIES.md),
with 24 existing production-package methods passing under runtime network denial.

## Checkpoint 2 — later public repair

The immutable tag above remains the baseline. PR81 merges tested repair
`0614556b993f85808b13e3a69984ce36050a8dfe` as
`501915920e99475e63af5fcb9e658f3c834f3cc8`. Local focused and broader tests pass;
hosted replay was subsequently verified in checkpoint 5. [Exact results, attempts and scope](CONNECT-REMOVAL-READ.md).
No historical source pin or test result has been rewritten. The current inventory
continues to describe the baseline; later-source coverage is explicitly linked
by source hashes in this checkpoint.

## Checkpoint 4 — NEAR journals and hosted receipts

Eight existing production database methods pass at `0614556b993f85808b13e3a69984ce36050a8dfe`, with network access denied during discovery and execution. Four additional files have partial source dispositions; no new application defect is confirmed. [Read scope, replay and remaining gaps](NEAR-JOURNAL-BOUNDARIES.md).

[GitHub run 41603474540](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41603474540) passed the earlier 24 NEAR provider/request methods at that same application commit. The downloaded archive digest, every receipt file and case-log hash, method identities and executed driver hash were verified. [Durable evidence](../evidence/5.0.2-build104/hosted-near-provider/manifest.json).

The separate [unsigned Release build job](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41601227473/job/125800183599) passed at merge `501915920e99475e63af5fcb9e658f3c834f3cc8` in 990.49 seconds. Its archive and build-log hashes are verified. [Durable evidence](../evidence/5.0.2-build104/hosted-removal-build/manifest.json). The other job in that workflow is not implied to pass by the build result. No simulator, device or App Store operation occurred.


## Checkpoint 5 — NEAR vectors, reader repair and completed hosted replays

[OW-2026-065](../findings/OW-2026-065.md) repairs a confirmed Data-slice parser
trap. The same audit fixture changes from four passes and one SIGTRAP to five
passes. Seventy-two transfer plans and ten classic-action vectors match a locked
independent SDK, and Node crypto verifies 82 application signatures. Twenty-six
adjacent package methods, 119 diagnostics tests (two skips), public-source/secret
checks, diagnostic coverage and unsigned generic iOS Release compilation pass.
[Read scope and reproduction](NEAR-SIGNING-VECTORS.md) · [Evidence](../evidence/5.0.2-build104/near-signing/manifest.json).
Three new source dispositions remain partial; no full-review verdict is issued.

[Run 41601227473](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41601227473)
completed successfully. Its signing account-read fixtures reproduce 12 failures
before and all 66 checks pass after; pending consent reproduces one failure
before and all 14 checks pass after. Archive, driver, fixture and case-log hashes
are verified. [Durable receipts](../evidence/5.0.2-build104/hosted-removal-read/manifest.json).
The earlier unsigned-build receipt remains intact.

[Run 41605014923](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41605014923)
completed all eight NEAR journal/removal methods successfully, with downloaded
archive, receipt and log hashes verified. [Durable receipts](../evidence/5.0.2-build104/hosted-near-journal/manifest.json).
The new NEAR reader/signing-vector workflow is a separate pending replay.
No Apple submission or physical-device operation occurred.

## Checkpoint 6 — NEAR multisig boundaries and artifact provenance

Ten existing production-package multisig methods pass on the host with runtime
network access denied. The bundled WASM, Rust source and two licenses match
the pinned upstream commit byte-for-byte. This is not a verified Rust-to-WASM
rebuild. The upstream contract test attempt failed during dependency compilation;
original failure logs are preserved and no contract runtime pass is claimed.
Two application files have partial dispositions. The newly inventoried upstream
files and lock dependencies retain explicit gaps. [Read scope and reproducible
commands](NEAR-MULTISIG-BOUNDARIES.md). No app code, App Store submission, simulator
or physical-device operation changed.

## Checkpoint 7 — Independent multisig signing vectors

Fifty SDK-generated bundles contain 188 transaction parts. Three host methods
pass; Node independently verifies all app signatures, and five corrupted-output
controls are rejected. An isolated nonce mutation causes 90 failed assertions
in one method. The initial fixture's signature-byte assumption and correction
remain in the evidence. No new production defect is claimed.

GitHub run 41607922685 reproduced the prior parser failure and repair plus
26 adjacent regressions; downloaded hashes, method identities and signatures
were verified. [Reproduction, preserved failures and remaining review](NEAR-MULTISIG-VECTORS.md).
No app, App Store, simulator or physical-device changes occurred.

## Checkpoint 8 — Native contract evidence and hosted multisig replay

The adapted native contract harness records nine passing methods, five SDK
abort blockers and one invalid inherited fixture pass. Four new checks inspect
actual mock receipts and characterize retained confirmations after a legitimate
quorum changes membership. No shipped-WASM or full-contract-suite pass is claimed.
The original failure logs, pruned graph and intermediate attempts are retained.
GitHub run 41609444047 independently passed ten app multisig methods and four
upstream-copy checks; its downloaded artifact and case logs are verified.
[Native evidence, reproduction and remaining scope](NEAR-CONTRACT-NATIVE.md).
No application, device, simulator or App Store changes occurred.

## Checkpoint 9 — Native mock rejection repair

The identical 20-method source fixture records nine valid passes, ten SDK abort
blockers and one invalid inherited fixture pass before; eighteen valid passes
and two invalid inherited fixture passes after. The repair changes only the
native SDK mock panic ABI and its declaration. Two misleading inherited tests
remain excluded, with correctly targeted companion rejection tests added.
A one-line member-admission mutation causes exactly four failures.
The independent signing-vector GitHub run 41611022824 and its five verifier
controls passed; downloaded hashes are verified. The native workflow's first
compiler-version failure is retained and explicit toolchain installation added.
[Reproduction and limits](NEAR-CONTRACT-REJECTIONS.md). Shipped-WASM execution,
source-to-binary reproduction and whole-wallet coverage remain unverified.
No application or App Store operation changed.

## Checkpoint 10 — Staged multisig submission

Six new host methods pass against unchanged production client/signing/receipt
code with synthetic providers and runtime networking denied. They cover cold
client reconstruction, per-part failures, request binding, nonce-based expiry,
late cancellation and concurrent identical-byte retries. Removing only the
request-payload equality guard in a scratch copy causes the expected one method
to fail, while five controls pass. Hosted run 41615849636 now reproduces the
preceding paired native-contract results; downloaded hashes are verified.
[Reproduction and limitations](NEAR-MULTISIG-LIFECYCLE.md). No full app/database
restart, shipped-WASM, physical-device or App Store operation is claimed.

## Checkpoint 11 — Activation and bootstrap authority

Six production-package host methods pass with synthetic providers and runtime
networking denied. Wrong bootstrap keys, altered permissions, duplicate keys,
exhausted nonces, stale plans and late cancellation are rejected. Deployment and
bootstrap removal remain separate stages, with original signatures reconciled
after JSON reconstruction. Removing the initial bootstrap-key equality check in
a scratch copy causes exactly one method to fail; five controls pass.
Two complete application-file source reads receive partial dispositions, not
full integration or UI coverage. [Reproduction and limits](NEAR-MULTISIG-ACTIVATION.md).
The previous lifecycle GitHub replay had started when this evidence was
prepared; its outcome is not claimed here. All 366 audit-helper tests pass. No application code, App Store,
simulator or physical-device operation changed.

## Checkpoint 12 — Journal reservation races and terminal integrity

Nine production database methods pass, including three new methods for
concurrent duplicate-wallet reservation, late terminal acknowledgements after
database reopen, and malformed-receipt rollback. Synthetic signatures and actual
SQLite code run with runtime networking denied. Two production files gain partial
source review; the existing six-method fixture is reviewed as test code.
[Reproduction and limits](NEAR-JOURNAL-RACES.md). Full service/model integration,
authentication and process-interruption coverage remain open. This checkpoint
does not change application source or involve an App Store operation.
The deliberate sender-reservation bypass produces exactly three expected
failed methods and six passing controls. All 368 audit-helper tests pass.
Earlier hosted lifecycle/activation checks remain running/queued at preparation;
no final result is inferred.

## Checkpoint 13 — Preserve retries until NEAR assets are current

[OW-2026-066](../findings/OW-2026-066.md) is repaired in [PR83](https://github.com/devdasx/oath-wallet/pull/83).
The same six synthetic production SQLite/signing methods change from two passes
and four failures to all passing. All 24 adjacent database methods pass with
runtime networking denied. Diagnostics record 119 passes and two explicit skips;
source validation, secret scanning and unsigned generic iOS Release compilation
pass. All 371 audit-helper tests pass. Four more source files receive scoped
partial dispositions, with other chains and full application integration still
open. [Reproduction and limitations](NEAR-BALANCE-FRESHNESS.md).

The previous lifecycle workflow 41617104807 is now complete, with downloaded
source/driver/fixture/log hashes verified: six control passes, one expected
mutation failure and five passing mutation controls. The new freshness workflow
is tracked separately; no hosted pass is inferred from local results. No
App Store operation occurred, and the original build-104 tag remains unchanged.


## Checkpoint 14 — TRON and TON ledger boundaries

Four complete source reads receive scoped partial dispositions. All 27 selected
existing offline ledger and send-journal methods pass after incremental native
host compilation at `fd06fdff104d128e00cc414d2de1472f11752e04`. Each test process
has networking denied; two live-provider methods are explicitly excluded.
All 373 audit-helper tests pass. [Exact reproduction and remaining gaps](TRON-TON-LEDGER-BOUNDARIES.md).
No new confirmed defect or application patch is claimed. Source review and
these tests do not prove every overlapping refresh schedule or provider snapshot
freshness. Generic iOS compilation is not repeated for this audit-only change;
the earlier build result retains its own source pin.

The prior activation/bootstrap workflow 41618881396 is now downloaded and
verified against GitHub's artifact digest and all 27 archived file hashes:
six control methods pass, with one expected mutation failure and five passing
mutation controls. Its original source and runtime limits remain unchanged.
The ledger still contains 16,917 outstanding review items, including partially
reviewed files. The new hosted TRON/TON replay is tracked separately. No App
Store, simulator or physical-device operation occurred.

## Checkpoint 15 — delayed inventory freshness

[OW-2026-067](../findings/OW-2026-067.md) repairs late TRON/TON responses that
were incorrectly classified as current balances. The original five-method
fixture produces two passes and three failures; the repair passes all five.
The final journal records are synthetic fixtures, not a complete send flow.
[Reproduction and validation](INVENTORY-FLIGHT-TIME.md). The earlier nine-case
NEAR journal-race replay is now downloaded and verified, including three
expected failures in its deliberately broken reservation variant.

The original build-104 tag, earlier source pins and unresolved review areas
remain unchanged. No App Store operation is included.

## Checkpoint 16 — history restart arithmetic and account binding

[OW-2026-068](../findings/OW-2026-068.md) rejects an overflowing Sui history
checkpoint without crashing or changing saved cursor state. [OW-2026-069](../findings/OW-2026-069.md)
binds Sui/XRP restarts to the ticket's account. The original four-method fixture
has one passing control, two failed assertions and one SIGTRAP; all four pass
after repair. All 22 adjacent offline methods pass; two live tests remain excluded.
[Reproduction and validation limits](HISTORY-RESTART-BOUNDARIES.md).

NEAR balance freshness and delayed TRON/TON freshness now have verified hosted
receipts, retaining their original source pins and before/after failures.
The whole-wallet review remains incomplete; this checkpoint does not promote
unreviewed files. No App Store operation is included.

## Checkpoint 17 — Sui signing and transaction buffers

Build 104 checkpoint 17 repairs a Sui transaction-parser crash on nonzero-origin Data. The identical fixture changes from one passing control/two SIGTRAPs to three passes. All 34 signing and WalletConnect methods pass, including 336 independent hash vectors; diagnostics and generic unsigned iOS Release compilation also pass. This is parser API robustness, not a demonstrated remote app exploit. [Exact source pins, reproduction and limits](SUI-SIGNING-BOUNDARIES.md). The full audit remains incomplete; no App Store operation.

## Checkpoint 18

Build 104 checkpoint 18 repairs nonzero-origin buffer crashes in the Stellar XDR and Polkadot SCALE readers. The identical nine-method fixture changes from three passes/six SIGTRAPs to nine passes; 40 adjacent send and WalletConnect methods pass. Diagnostics and generic unsigned iOS Release compilation pass. Public API/internal parser robustness is demonstrated, not a remote exploit. The full audit remains incomplete. [Exact pins, reproduction and limits](XDR-SCALE-BUFFERS.md).

## Checkpoint 19

Build 104 checkpoint 19 fixes malformed Stellar plan timestamps that could crash structural validation during saved-send verification. Fresh before/after builds reproduce three crashes and then six passing methods; 40 adjacent methods pass. Valid saved transactions retain their bytes and signatures. Earlier Sui/XRP history and Sui signing GitHub replays are downloaded and hash-verified. The full audit remains incomplete. [Exact pins, reproduction and limits](STELLAR-PLAN-TIMESTAMPS.md).
