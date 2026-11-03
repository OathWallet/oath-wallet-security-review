# Link session metadata and transport changes

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Reviewed application: `57893f12d80eea8203a7e235733f055f5dbd7902`.
Regression-only baseline: `01e177d816a1bcb572a3050302e42ad444643962`. Original review baseline remains 4.1.15 (100).

## Source and cause

`AppMetadata.init(from:)` permits absent redirect metadata. Redirect's Codable
representation also permits an absent universal link. These are legitimate
optional fields for ordinary relay sessions and can survive a WCSession Codable
round trip. No invariant in that representation guarantees they exist merely
because a session's stored transport is Link Mode.

`LinkSessionRequester` force-unwrapped both redirect and universal link.
`LinkSessionResponder` force-unwrapped redirect before its universal-link guard.
The same synthetic persisted-form inputs reproduce three nil-unwrap crashes.

`LinkSessionRequestSubscriber.onSessionRequest` called
`upgradeSessionToLinkModeIfNeeded` immediately after finding a session, before
checking redirect metadata, chain/method permission or expiry. Missing redirect,
missing universal link, unauthorized chain, unauthorized method and expired
requests each changed the session-store transport even though the request was
then rejected. This can leave subsequent operations using a transport for which
peer metadata is missing. The tests prove the crashes and store mutations
individually, not an end-to-end attack against an installed app.

## Repair

[OW-2026-025](../findings/OW-2026-025.md) records this availability/state defect.
The requester now throws a missing-peer-link error instead of force-unwrapping;
the responder uses optional chaining and its existing error. The incoming
subscriber changes transport only after all existing checks succeed. Valid
requests still upgrade once and existing link sessions continue emitting.
Session wire/storage fields and wallet persistence identities do not change.

This deliberately does not make all redirect fields required during decoding:
ordinary relay and legacy metadata must continue to restore. Full URL scheme,
domain-association and peer identity policies remain separate review work.

## Paired production evidence

Identical 16-case fixture SHA-256:
`f8818ab9fba8f9306b78a9a853c77f20ca60b2c7320c4b46d969a475a9571d0b`.
Before: **three nil-unwrap crashes, five transport-state assertions and eight
passing controls**. After: **all 16 pass**. Each case runs separately with
networking denied; total paired duration 87.134 seconds.

The harness compiles complete sender, responder, subscriber, dispatcher,
serializer, session value and history implementations. It adds host imports and
a host UIApplication opening endpoint. That endpoint traps unless a fixture
explicitly installs a handler. Positive outgoing cases observe the target URL,
assert `universalLinksOnly`, complete the opening callback synthetically and
decrypt the returned envelope through production cryptography. No UIKit opening,
universal-link association or actual peer app is exercised.

Fixtures use the upstream in-memory session-store mock, memory-only KMS and
production history over runtime storage. Metadata and WCSession use real
Codable round trips. Outgoing controls verify request contents and pending
history, successful response contents and history completion, missing-session
rejection, missing-universal response rejection and permission rejection before
missing metadata can trap.

Incoming cases call the production `onSessionRequest` directly, bypassing the
subscription Task scheduling. Only valid incoming controls populate pending
history; rejected cases prove synchronous transport preservation, not complete
permission/error-response delivery. Their asynchronous error replies encounter
no pending RPC record. Callback teardown, error transmission and subscriber
thread confinement remain explicit gaps, not passing checks from this fixture.

The initial fixture placed an async call inside XCTUnwrap's synchronous
autoclosure. That compile failure is retained as setup evidence; the corrected
fixture was committed before the production repair. The paired runner demands
exact case events, assertion count/messages or file-specific nil-unwrap fatal
messages and signals. Unrelated failures, skipped/missing cases and compiler
errors fail classification. Eight controls prevent blanket rejection from passing.

Validation on the final pin: SDK **217 passes/one existing skip**, diagnostics
**118 passes/two skips**, **150 audit helper tests**, source/secret validation,
diagnostics coverage, and generic unsigned iOS Release compilation
(**159.85 seconds**) pass. Host tests and compilation are separate from runtime
verification. No simulator or physical device was used.

```sh
python3 scripts/checkout.py
python3 scripts/link-metadata.py .work/source --output .work/link-metadata --scratch .work/link-metadata-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Remaining coverage

These three Link Mode components remain partially reviewed for outgoing
request/response topic authorization, failure rollback, cancellation races,
validity of restored URL strings and queued callbacks. AppMetadata is partial
for its complete URL/redirect decoding policy, normalization and domain trust.
The prior incoming-envelope proof is preserved and reruns in the full SDK suite.

Oath advertises Link Mode disabled and no app caller of `dispatchEnvelope` was
found in the inspected app source. The SDK API is present, but no enabled Oath
remote trigger, signing bypass or fund-loss result is claimed. No App Store
operation, real wallet material, Keychain access or external URL opening occurred.

## Publication

[PR 35](https://github.com/devdasx/oath-wallet/pull/35) merged as
`2c4c53ed752508102ea4a786cb3c12f878add3b7`. The tested application source matches;
97 concurrent website-only differences are retained in
[merge identity](../evidence/link-metadata-merge-identity.json). This is not
full-tree or installed-binary equivalence. The full CI matrix on this new source
pin is not yet verified; earlier results keep their original pins.

## Follow-up

[Progress 41](SESSION-RESPONSE-ROUTING.md) repairs session responder topic,
origin and method validation. Generic transport contracts, history concurrency,
URL trust and queued subscriber lifetime remain distinct unfinished areas.
