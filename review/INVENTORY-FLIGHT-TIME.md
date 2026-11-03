# TRON/TON inventory request freshness

Build 104 checkpoint 15 addresses [OW-2026-067](../findings/OW-2026-067.md).
The immutable prerelease baseline and all earlier evidence retain their pins.

## Reproduce

On macOS with Swift 6.4 and Python 3.11 or newer, use fresh output/scratch paths:

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach fd06fdff104d128e00cc414d2de1472f11752e04
python3 scripts/inventory-flight-time.py wallet scratch/before evidence/local/before --baseline --expected-commit fd06fdff104d128e00cc414d2de1472f11752e04
git -C wallet checkout --detach 63e0be4a10106fc577792a7fb3c6d69b1cc8870c
python3 scripts/inventory-flight-time.py wallet scratch/after evidence/local/after --expected-commit 63e0be4a10106fc577792a7fb3c6d69b1cc8870c
python3 scripts/inventory-flight-adjacent.py scratch/after/source scratch/after/build evidence/local/adjacent --expected-commit 63e0be4a10106fc577792a7fb3c6d69b1cc8870c
```

Dependencies may download during compilation; every selected regression process
has networking denied. The first driver expects three baseline failures and
two passing controls. The repaired source must pass all five. The adjacent
driver recompiles before running 27 existing offline ledger/journal methods;
two live tests are explicitly excluded.

## Evidence boundaries

The controlled response gate orders the old read before finality without sleeps.
Real clients decode those responses, real SQLite commits store them, and real
predicates decide freshness. Final transaction/send records are synthetic
fixtures written directly; this is not a complete signed-send, settlement,
SwiftUI or worker integration test. Exact source hashes, tool versions, method
logs and original failed fixture attempts are retained in the evidence bundle.

Starting the request after local confirmation is a conservative necessary
condition, not proof that a provider returned the latest block. This repair
does not address stale server caches, clock changes or other chains. No source
file receives a complete-reviewed disposition merely because these tests pass.
Remaining application/dependency coverage and provenance gaps stay open.

The earlier NEAR journal-race GitHub run
[41620145140](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41620145140)
completed successfully. Its downloaded archive digest, case logs and source,
driver and fixture identities are checked separately: nine controls pass, and
the deliberately broken reservation variant fails three methods while six pass.
[Receipt](../evidence/5.0.2-build104/hosted-near-journal-races/manifest.json).

No simulator, physical device, live transaction or App Store action is included.

## Local validation result

The exact paired tests record **two passes/three failures before** and **five
passes after**. All **27** adjacent offline tests pass. Diagnostics record
**119 passes and two skips**; public-source validation (4,860 files), diagnostics
coverage (722 catch sites), secret scanning and unsigned generic iOS Release
compilation pass. The product identifies 5.0.2 (104). All **376** audit-helper
tests pass. The completion gate retains **16,917** outstanding review items;
these are coverage/validation items, not a vulnerability count.

The initial helper run preceded creation of its evidence manifest and failed
with FileNotFoundError; that attempt is preserved. The two initial Swift fixture
compile failures are also retained. Neither is counted as an application bug.
The workflow linter's existing custom-runner-label warning is retained alongside
the successful run excluding only that known label warning.

[Manifest and raw results](../evidence/5.0.2-build104/inventory-flight-time/manifest.json).
Hosted replay of this repair is pending; its workflow uses pinned public commits,
read-only permissions and no deployment credentials.

The repair is merged in [PR84](https://github.com/devdasx/oath-wallet/pull/84),
`05e7917f0a3c26072b1a6b88d2e9e4a0d0310427`. The full merge tree matches the tested repair tree.
The changed publication files and expanded new evidence archives also pass a
redacted secret scan. This is not a new whole-history scan claim.
