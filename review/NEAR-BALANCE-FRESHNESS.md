# NEAR post-send balance freshness

Build 104 checkpoint 13. [OW-2026-066](../findings/OW-2026-066.md) records a
confirmed refresh-completion defect and a narrowly scoped database predicate
repair. The immutable build-104 source inventory is not rewritten to claim
that later fixes were present in the original tag.

## Paired reproduction

Before source: `5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`.
After source: `fd06fdff104d128e00cc414d2de1472f11752e04`.
Both are public application commits. Six identical production-source methods
give **two passes/four failures before**, and **six passes afterward**.

The fixtures cover a failed token read with retained old units/timestamp, a new
wall-clock observation at a pre-execution block, a valid observation at the
execution block, a genuine zero token balance, the equivalent native-send block
boundary, and recovery after database reopen plus a new successful read.
Production inventory/history/journal implementations and real signatures run
against temporary SQLite files and public synthetic test keys.

The application refresh adapter calls the tested predicate before accepting a
send as current; the durable worker completes only accepted IDs. These caller
relationships are source-traced. The new tests directly exercise the predicate
and persistence, not the entire application/worker/provider combination.

Use macOS with Swift 6.4 and Python 3.11 or newer. Dependency resolution may
download public packages during compilation; test processes have networking
denied. Start from clean checkouts and fresh scratch/output paths:

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach 5d91d1e4dfd36c56031c7a8fb1ee305446dc54de
python3 scripts/near-balance-freshness.py wallet scratch/before evidence/local/before --baseline --expected-commit 5d91d1e4dfd36c56031c7a8fb1ee305446dc54de
git -C wallet checkout --detach fd06fdff104d128e00cc414d2de1472f11752e04
python3 scripts/near-balance-freshness.py wallet scratch/after evidence/local/after --expected-commit fd06fdff104d128e00cc414d2de1472f11752e04
python3 scripts/near-balance-adjacent.py scratch/after/source scratch/after/build evidence/local/adjacent --expected-commit fd06fdff104d128e00cc414d2de1472f11752e04
```

## Local validation

All 24 adjacent offline ledger/journal/refresh methods pass. The live-provider
method is explicitly excluded. Diagnostics record 119 passes and two skips
(the optional live case and a shared one-time reporter setup case). Public-source
validation, diagnostics coverage, secret scanning and generic unsigned iOS
Release compilation pass. All 371 audit-helper tests pass.
[Raw logs, exact hashes and outcomes](../evidence/5.0.2-build104/near-balance-freshness/manifest.json).
The fix is published in [PR83](https://github.com/devdasx/oath-wallet/pull/83).

## Earlier hosted results

The preceding [staged multisig workflow](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41617104807)
completed successfully. Its downloaded artifact, file and log hashes, exact
source/fixture/driver pins, six passing control methods and one expected
mutation failure were verified. The other five mutation controls passed.
[Receipt](../evidence/5.0.2-build104/hosted-near-multisig-lifecycle/manifest.json).
This supersedes that workflow's earlier pending status, not its original
source version or integration limits.

## Remaining limits

Four complete source-file reads receive **partial** dispositions: NEAR inventory
commits and synchronizer, the durable refresh worker, and its application
adapter. Their hashes match the original build-104 baseline; exact paths and
read ranges are in the [source binding](../evidence/5.0.2-build104/near-balance-freshness/source-binding.json).
Generation checks reject stale inventory tickets, per-holding failures preserve
last-known balances, and the worker intersects accepted IDs with its selected
batch while matching stored revisions. Those controls are not a proof of all
concurrency schedules. Other chains' balance-current predicates still need
separate scrutiny; the NEAR repair must not be generalized as their validation.

No live NEAR provider, funded send, SwiftUI presentation, simulator, physical
device or App Store execution was performed. The source-to-WASM provenance gap,
historical aezeed provenance finding, remaining dependency/source inventory and
unresolved app integration areas stay open. Neither this repair nor the passing
tests completes the whole-wallet review. Hosted reproduction of this new repair
is tracked separately from local results.

## Subsequent hosted verification

Run [41622627422](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41622627422) completed successfully. Its downloaded archive, source pins, fixture and case logs were verified against GitHub metadata. [Durable receipt](../evidence/5.0.2-build104/hosted-near-balance-freshness/manifest.json). The original local checkpoint manifest retains its publication-time status.
