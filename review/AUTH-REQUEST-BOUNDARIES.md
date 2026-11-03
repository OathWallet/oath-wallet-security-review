# Authentication request input and side-effect review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Tested app: `a04bebfafd38f02a441c1a0ee81540882438a99c`.
Regression baseline: `9050542eed7417e7c0a6ddb14f399ad51c028939`.

## Source and contract

Read AuthRequestParams, SessionAuthenticateRequestParams, both legacy relay/link
senders, AuthenticateTransportTypeSwitcher, SessionAuthenticatedProtocolMethod,
AuthenticatedSessionRecapUrnFactory and LinkEnvelopesDispatcher. Traced SignClient's
deprecated authenticate API and DEBUG link entry. The inspected Oath app source
has no outgoing invocation of these authentication APIs. This is a compiled SDK
input/availability finding, not an incoming Oath signing authorization bypass.

The ordinary AuthRequestParams initializer bounds TTL to 300–604800 seconds.
Synthesized decoding bypassed that check; a decoder configured for nonfinite
numbers could also construct NaN/infinity. SessionAuthenticateRequestParams
converted an unchecked Double TTL to UInt64. SessionAuthenticatedProtocolMethod
converted the sender's TTL to Int. Negative, nonfinite or huge values could trap.

Both legacy senders force-unwrapped the first chain after creating a temporary
X25519 key. Empty lists trapped. A non-EVM first chain threw only after key
creation. Valid EVM first chains followed by unsupported/malformed chains reached
the transport, response-key storage and response-topic storage. These senders are
legacy EVM-specific paths; the general authentication model documents other chain
families for newer flows and must not be globally limited to EVM.

## Repair

[OW-2026-023](../findings/OW-2026-023.md) records the related input defects.
A shared TTL validator now applies to initialization, decoding, sender entry and
direct expiry construction. Decoding retains the existing keys and optional
fields and still requires the TTL field. The internal expiry initializer throws
instead of trapping on invalid TTL. Both callers propagate that error.

The legacy senders require a nonempty list in which every chain is a valid EVM
CAIP identifier, before key creation, protocol TTL conversion or persistence.
The outer transport switcher applies these guards before creating a pairing.
That outer ordering is source-reviewed and compiled, not runtime-exercised by
the minimal sender harness. General AuthRequestParams still round-trips other
chain families. Valid minimum/default/maximum TTL, request contents, recap
resources, routing metadata and normal transport selection are preserved.

## Evidence and test seams

The identical 20-case fixture has **32 assertions across eight failed cases,
eight conversion/optional-unwrapping crashes, and four passing controls before**.
After repair all 20 pass; paired execution took 100.562 seconds. Fixture SHA-256:
`f163f4fe744e3fafe1900f99653aeb57bddfb4e538035589389083c32054235d`.

The regression baseline changes the two senders' concrete KMS dependency to the
existing KeyManagementServiceProtocol and adds a minimal LinkEnvelopeRequesting
interface. The actual LinkEnvelopesDispatcher conforms, and factory wiring keeps
its real implementations. Tests inject the upstream memory-only KMS mock and
transport spies. No sender branching is reimplemented. Newly generated test
agreement keys remain in mock memory; only counts and public routing are asserted.
No Keychain, actual relay, external URL opening or wallet credentials are used.

Cases independently cover decoder bounds/nonfinite values; direct negative,
NaN, infinite and huge TTL conversion; both empty-chain senders; rejection before
key creation; mixed and malformed trailing chains on both routes; decoded invalid
TTLs; valid minimum/default/maximum lifetimes and response routing; general-model
non-EVM round trips; and unproven link rejection. Every rejected send asserts
zero key, response-record, transport and subscription side effects. Four controls
ensure that blanket failure cannot satisfy the corpus.

The paired runner exports exact commits and runs each case in its own host
process with networking denied. It requires exact assertion counts/messages or
case-specific fatal messages and signals. Missing/skipped cases, compiler errors
and unrelated crashes fail classification. The fixture's initial compile failure
used a nonexistent String.hexToData helper; that setup log is retained separately.
The corrected identical fixture was committed before the production repair.

Full SDK: 185 passed/one skipped. Diagnostics: 118 passed/two skipped. Audit
helpers: 142 passed. Source/secret checks and diagnostics coverage pass. Unsigned generic iOS Release compilation passes (162.94 seconds).
Exact durations and build status are independently recorded in the
[evidence manifest](../evidence/auth-boundary/manifest.json).

```sh
python3 scripts/checkout.py
python3 scripts/auth-boundary.py .work/source --output .work/auth-boundary --scratch .work/auth-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Remaining scope

AuthRequestParams remains partial for domain/URI/nonce/resources and downstream
statement/signature semantics. The senders remain partial for key/record cleanup
on transport failure, concurrent cancellation and restoration. The protocol-method
factories still rely on validated caller TTL; the two supplied-TTL production
callers are now guarded, while the other inspected calls use the bounded default.

LinkEnvelopesDispatcher's incoming response path calls RPCHistory.resolve without
an explicit response topic. Its serializer, link trust, response-correlation and
logging boundaries require their own controlled proof; this corpus replaces the
link endpoint with a spy and does not claim to test those behaviors. Modern
multichain authentication, complete peer flows and actual relay retention remain
separate work. No simulator, device, transaction or App Store operation occurred.

## Follow-up

[Progress 39](LINK-ENVELOPE-BOUNDARIES.md) adds a controlled proof and repair for
the incoming link encryption and response-topic gap noted above. Outgoing
transport cleanup and the other listed limitations remain separate work.
