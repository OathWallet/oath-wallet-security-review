# Bitcoin payment recovery and interrupted resets

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

A host test substituted a different, already-signed payment for the bytes in a local SQLite journal. Both payments spent the same synthetic inputs. With no history returned by the injected peer, the original reader let the changed recipient reach the rebroadcast decision. No transaction was transmitted. Separately, three existing upgrade tests found that the wallet's own reset fence rejected a write during startup.

[Payment identity, severity and compatibility](../findings/OW-2026-044.md) · [Interrupted reset](../findings/OW-2026-045.md) · [Merged app changes](https://github.com/devdasx/oath-wallet/pull/56).

## Source and execution

The unchanged production code at the parent of app PR 56 failed three of 800 selected database tests, with 72 explicit skips. Commit `8425bc0597b6bd4ab36f8710d0e8d939d786a7fa` adds the failing payment test. All four named assertions reproduced with network access denied. At `5071662dc0700d7011795035aa14b5795a4a1e3a`, the same four test functions passed, plus three controls for chain and receipt mismatches, a same-ID witness change, and opening an older database. The controls include Bitcoin, Bitcoin Cash, Litecoin and Dogecoin. The database and Bitcoin packages passed 732 and 314 tests, respectively, with 72 and 60 explicit skips. The diagnostics suite passed 119 and skipped two.

The unsigned generic iOS Release build, public release validator, secret scan and diagnostics coverage check passed on the fixed source. The Git tree at public merge `ad77a9d5f790114ec90c7bba59d1546279c9c794` matches the tested head. The [5.0.1 (103) release tag](https://github.com/devdasx/oath-wallet/releases/tag/v5.0.1-build103) predates these changes. Evidence covers the host tests and compilation. App Store distribution, device execution and live rebroadcast were outside these checks.

[Before results and log hashes](../evidence/progress56/before/result.json) · [After results and log hashes](../evidence/progress56/after/result.json) · [Database suite](../evidence/progress56/packages/fixed-database/OathDatabase.json) · [Bitcoin suite](../evidence/progress56/packages/fixed-bitcoin/OathBitcoin.json) · [Build and merge evidence](../evidence/progress56/integration.json).

## Reproduction

On a compatible macOS host with Xcode, use two directories for the Swift builds. The script checks the application commit, the selected test, its exact fixture source and its expected failure or success. Each test process runs with network access denied. The build step can retrieve its pinned public packages.

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-recovery-source
git -C /tmp/oath-recovery-source checkout --detach 8425bc0597b6bd4ab36f8710d0e8d939d786a7fa
python3 scripts/bitcoin-journal-recovery.py /tmp/oath-recovery-source --before --scratch /tmp/oath-before-build --output /tmp/oath-before-result
git -C /tmp/oath-recovery-source checkout --detach 5071662dc0700d7011795035aa14b5795a4a1e3a
python3 scripts/bitcoin-journal-recovery.py /tmp/oath-recovery-source --scratch /tmp/oath-after-build --output /tmp/oath-after-result
```

## Other checks at the historical review target

At `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`, we rebuilt the prepared aezeed framework twice. Both complete file sets matched the reference. Its prepared Go bridge passed the race-enabled host suite and vet. All four public seed fixtures and all 64 address and derivation fixtures matched. The two builds do not establish the provenance of older pre-repair archives. [Framework file hashes](../evidence/progress56/aezeed-provenance/result.json) · [Bridge checks](../evidence/progress56/prepared-bridge/result.json).

All 76 Squads SDK vectors reproduced with the network denied to the generator. There were 19 cases each for setup, native transfers, SPL transfers and Token-2022 transfers. The advisory gate reproduced its archived decision on exactly the original scan and source-selection inputs. Its 40 raw advisory occurrences had zero unresolved selected-source intersections. This replay did not fetch a fresh advisory database or establish historical binary clearance. [Squads output](../evidence/progress56/squads/8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707/result.json) · [Advisory inputs and result](../evidence/progress56/advisory/result.json).

The original recovery service and status reader retain partial dispositions. The fixture covers the decision before rebroadcast. Peer consensus, arbitrary joint database tampering, UI authorization timing and recovery in a live network environment remain outside its evidence. Three of the 115 required checks still lack a passing record on the pinned revision: OathAnkr, upstream native Wallet Core, and upstream extended-key type handling. The complete ledger has 16,583 open entries. [Compiled input dispositions](../evidence/progress56/compiled-inputs.json) · [Previously published Stellar reproduction passed on GitHub](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41526433335).
