# Relay metadata privacy boundary — progress 30

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Application target: `e7aed8c9d08357df10a4f85be7d069a66fad07f8`.
The confirmed, repaired privacy finding is [OW-2026-015](../findings/OW-2026-015.md).
The full audit remains incomplete.

## Source dispositions

Complete reads in this increment:

- `Publish.swift`: stored/decoded parameter fields, outbound JSON and method.
  The repair whitelists routing plus the already-encrypted peer message.
- `SessionResponder.swift`: session existence, request expiry, metadata
  collection, response forwarding and verify-context cleanup. Its history/topic
  association and concurrent use remain subject to the existing broader protocol
  review; this read alone does not prove all session races.
- `SessionReq.swift`: session acknowledgment/permission guards, optional wallet
  service forwarding, TTL calculation and relay request metadata. Wallet service
  discovery and HTTP implementation are not declared reviewed through this caller.
- `TVFCollector.swift` and `ChainTVFCollector.swift`: tag-dependent dispatch,
  method selection and optional data models. Reading the dispatcher does not
  mark every per-chain collector reviewed.
- `SolanaTVFCollector.swift`: successful response parsing, optional transaction
  hashes and handling invalid entries. No signatures are generated here.
- `SolanaSignatureExtractor.swift`: Base64 decoding and first-signature extraction.
  This helper is not a transaction validator: it uses a one-byte count and does
  not validate a complete message/signature array. A valid packet's bounded
  signature count fits one byte; malformed helper inputs can still produce a
  meaningless hash. This is not a signing authorization boundary, and the new
  publish encoder omits its optional relay metadata output. No reachable fund-loss
  exploit was established. Arbitrary-input resource robustness is not claimed.
- Existing `SolanaSignatureExtractorTests.swift` and `SolanaTVFCollectorTests.swift`:
  reviewed synthetic happy-path/error checks. These upstream suites were read,
  **not separately executed** by the application's dependency-minimal SDK harness.
- New `RelayMetadataPrivacyTests.swift`: exact outgoing-field checks, real
  collector input, decoded Params defense and encrypted peer-response control.

Partial/outstanding follow-up:

- `RelayClient.swift`: only the publish/acknowledgment path was traced here; the
  whole client remains partially reviewed.
- `EventsClient.swift`, `EventsClientFactory.swift` and `Events.swift` were read,
  but their initialization task, disable ordering, storage and dispatcher path
  need an adversarial lifecycle test. The constructor saves an init event and
  schedules stored delivery; some local event-storage paths do not check the
  telemetry flag. No live disclosure or deterministic race proof was run yet.
  The ledger explicitly retains these as partial, not fixed.

Previously reviewed networking and application configuration were inspected as
call-path context, without counting them as new file coverage.

## Evidence

The exact same four-case fixture fails 11 metadata assertions before the encoder
repair and passes afterward; its encryption/routing control passes in both phases.
The paired run takes 37.488 seconds including compilation. It uses no network,
real wallet, dApp, relay, simulator or device. Earlier compiler and nested-profile
failures remain under the same manifest. Broader host SDK validation passes 60
cases with one skip; diagnostics passes 118 with two skips. The generic unsigned
iOS Release build passes. These results are neither a live-relay interoperability
check nor a final-target full CI verdict.

The [previous Solana vector repair](SOLANA-VECTOR-ISOLATION.md), independent SDK
fixture regeneration, npm-tool advisory report and original timeout remain
source-pinned at progress 29. They are not silently reclassified as new-target
executions. All original findings remain visible.
