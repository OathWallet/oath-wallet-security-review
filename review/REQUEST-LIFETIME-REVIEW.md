# Outgoing session request lifetime review

Tested application: `05f1f349938c3281810241513bae8beceab35ffd`.
Regression-only baseline: `a90d99005f3b8476178a968ba1016c0347e0328e`.

## Read scope and call path

Read the complete SessionRequester (`LinkAndRelayDispatchers/SessionReq.swift`),
SessionRequestDispatcher, LinkSessionRequester, WalletServiceFinder,
WalletServiceSessionRequester and its protocol; SessionRequestProtocolMethod;
SessionStorage; SequenceStore; DeleteSessionService; ProposalExpiryWatcher and
RequestsExpiryWatcher; HistoryService. The short protocol-method definition and
wallet-service protocol are reviewed. The larger transport, persistence and
lifecycle implementations remain partial because the questions below are not
resolved by these tests.

Traced `SignClient.request(params:)` to SessionRequestDispatcher, which checks
session existence/acknowledgement before choosing relay or link mode. The relay
requester checks method/chain permission, then may choose a wallet service from
scoped properties. NetworkingInteractor forwards `protocolMethod.requestConfig.ttl`
to relay publication. This connects the tested wrong argument to the relay TTL;
the tests do not invoke a real relay or prove its retention behavior.

The inspected Oath service builds approvals and calls `Sign.instance.respond`;
no outgoing `Sign.instance.request` invocation was found in application source.
The finding concerns a compiled SDK API, not a demonstrated incoming Oath
signature bypass. Existing incoming request validation is a separate boundary.

## Confirmed finding

[OW-2026-020](../findings/OW-2026-020.md) has two related defects: a calculated
request lifetime was discarded in favor of the default protocol method, and a
wallet-service match bypassed request expiry validation. The fix validates
before route selection and uses the calculated method instance for publication.

The [protocol's expiry and relay TTL contract](https://specs.walletconnect.com/2.0/specs/clients/sign/rpc-methods#wc_sessionRequest)
ties publication lifetime to an explicit request expiry. Existing whole-second
rounding, the 300-second fallback without an expiry, and the ability to send the
remaining portion of an already-created request are preserved. The change does
not reset elapsed requests to a fresh minimum lifetime.

The repair retains session/permission checks, request ID, method, chain, params,
expiry field, tag and prompt. Valid service routing still sends once to the
selected service, without relay fallback when that service fails. No stored
identity, encryption format or migration changes.

## Controlled evidence

Same **11 cases** in independent network-denied host processes:

- Before: **six expected assertions across four failed cases**, seven passing controls.
- After: **all 11 cases pass**.
- Fixture SHA-256: `f5d45ee179a515820fe5508c0306b4c00b8e7378eed14e8f59e0d1fa9d66568d`.

Production SessionRequester, WalletServiceFinder and request/protocol models
execute unchanged in the harness. An upstream in-memory session-store fixture
and transport spies replace storage/network endpoints. The schema compilation
also includes the real SessionStorage and HTTP requester, but this corpus does
not exercise their persistence or HTTP-response behavior. No test copies the
requester's branching implementation.

Tests cover one-hour and elapsed one-minute lifetimes; missing expiry;
expired/unbounded requests on both routes; valid service payload/URL; denied
method/chain; missing/unacknowledged sessions; and transport failures. The
expected relay lifetime is bracketed by real before/after calculations, avoiding
an assumption about exact wall-clock scheduling. Request contents are asserted
independently from the relay configuration.

The paired evidence classifier checks exact case names, terminal outcomes,
assertion text/count and exit status. Compilation failures, unrelated errors,
missing/skipped tests and arbitrary crashes do not satisfy the proof. The first
test compile failed because the test imported internal relay configuration
without `@testable`; that setup log is retained separately. No production change
was made to expose those properties.

Full SDK checks: **147 passed/one skipped**. Diagnostics: **118 passed/two
skipped**. Public source/secret checks, diagnostics coverage, **130 audit helper
tests**, and unsigned generic iOS Release compilation (**30.72 seconds**) pass.
See the [durable evidence manifest](../evidence/request-lifetime/manifest.json).

```sh
python3 scripts/checkout.py
python3 scripts/request-lifetime.py .work/source --output .work/request-lifetime --scratch .work/request-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Still open

- Link mode assumes redirect/universal-link presence with force unwraps; restored
  state and the complete creation invariant have not been tested here.
- Expiry watchers capture `unowned self` in repeating timers. Teardown behavior
  and reachable lifecycle conditions still need controlled tests.
- SessionStorage callback ownership and HistoryService's asynchronous deletion
  need lifetime and stale-work checks. SequenceStore uses weak timer capture,
  but timer invalidation/resource ownership is not established by this corpus.
- DeleteSessionService waits for remote delivery before local cleanup. Oath's
  wrapper revocation and failure recovery remain separate review work.
- Wallet-service URL policy, redirects, response-ID/content validation, response
  size and logging boundaries are not resolved by a transport spy.
- Cancellation, concurrent revocation and late completion are not covered by
  the eleven lifetime cases. These files remain partial in the ledger.

No simulator, physical device, live service, transaction or App Store operation.
