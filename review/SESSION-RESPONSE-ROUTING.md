# Session response routing

Reviewed application: `8508d02deaf965dbe6f46b3c0ca637074234e5da`. Regression-only baseline: `42846f9f9b9ff66ff8407700aa77539e70f963c5`.
Original review baseline remains 4.1.15 (100), `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

## Finding and repair

[OW-2026-026](../findings/OW-2026-026.md) concerns the bundled SDK's two
session responders. Both accepted a pending request by ID while checking only
that the supplied session existed. Neither compared the pending request's topic
with that session. HistoryService also mapped local-origin records and other
outer RPC methods whose parameters decoded as SessionType.RequestParams.

Two simultaneously stored synthetic sessions demonstrate cross-session routing.
The link path encrypts the supplied result (or expiry error) using the wrong
session key and removes the other pending record. The relay responder reaches
its networking endpoint with the wrong topic; the fixture records that call but
does not run a live relay. Local-origin and other-method records were also
accepted. This is an SDK response-target validation defect, not proof of an
Oath app signing bypass, external attack or fund loss.

HistoryService now requires a remote-origin wc_sessionRequest for this getter.
The immutable Record.origin property is publicly readable across SDK modules;
its Codable representation is unchanged. Both responders check that the mapped
request topic matches before metadata checks, expiry replies, response sending
or completion side effects. They use that same captured request for expiry,
avoiding a second history lookup. No wallet, Keychain or storage migration changes.

## Evidence

Identical 12-case fixture SHA-256: `80d99753f87c4a704071e3a49de814ade7164d1f5e1d3b31709b5e3ec5736572`.
Before: **18 assertion failures across eight invalid cases; four controls pass**.
After: **all 12 pass**. The paired runner exports exact commits, checks fixture
identity and runs each case separately with networking denied. Duration:
**75.991 seconds**. Original exploratory attempts are retained.

Invalid cases cover wrong session for fresh and expired requests, local origin
and wrong outer protocol method, for both link and relay responders. Controls
cover valid success and expired requests on both paths. Link fixtures use the
complete production responder, dispatcher, serializer and history, decrypt the
observed envelope with the requested session's key, and check history removal
or preservation. Session metadata traverses real Codable round trips.

The host UIApplication endpoint is an explicit synthetic callback; no external
URL or actual UIKit operation runs. KMS and session storage use upstream memory
mocks. The relay endpoint is upstream NetworkingInteractorMock, so relay
acknowledgement and history consumption are not proved by these tests. All
fixtures use synthetic requests and keys. No funded account or transaction is used.

Validation at this source pin: **229 SDK passes/one skip**, **118 diagnostics
passes/two skips**, **154 audit-helper tests**, public/secret validation,
diagnostics coverage and unsigned generic iOS Release compilation pass.
Release build duration: **160.63 seconds**. These are host and
compile results, not simulator/device runtime results.

```sh
python3 scripts/checkout.py
python3 scripts/response-routing.py .work/source --output .work/response-routing --scratch .work/response-routing-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Reachability and remaining gaps

OathWalletConnectService's signed response at line 1330 and general response at
line 1505 pass the original request's topic and ID together. The signing path
also rechecks the pending item, unlocked state, deadline, wallet mapping and
session authorization. No inspected caller supplied another request's session.
Oath advertises Link Mode disabled. The fix hardens the SDK's API boundary;
no remote cross-wallet signing exploit is claimed.

Generic transport respond/resolve APIs still validate by ID without an explicit
outgoing origin/topic contract; authentication has distinct derived response
topics, so those paths require separate compatibility review. History set and
resolve compound operations and replacement while async sends are suspended
remain unresolved concurrency concerns. HistoryService's other getters and
pending-provider filtering are not validated by this response-only repair.

RPCHistory and relay SessionResponder are reclassified from reviewed to partial
because these remaining areas were not covered by their earlier narrow review.
Previous evidence remains intact. No source-to-App-Store equivalence or completed
whole-wallet audit is asserted. No App Store, simulator or device operation occurred.

## Publication

[Source repair](https://github.com/devdasx/oath-wallet/pull/36) merged as `0d0f31e4c1f2c77263742d3c796ceb3788634166`. Application source matches the tested pin; 97 website-only differences are recorded in [merge identity](../evidence/response-routing-merge-identity.json). This is not full-tree or installed-binary equality. Full new-target CI is not yet verified.
