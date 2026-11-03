# RPC history compound-operation atomicity

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Reviewed app: `6d8fda366773726364b0cb8b389d793cd34bd0bd`. Regression-only baseline: `c1d12689cceb67d9bd4cfc76371082fe60da5893`.
Original baseline: 4.1.15 (100), `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

## Source review and defect

[OW-2026-027](../findings/OW-2026-027.md) concerns RPCHistory's compound storage
operations. RuntimeKeyValueStorage serializes each individual dictionary call;
CodableStore performs independent reads and writes. Neither makes a history
check-then-insert, validate-then-delete or snapshot-then-delete sequence atomic.

NetworkingClientFactory, PairingClientFactory and SignClientFactory each call
RPCHistoryFactory.createForNetwork over their supplied backing storage. The
factory uses the same network namespace. An instance-only lock would therefore
leave ordinary separate history wrappers racing on the same records.

The controlled corpus reproduces duplicate insertion and duplicate response
resolution on both one instance and two instances over shared storage. Both
competing operations succeed. Topic cleanup and expiry cleanup also erase a
replacement record inserted after their old snapshot was read. These are actual
production history effects, not inferred from source-only pattern matching.
They do not demonstrate an app-level duplicate signature or fund-loss attack.

## Repair and compatibility

One process-wide recursive lock now protects complete RPCHistory reads and
mutations across instances, including expiry cleanup during construction. Thin
forwarding helpers enter through a locked method. Recursion supports internal
get/validate calls and the tested synchronous clock read. Network requests,
signing and asynchronous response waits are not inside these critical sections.

The shared lock also serializes independent namespaces/stores while a local
history operation runs. It does not introduce a new file format, key, namespace,
migration or persistent field. The fixture verifies independent relay/network
records with the same ID and 32 concurrent distinct IDs. This is a correctness
tradeoff; end-user latency under a large disk backlog has not been benchmarked.

## Reproducible evidence

Identical fixture SHA-256: `8f9dfaddc57644e8b2acc6c9375a428f89aab68a9dc97cf82d11e98b9e8a9797`.
**Before: 10 assertions across six failing race cases, five passing controls.**
**After: all 11 cases pass.** Paired duration: **140.433 seconds**.

The harness compiles complete production RPCHistory, CodableStore and related
modules. A thread-safe synthetic KeyValueStorage captures one read/snapshot,
signals that point and pauses it. A second worker then attempts the competing
operation. A bounded 250ms window allows the old second operation to complete;
the fixed second operation waits until the first is released. Completion and
gate timeouts are explicit failing assertions. The runner requires the exact
original failure assertions, so a scheduling miss cannot count as a reproduced
baseline failure. Each case runs separately with networking denied.

Controls verify sequential duplicate rejection, independent IDs, wrong-topic
rejection without consuming history, namespace independence and synchronous
reentry. The harness does not inject a production scheduling hook, access a
real wallet, use Keychain or invoke a live relay. Synthetic memory storage is
not evidence of multiprocess UserDefaults behavior or crash durability.

The initial lock edit made two formerly single-expression getters require
explicit returns. Its compile errors are retained as exploratory evidence;
the corrected source passes the paired corpus and full SDK suite.

Final-pin validation: **240 SDK passes/one skip**, **118 diagnostics passes/two
skips**, **158 audit-helper tests**, public/secret checks, diagnostics coverage
and generic unsigned iOS Release build pass. Release build duration:
**237.68 seconds**. Host tests and compilation are separate
from device/simulator runtime checks, which were not performed.

```sh
python3 scripts/checkout.py
python3 scripts/history-atomicity.py .work/source --output .work/history-atomicity --scratch .work/history-atomicity-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Review dispositions and remaining limits

RPCHistory remains partially reviewed: generic outgoing response origin/topic
contracts, response generations across async transport waits and global
cross-topic ID collision policy remain open. The lock does not bind a response
validated before an await to a later replacement record, and it does not guard
direct writes outside RPCHistory or separate processes sharing an app group.
No exhaustive race-freedom or multi-process transaction guarantee is claimed.

RPCHistoryFactory is reviewed for stable prefixes, construction and separation
of relay/network namespaces. KeyValueStorage is reviewed for its complete
protocol and RuntimeKeyValueStorage's serialized individual dictionary calls;
that does not make arbitrary compound client operations atomic. CodableStore
remains partial for throwing encoders, malformed persisted data, migration
coordination across instances/processes and crash-consistent persistence.
No scanner result is used to mark a source file reviewed.

No App Store upload/submission, simulator, physical device, external URL opening
or live transaction occurred. Source repair is not proof of App Store availability.

## Publication

[Source repair](https://github.com/devdasx/oath-wallet/pull/37) merged as `a853ab33e7739ab04003354d7992c33f0b07ef4b`. Application source matches the tested pin; 97 website-only differences are in [merge identity](../evidence/history-atomicity-merge-identity.json). This is not full-tree or installed-binary equality. Full current-target CI is not yet verified.

## Follow-up

[Progress 43](HISTORY-SEND-GENERATIONS.md) protects inspected request rollback,
response completion and proposal completion with persisted entry generations.
Other relay acknowledgement, pre-send authorization and cross-process questions
remain unfinished; this does not make transmission and local mutation atomic.
