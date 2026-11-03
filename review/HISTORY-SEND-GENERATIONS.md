# Pending-history identity across asynchronous sends

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Reviewed application: `4cb121a588583b9b0adef626c05cbedafce3a759`. Regression-only baseline: `c446732194d1e81ef1127985434ec7f19c147268`.
Original baseline remains 4.1.15 (100), `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

## Cause and repair

[OW-2026-028](../findings/OW-2026-028.md) is distinct from synchronous history
atomicity. NetworkingInteractor and LinkEnvelopesDispatcher validate or create a
record, suspend during serialization/delivery, then resolve or delete by ID. A
replacement inserted during that suspension is consumed by the old operation.
NetworkingInteractor.approveSession has the same stale proposal-completion path.

The corpus replaces the entry at a controlled delivery boundary, including
replacements with identical ID, topic, origin, method, parameters, timestamp and
transport. Comparing those content fields alone cannot identify a new entry.
Six cases reproduce incorrect deletion or successful stale completion.

New history records now receive an optional, persisted local generation UUID.
Set returns the minted record; failed request sends delete only if that entry
still matches. Response and proposal completion capture their validated record
and pass it to resolve, which checks the generation and ID under the shared
history lock. A replaced response entry produces a requestReplaced error and
remains pending. Conditional request rollback preserves the replacement while
propagating the original send error.

## Compatibility

The added field belongs only to the local pending-history JSON. It is not added
to RPCRequest, RPCResponse, encrypted network payloads, wallet backups or wallet
secrets. Existing records decode with a nil generation. Their complete stored
snapshot is compared until removed; every new entry has a generation. No wallet,
Keychain, container, history namespace or existing identifier changes.

Legacy records lacking the field still complete normally. A legacy entry
replaced by a newly written one is protected. Identical replacements written
through a reopened history over the same backing store are also protected,
showing that entry identity is persisted rather than held only by one wrapper.
The corpus also verifies request rollback with local expectedResponseTopic
metadata, which is separately excluded from JSON-RPC encoding.

These checks cover decoding existing persisted data and compatibility of the
current SDK. They do not prove simultaneous mutation by an older app process,
old-binary behavior or direct tampering with stored generation values.

## Evidence and reproduction

Identical 14-case fixture SHA-256: `4e06f9d82c9592d6ca5a1bf238020261974f901d48b89224238c8d72a67fb119`.
Before: **10 assertions across six failed cases; eight controls pass**.
After: **all 14 pass**. Paired duration: **80.445 seconds**.
Cases run separately with networking denied and exact baseline failure matching.

The harness compiles complete production NetworkingInteractor, RelayClient,
LinkEnvelopesDispatcher, serializer and history. It substitutes a synthetic
Dispatching endpoint and an explicit host UIApplication callback. No live relay
or actual URL opening occurs. Relay publish fixtures repeat synthetic boolean
acknowledgements because RelayClient installs that subscriber after protectedSend
returns. This isolates history cleanup from a separate early-ACK ordering concern;
it does not validate real relay acknowledgement timing or retry semantics.

Link response fixtures decrypt the envelope and verify generation is absent from
its wire object. Relay fixtures inspect real outgoing publish/approval method
names and retain the settlement request as an independent pending entry. Session
approval uses synthetic RPC payloads: this tests transport/history bookkeeping,
not a complete peer handshake or actual application approval/signing flow.

The first exploratory fixture incorrectly expected irn_approveSession instead
of the production wc_approveSession method. Its two extra assertion failures are
retained as setup evidence and are excluded from the final baseline classifier.

Final-pin checks: **254 SDK passes/one skip**, **118 diagnostics passes/two
skips**, **162 audit-helper tests**, public/secret validation, diagnostics coverage
and unsigned generic iOS Release compilation pass. Build duration:
**161.63 seconds**. No simulator or device check was performed.

```sh
python3 scripts/checkout.py
python3 scripts/history-generation.py .work/source --output .work/history-generation --scratch .work/history-generation-build
python3 scripts/run.py .work/source walletconnect-sdk
```

## Remaining limits

This repair protects completion and rollback of the inspected request, response
and proposal paths. It cannot recall a message already accepted by an endpoint,
make send and local storage mutation one transaction, or establish authorization
at every pre-send suspension. Generic outgoing origin/topic policy, relay
acknowledgement ordering/lifetime, repeated response publication, proposal-error
rollback and cross-process writers remain separate unfinished areas.

RelayClient's incoming-notification acknowledgement still uses separate history
bookkeeping and requires a dedicated review; these send-completion tests do not
cover that callback. Legacy snapshot comparison is not a substitute for generation
tracking by other concurrent software that writes records without the new field.
RPCHistory, NetworkingInteractor and LinkEnvelopesDispatcher remain partial.
No remote signing exploit, duplicate signature or fund loss is claimed.

No App Store operation, real wallet material, live transaction, simulator or
physical device was used. Source repair is not proof of App Store availability.

## Publication

[Source repair](https://github.com/devdasx/oath-wallet/pull/39) merged as `da45a6b791a67f41073a85b4f1db67f9ca6318c5`. Application source matches the tested pin; 116 website and website-deployment differences are in [merge identity](../evidence/history-generation-merge-identity.json). This is not full-tree or installed-binary equality. Full current-target CI is not yet verified.
