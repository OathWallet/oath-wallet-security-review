# Incoming Link Mode boundaries

Reviewed application commit `f2019f3e752ee3fb1b57d7259abb8721779f0cc8`, following `18b1033433143f30eeedf5b29e1ab16ea4e12f88`
(regression-only baseline). Original review baseline remains 4.1.15 (100).

## Source trace and confirmed behavior

The complete `LinkEnvelopesDispatcher` accepts a URL, extracts `wc_ev` and
`topic`, decodes a base64url envelope through the production `Serializer`, then
persists requests or resolves response history. Its response path previously
used `RPCHistory.resolve(response)` without the topic/local-origin guard already
used by the relay path. A sender with topic B's key and a target pending RPC ID
could consume topic A's request. The later legitimate A response was lost.
Success and error responses both reproduced this. A response could also consume
a remotely originated request from the same history store.

The serializer intentionally supports plaintext type 2 for initial Link Mode
authentication. The dispatcher did not distinguish that initial request from
session messages or responses. A sender with no topic key could dispatch a
plaintext `wc_sessionRequest` or `wc_sessionDelete`, or consume a pending response.
The fixture proves subscriber delivery and history mutation, not downstream
transaction signing, session deletion or fund loss.

Oath configures `redirect.linkMode: false` in `OathWalletConnectService.swift:151`.
The inspected app source contains no `dispatchEnvelope` caller. Its pairing path
uses `Pair.instance.pair(uri:)`. SDK `SignClient.dispatchEnvelope` is public and
wired to this dispatcher. Thus this is a bundled dependency boundary defect;
a reachable installed-Oath exploit has not been demonstrated.

## Repair and protocol compatibility

[OW-2026-024](../findings/OW-2026-024.md) covers the related incoming-link defects.
The dispatcher accepts plaintext only when the decoded request method is
`wc_sessionAuthenticate`. Other requests and all responses require encrypted
(type 0 or 1) envelopes. Malformed or unknown envelope prefixes are rejected.
Incoming responses call the existing expected-response-topic/local-origin
history resolver, so rejection does not delete legitimate pending work.
Outgoing response acknowledgement remains unchanged.

The existing resolver supports a distinct authentication response topic derived
from the stored requester's public key. Both type-1 authentication success and
error controls exercise this, so a naive same-topic-only fix cannot pass.
This proves routing and encryption compatibility, not CACAO signature identity
or universal-link domain ownership. Those remain separate boundaries.

## Exact reproduced tests

The same 16 cases run before and after against full production dispatcher,
serializer, cryptography and history. Before: **18 assertions across eight failed
cases, with eight passing controls**. After: **all 16 pass**. Each case runs in a
separate network-denied host process; the paired run took 91.478 seconds.
Fixture SHA-256: `192c46a72414eb96ef2c92d3df3a9d488caa0b6e189b925a95de6ff80e608576`.

Adversarial cases cover cross-topic success/error, plaintext success/error,
remote-origin success/error and plaintext session request/delete. Controls cover
ordinary success/error, duplicate delivery, encrypted requests, initial plaintext
authentication dispatch, distinct-topic type-1 auth success/error, malformed
frames and tampered encryption. No live relay, URL opening, Keychain, real wallet
secret or external service is used.

The host harness copies the entire production dispatcher unchanged and adds
Foundation imports needed when UIKit is absent. Its minimal host `UIApplication`
endpoint traps if reached; only incoming paths run. Memory-only KMS and storage
are test substitutes. No response policy is reimplemented in test code.
The first host compilation lacked Foundation imports; that setup failure is
retained and is not counted as a production defect. The fixture was expanded
before its regression-only baseline commit; earlier exploratory logs remain.

Full SDK: **201 passed, one existing skipped isolation case**. Diagnostics:
**118 passed, two existing skips**. Source/secret validation and diagnostics
coverage pass. Audit helper validation passes 146 tests. Generic unsigned iOS
Release compilation passes in 452.21 seconds.

```sh
python3 scripts/checkout.py
python3 scripts/link-boundary.py .work/source --output .work/link-boundary --scratch .work/link-build
python3 scripts/run.py .work/source walletconnect-sdk
```

The runner exports exact commits and requires identical fixtures, exact per-case
assertion counts/messages, positive controls and final passes. Unrelated failures,
compilation errors, missing cases, skips and crashes fail classification.

## Coverage and remaining work

The dispatcher remains **partially reviewed** for outgoing URL-open races,
logging, ambiguous duplicate query items, URL trust and failure cleanup. A blanket
reviewed disposition would overstate this incoming-message proof.

Full files read for the surrounding trace include `LinkAuthRequestSubscriber`,
`LinkSessionAuthenticateResponder`, `LinkSessionRequestSubscriber`,
`LinkSessionRequestResponseSubscriber`, `LinkSessionRequester`,
`LinkSessionResponder` and `SessionRequestDispatcher`. Their dispositions remain
partial: user-authorization/verification semantics, async teardown, transport
failure rollback, session-to-link upgrade ordering and restored metadata
invariants need separate controlled proofs. In particular, requester/responder
redirect force unwraps and upgrading transport before checking a peer universal
link are leads, not declared findings in this corpus.

Earlier read dispositions and findings for general serializer/history are
preserved. This checkpoint does not establish their concurrent transactional
behavior, exhaustive parser safety or complete end-to-end protocol semantics.
No simulator, physical device or App Store operation occurred.

The `Response` value type was read in full: it only carries RPC ID, topic,
optional chain ID and RPCResult through synthesized Codable, with no validation
or authorization side effects. Its narrow reviewed disposition does not confer
trust on producer-supplied values. `SessionRequestsProvider` was traced through
its wall-clock debounce and delayed main-actor emission; thread confinement and
clock rollback remain partial. `ConsoleLogger` was read through level gating,
publisher and console formatting; debug payload retention, concurrency and all
production subscribers remain partial. These reads do not claim logging is
redacted or that an installed app exposes a sensitive diagnostic payload.

## Publication and prior CI evidence

[PR 34](https://github.com/devdasx/oath-wallet/pull/34) merged as
`888fa6f53e117bc8b2591c8a6643426d58fa2462`. The merged application source is identical to
the tested pin; 97 concurrent website-only differences are recorded in
[merge identity](../evidence/link-boundary-merge-identity.json). Full-tree equality
is not claimed.

The prior [CI run 41337776806](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41337776806)
completed 57 successful jobs. Its 57 artifacts were downloaded, and the log
hashes of 65 result records were verified: 58 passes pinned to app
`4cfeb14ce9bd85ca2d10017cb053ab421df30cf2`, plus seven deliberately failing
historical baselines. [Durable artifact manifest](../evidence/ci-progress31/manifest.json)
preserves their exact identities. This is separate from today's targeted tests;
the full matrix for the new source pin is not yet verified.
