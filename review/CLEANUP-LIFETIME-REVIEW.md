# Session cleanup and sequence-store lifetime review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Tested app: `eef7eeb2d46c74aa6528b9b34ef122f9a61ef8ed`.
Corrected regression baseline: `822aa4539c2188ef6a752eaf228b0284c80216fa`.

## Source read and caller trace

Read complete HistoryService, SequenceStore, KeyValueStorage, CodableStore and
RPCHistory. Traced SessionEngine's expiration callback at lines 153–159 to
HistoryService.removePendingRequest, then to RPCHistory.deleteAll(forTopic:).
The factory creates HistoryService using the default background queue.

HistoryService queued a closure capturing its owner as unowned. The queue can
run after owner release. Capturing the history object directly lets committed
cleanup finish without retaining or dereferencing the service owner. This
preserves asynchronous scheduling and the existing topic filter; it does not
silently drop cleanup when the owner disappears.

SequenceStore already captured itself weakly, so it did not exhibit that crash.
However, its repeating timer stayed valid and registered after store release.
The repair explicitly invalidates that timer in deinit. It does not change
expiry dates, notification order, stored payloads or session identities.

KeyValueStorage's RuntimeKeyValueStorage implementation serializes each dictionary
operation on its private queue; its read/write/delete/bool methods and UserDefaults
conformance were read. This disposition does not establish atomic multi-step
operations in higher-level callers. RPCHistory's check-then-insert and scan/delete
sequences still need concurrency review. HistoryService remains partial for that
reason and for stale-work, verification-context and deletion-order boundaries.

DeleteSessionService waits on a network request before local removal. Oath's
OathWalletConnectService.disconnect at lines 455–480 separately revokes the
connection and removes its wallet mapping before awaiting that SDK operation.
This trace is not a new claim that remote latency bypasses app authorization.
The complete SDK deletion/error recovery contract remains open.

## Before/after proof

[OW-2026-022](../findings/OW-2026-022.md) records the confirmed crash and timer leak.
The same eight cases run independently with networking denied:

- Before: one unowned-reference abort, one timer-validity assertion, six controls pass.
- After: all eight pass.
- Fixture SHA-256: `e5413490d5d802d3162c24918180778feeeecb087471dd1824a273a4935153b5`.

A **testability seam is explicit**: the baseline adds an internal cleanupQueue
initializer parameter defaulting to the original global background queue, then
uses that queue for the unchanged unowned closure. Tests hold a serial queue,
schedule real production cleanup, release the owner, resume and drain the queue.
This controls scheduling, not the deletion implementation. The same seam and
fixture exist before and after; only the capture and timer teardown are repaired.

Timer tests inspect the actual private timer via Mirror and assert its validity
before/after owner release. A separate real Foundation run-loop control waits
past the three-second production period and checks that only expired sequences
are removed and notified once. Explicit deletion must not emit expiry. All
storage uses RuntimeKeyValueStorage and synthetic topics, not UserDefaults or
real wallets. Cleanup tests preserve other topics and cover repeated/absent and
multiple queued deletions, plus pending-request reads with expired/malformed data.

An initial control incorrectly used a primitive JSON-RPC params value. RPCRequest's
decoder correctly rejects primitives, so the subsequent get returned nil; this
was not evidence that HistoryService deleted a row. The corrected fixture uses
a readable object with invalid session fields and first asserts that the RPC
record is readable. Original failed fixture output and both fixture commits are
retained. The final paired runner verifies the corrected fixture hash exactly.

Full SDK suite: 165 passed/one skipped. Diagnostics: 118 passed/two skipped.
The audit helper suite passes 138 tests. Source/secret checks, diagnostics
coverage and unsigned generic iOS Release compilation (168.75 seconds) pass.
Paired execution took 70.799 seconds. See the [durable evidence manifest](../evidence/cleanup-lifetime/manifest.json)
for independent source, coverage and build results.

```sh
python3 scripts/checkout.py
python3 scripts/cleanup-lifetime.py .work/source --output .work/cleanup-lifetime --scratch .work/cleanup-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Remaining work

The SDK's ordinary SignClient retention limits the demonstrated app teardown
reachability. These are controlled owner-release tests, not a remotely triggered
Oath exploit. Concurrent re-use of a topic, deleting while a new request is
inserted, suspended-app timer behavior and full network deletion are not covered.

The authentication paths were also read: SessionAuthenticateRequestParams converts
TTL directly to UInt64; AuthRequestParams's ordinary initializer bounds TTL, but
synthesized decoding has not been exercised against that invariant here.
SessionAuthRequestService and LinkAuthRequester dereference the first chain and
create key material before that check. Their full caller invariants and synthetic
invalid-input behavior remain leads, not confirmed findings from this corpus.
The three authentication files previously marked reviewed for the OW-2026-005
response-topic work are reopened as partial: that evidence does not resolve
these input/lifetime invariants. This changes the coverage count without
erasing the earlier response-topic fix or its tests. CodableStore's force-try
encoding and migration behavior also remain partial.

No simulator, physical device, live relay, transaction or App Store operation.
