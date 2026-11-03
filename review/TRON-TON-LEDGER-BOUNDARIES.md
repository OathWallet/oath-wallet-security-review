# TRON and TON ledger refresh boundaries

Build 104 checkpoint 14. Reviewed source: `fd06fdff104d128e00cc414d2de1472f11752e04`.
This checkpoint does not change the application. It does not generalize the
NEAR freshness repair to other chains or complete the whole-wallet review.

## Source trace

The complete TRON and TON ledger and synchronizer files were read. All four
are byte-identical to the original build-104 inventory and receive **partial**
review dispositions. [Exact hashes and read ranges](../evidence/5.0.2-build104/tron-ton-ledger/source-binding.json).

Both inventory writers validate account identity and the active synchronization
ticket inside the database write. A response from an older run cannot commit
through that ticket. They retain token values after individual failures or
incomplete discovery and store `partialInventory` as the account failure. A
successful complete discovery may set a disappeared token balance to zero.
TRON separately permits this for TRC10 balances from its account response.
Token metadata with conflicting decimal precision is rejected transactionally.

The synchronizers coalesce concurrent refresh callers onto the same account
flight. Inventory and history are separate tasks. An incomplete inventory
throws after its partial cache update, and the wrapper propagates that error.
The application's post-send adapter awaits that refresh before checking the
balance predicate. Unlike the NEAR failure reproduced in OW-2026-066, a partial
inventory does not ordinarily return success to that adapter. This conclusion
is a source trace; the existing ledger tests are not an end-to-end adapter test.

TRON history validates current tickets before reducing provider errors to
stored failures. Both ledgers compare the exact stored history cursor before
advancing it. The TRON writer replaces prior tentative events; the TON writer
preserves the native fee/failure across native and token streams and replaces
local intent only when movement fields match. These observations do not prove
all provider response combinations or all finality transitions.

## Open questions and explicit limits

- The TRON balance predicate relies on local observation time. Its inventory
  does not carry an execution-height anchor for every holding. TON's predicate
  compares local observation time to the saved send update time. Neither is
  established as proof that a provider snapshot includes the transaction.
- Starting a new refresh clears the account-level failure flag before a new
  inventory commits. The normal adapter awaits its flight, but a complete
  concurrency proof across multiple wallet accounts and overlapping refreshes
  has not been produced. No new vulnerability is asserted from this alone.
- Quote work is awaited inside these synchronizers. Cancellation and latency
  behavior across those requests need separate examination.
- Complete application/service/database integration, every cancellation
  interleaving, live node behavior, chain finality and UI behavior remain open.

Supporting excerpts in the app refresh wrapper, send predicates and inventory
models/client were read without claiming those entire files reviewed. Tests
exercise production package implementations with temporary databases and
synthetic transports; no live provider, funded transaction, simulator, phone
or App Store operation is authorized or used for this checkpoint.

## Hosted activation evidence

The earlier [activation/bootstrap workflow](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41618881396)
completed successfully at audit commit `3a2344f4aa29de40ed8ccf69ecc72e0e0dbfb8b0`.
The downloaded artifact matches GitHub's SHA-256 digest. All 27 archived files,
source/driver/fixture pins and per-method logs were verified: six control
methods pass; the isolated bootstrap-key mutation fails exactly the expected
method and its other five controls pass. [Durable receipt](../evidence/5.0.2-build104/hosted-near-multisig-activation/manifest.json).
This supersedes its earlier pending status and leaves its original source pin
and contract/runtime limitations intact.

## Reproduction

Use a clean checkout at the exact source pin and macOS with Swift 6.4. The
script compiles before execution and records the test executable hash. A new
build directory performs a fresh build; local evidence may reuse an isolated
cache and must say so. Dependency resolution can download public packages;
the individual test processes are denied network access. Two opt-in live
methods are deliberately excluded.

```sh
python3 scripts/tron-ton-ledger.py wallet scratch/build evidence/local/tron-ton-ledger
python3 -m unittest discover -s tests -p test_tron_ton_ledger.py
```


## Recorded local result

All **27** selected existing production-package ledger/journal methods pass;
**two** opt-in live-provider methods are excluded. Host compilation reused the
unchanged isolated cache from checkpoint 13 and finished before testing. The
whole compile-and-test selection took **102.427 seconds**. Four suite hashes,
all method logs, the executable hash and tool versions are preserved in the
[manifest and archive](../evidence/5.0.2-build104/tron-ton-ledger/manifest.json).
The cases cover cached balances after partial reads and reopening, stale tickets,
pagination, duplicate-wallet reservations, signature tampering, acknowledgements,
terminal receipts and migrations. They are inherited tests, not 27 newly authored
methods or a complete post-send-worker test. All **373** audit-helper checks pass.
The whole-wallet completion gate remains open with **16,917** outstanding items.


Publication scanning of the changed files and expanded new archives reports no
secret matches. An unfiltered scan of the entire audit repository reports 3,953
matches across inherited evidence, hashes and synthetic fixtures; that scan is
not claimed globally reconciled or passing here. Its redacted original reports
are retained alongside the precisely scoped passing publication scan. Workflow
lint reports only the known custom runner-label warning; both original and
filtered logs are retained. [Validation scope](../evidence/5.0.2-build104/tron-ton-ledger/validation/scan-scope.json).
