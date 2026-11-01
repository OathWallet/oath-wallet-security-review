# Session watcher and storage callback lifetime review

Tested application: `d13c1979398ab3dc51d9af18f5bf23821e18262f`.
Regression-only baseline: `5522b5ff7c30279151ee2a4d88b6d9a8c0fd400e`.

## Source and reachability

Read both complete expiry watchers and SessionStorage, SequenceStore and
HistoryService. Traced factory construction at SignClientFactory.swift:61,
97–99 and retained watcher properties at SignClient.swift:164–166. These are
compiled SDK components. SignClient retains its watchers during its ordinary
singleton lifetime; the tests explicitly exercise release and repeated setup.
A remotely triggered Oath teardown or app startup crash is not demonstrated.

ProposalExpiryWatcher and RequestsExpiryWatcher scheduled repeating timers
with unowned captures. Releasing a watcher left a scheduled timer dereferencing
its destroyed owner. Calling setup twice overwrote the handle without removing
the old timer, causing two checks each period. SessionStorage installed two
unowned callbacks into a separately retainable SequenceStore; updates and
expiry cleanup after wrapper release also dereferenced a destroyed owner.

[OW-2026-021](../findings/OW-2026-021.md) groups these lifetime defects. Watcher
timers now invalidate on replacement and teardown and capture owners weakly.
Storage callbacks capture their wrapper weakly. Teardown does not clear shared
storage callbacks, which could otherwise remove a replacement wrapper's callbacks.
No persistence encoding, wallet identity, expiry threshold, protocol payload or
notification content changes.

## Same-fixture evidence

Ten production-code cases execute separately with networking denied:

- Before: four unowned-reference aborts, two exact duplicate-timer assertions,
  and four passing controls.
- After: all ten cases pass. Paired execution took 95.876 seconds.
- Fixture SHA-256: `ccd64d38d7a6709580d64e71bafaf4466b75f532fbc9343d62ac0bb7d9c727e5`.

The timer checks use the real Foundation run loop, assert main-thread execution,
and require a separate witness timer to fire beyond the production three-second
period. They do not replace the production timer implementation. The storage
checks use actual SequenceStore, CodableStore, RPCHistory and synthetic data in
RuntimeKeyValueStorage. They retain the underlying store after wrapper release.
Controls verify a replacement wrapper still receives callbacks; live updates
and expiry notifications still fire; only expired requests/proposals are removed;
and repeated cleanup does not emit duplicate expiry events.

The classifier requires the exact test start, an unowned-reference fatal message,
signal 6 and no assertion errors for an expected baseline crash. It does not
accept arbitrary crashes, missing cases or compilation failure. The initial
fixture failed compilation because Int loop variables needed explicit Int64
conversion for RPCID; this setup failure is preserved and is not a product finding.
The unchanged corrected fixture is committed before the production repair.

Full SDK checks: 157 passed/one skipped. Diagnostics: 118 passed/two skipped.
Source/secret checks, diagnostics coverage and 134 audit helper tests pass.
Unsigned generic iOS Release compilation passes in 145.54 seconds.
See [evidence manifest](../evidence/watcher-lifetime/manifest.json).

```sh
python3 scripts/checkout.py
python3 scripts/watcher-lifetime.py .work/source --output .work/watcher-lifetime --scratch .work/watcher-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Remaining scope

The two small watcher implementations have a documented review disposition;
SessionStorage remains partial because concurrent/stale session updates and
shared-store ownership are not exhausted here. Run-loop scheduling assumes a
running run loop as before; background-thread timer registration and suspension
behavior are not established by these host tests. These are not iOS runtime tests.

HistoryService still schedules deletion with an unowned capture. Its queue
lifetime and cleanup completion require a separate controlled proof. SequenceStore
uses a weak timer capture, avoiding this dereference defect, but does not explicitly
invalidate its timer on release; resource cleanup remains open. Authentication
request TTL construction, malformed persisted data and CodableStore's encoding
failure behavior also remain separate review areas. No broad component completion
is inferred from compiling those implementations into this harness.

No simulator, device, funded wallet, live service or App Store operation.
