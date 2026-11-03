# Build 103 diagnostic test failures

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Two jobs failed during the [release-tag matrix](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41532120820). We verified the SHA-256 digest of each GitHub artifact before inspecting its individual tests. [Original failure receipts](../evidence/5.0.1-build103/ci-retests/failures.json).

## Arc token decimals

The Arc test expected one RPC decimals error and one invalid transaction sender error. It received three events. A fixture-only observation on the release tag identified the third as a local decoder reporting the same RPC rejection. An unavailable required decimal scale still makes the inventory incomplete and prevents displaying the tracked amount. Optional name and symbol lookups remained quiet. No incorrect balance or signing outcome was observed.

[Wallet PR 59](https://github.com/devdasx/oath-wallet/pull/59) removes the redundant report at the inventory boundary. Malformed data in a successful RPC response still produces a decoder diagnostic. Sixteen fresh processes passed this test on the repair. All seven opted-in provider diagnostic scenarios passed in separate network-denied processes. Each corresponding disabled control skipped as expected. [Observed event types and repeated runs](../evidence/5.0.1-build103/ci-retests/arc-reproduction.json) · [Repair diagnostic suite](../evidence/5.0.1-build103/ci-retests/arc-repair/diagnostic-modes.json).

## Extended-key job

The key-import, recovery and child-index checks in the same job passed. A later step intended to reproduce a historical race in four multisignature diagnostic **tests**. Its two-second timer sometimes released delivery before the original polling code took its final snapshot. All four original checks unexpectedly passed on this run, so the evidence job correctly failed.

The revised replay controls the in-memory transport. The old consumer takes its final snapshot before the transport is released. The repaired consumer accepts delivery at its expectation before it reads the event. Both versions run the original assertions against their respective production libraries. Bitcoin, Bitcoin Cash, Dogecoin and Litecoin each reproduced the old failure and passed on the reviewed release. Network access was denied for all eight executions. [Replay results and per-test hashes](../evidence/5.0.1-build103/ci-retests/delivery-replay.json) · [Reproduction script](../scripts/multisig-diagnostic-delivery.py).

These follow-up results leave the two original GitHub jobs recorded as failed.

A separate exploratory run started all provider XCTest cases in one process. Several diagnostics suites could not observe their private sinks after the process-wide diagnostics service was configured by an earlier suite. This run was stopped and is excluded from passing totals. The package's standard audit runner isolates XCTest cases. The seven explicit diagnostic scenarios above also ran separately.

The Arc repair is now merged in [wallet PR 59](https://github.com/devdasx/oath-wallet/pull/59). On that source the standard isolated full provider package passed 1,323 XCTest cases with 201 explicit skips and no failures. It had no additional Swift Testing cases. The unsigned generic iOS Release build succeeded. [Package results](../evidence/5.0.1-build103/ci-retests/arc-repair/OathAnkr.json) · [Tested source and merge receipt](../evidence/5.0.1-build103/ci-retests/arc-repair/merge.json).
