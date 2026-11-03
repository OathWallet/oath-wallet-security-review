# Stellar persistence and refresh — build 104 checkpoint 20

This bounded follow-up reviews the public Oath 5.0.2 (104) prerelease at
`c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`. No application implementation is
changed by this checkpoint. The whole-wallet audit remains incomplete.

## Source review

Seven complete source files were read, and their hashes match the immutable
build-104 inventory. Four previously outstanding files receive partial review
coverage; three existing partial entries gain additional evidence. None is
promoted to fully reviewed.

- `StellarClient.swift`: parallel classic/indexed balance reads, complete-page
  checks, ownership and network binding, the minimum ledger across balance
  sources, exact history windows, bounded retries and cancellation.
- `StellarLedger.swift`: account/run tickets, monotonic inventory commits,
  missing-token zeroing after a complete snapshot, cursor-account binding,
  event replay, fee refunds and metadata reprojection.
- `StellarSynchronizer.swift`: per-account flight coalescing, separate history
  workers, ticket validation, preservation of cached balances on failure,
  bounded price batches and cancellation paths.
- `StellarSend.swift`: sender reservation, exact signed-byte journaling,
  receipt settlement, terminal state checks, expiry, and the history/checkpoint
  predicate used to finish post-send balance refresh.
- `WalletConnectStellarJournal.swift`: request/signature decoding, wallet and
  account checks, duplicate request identity, pending-owner reservations,
  restart loading, and monotonic terminal results.
- `PostSendBalanceRefresh.swift`: durable pending work, target isolation,
  revision-checked completion, bounded queues/flights, retry exhaustion,
  cancellation and resumption.
- `OathPostSendBalanceRefresh.swift`: the application adapter that refreshes
  Stellar accounts and acknowledges only sends accepted by the database's
  freshness predicate. Its other chain branches remain separately scoped.

[Hashes and exact read ranges](../evidence/5.0.2-build104/stellar-persistence/source-binding.json).
The ledger does not treat successful tests as a full manual-review verdict.

## Checks and limits

All 31 selected host methods passed. [Results and source bindings](../evidence/5.0.2-build104/stellar-persistence/manifest.json).

The replay selects 31 existing production-package methods: ten Stellar ledger
methods, six Stellar send-journal methods, two Stellar WalletConnect journal
methods, and thirteen generic post-send worker methods. The single opt-in live
Stellar ledger method is explicitly excluded. Each selected method runs in its
own host test process with runtime network access denied; dependencies may be
fetched during compilation. Each replay creates a fresh pinned checkout and
fresh SwiftPM build directory, and records the executable and source hashes.

These checks cover database reopening, valid saved signatures, tampering,
duplicate imports, cancellation of unsigned work, fee-consuming failure,
proven expiry, split event pages, fee refunds, migrations, reset boundaries,
cache preservation, and generic durable-worker retries and isolation.
The generic worker tests and Stellar tests are separate: their passing does
not establish an end-to-end application/provider/worker run.

The reviewed code requires both transaction-history evidence and a balance
checkpoint at or beyond that history checkpoint before acknowledging a Stellar
refresh. The suspected absence of a transfer event on failed execution is not
reported as a confirmed defect: the decoder deliberately retains fee events
for failed execution, and missing transaction evidence conservatively keeps
work pending. This follow-up does not establish that every real provider emits
all relevant fee events, nor that every cross-provider timing combination is
covered. A synthetic no-history/fresh-inventory end-to-end case and provider
consistency checks remain open.

No new vulnerability or application fix is claimed. No new generic iOS build
is claimed for this audit-only change; checkpoint 19 already records the
unsigned Release build of the identical application tree. No simulator,
physical device, live transaction or App Store operation is included.

## Reproduction

Use a clean public application checkout at the pinned commit and the toolchain
specified by the dedicated workflow:

```sh
python3 scripts/stellar-persistence-regressions.py /path/to/wallet /tmp/stellar-persistence /tmp/stellar-persistence-results --expected-commit c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
```

The workflow pins actions and tool versions, uses read-only permissions, has
no deployment secrets, and does not execute outside pull-request code on the
dedicated runner. Local and GitHub results are recorded separately.

All 399 audit evidence/helper tests pass. The publication scan of changed files
and expanded new archives reports no leaks; it is not a full Git-history scan.
The completion gate still reports 16,917 unfinished review/validation items
(not vulnerabilities), so no completion verdict is issued.

## Earlier repair replay

The [XDR/SCALE hosted replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41736609601)
completed successfully. Its downloaded artifact matches GitHub's SHA-256
digest. All recorded report/log hashes and source pins were checked. It
reproduces three passing controls and six SIGTRAPs before the repair, then
nine passing repaired methods and 40 passing adjacent methods. Original
checkpoint 18 results remain unchanged.

[Hosted receipt and verification](../evidence/5.0.2-build104/hosted-xdr-scale/verification.json).

## Remaining scope

Complete hostile-provider semantics, every Stellar operation, full application
integration and authorization interleavings, dependency review and
source-to-binary provenance remain open. This is a maintainer-commissioned,
Codex-led review, not independent certification or a guarantee of zero bugs.
