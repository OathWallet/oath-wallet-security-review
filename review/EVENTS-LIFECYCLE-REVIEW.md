# SDK event lifecycle review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Target: `4cfeb14ce9bd85ca2d10017cb053ab421df30cf2`.
Finding: [OW-2026-016](../findings/OW-2026-016.md).

Read in full, with hashes recorded in the coverage ledger:

- EventsClient: construction, policy guards, queue mutation, locking, worker
  ownership, opt-out, generation/revision acknowledgement and deinitialization.
- EventsClientFactory and Events: singleton construction and factory policy applied
  before initialization, preserving Oath's existing choice to disable telemetry.
- EventsDispatcher and NetworkingService: bounded retries, cancellation and the
  HTTP boundary. Delay values come from internal configuration, not user input.
- UserDefaultsStateStorage: default and persisted state plus isolated test suite.
- EventStorage, InitEventsStorage and MessageEventProperties: bounded persisted
  queues (30 errors, 100 initialization events, 200 messages); failed decoding
  returns an empty queue. Default stores remain UserDefaults, not secret stores.
- EventsCollector: trace/topic accumulation and error conversion. Opt-out now
  clears the trace; this does not prove every potential upstream trace is bounded.
- MessageEventType, MessageEvent, InitEvent and EventsImports: identifiers, event
  fields, fixed discriminators, decoding and module reachability.
- CheckWalletConnectSDK and EventsPrivacyLifecycleTests: production module graph,
  dependency seams, controlled transport, actual URLSession cancellation and exact
  test coverage. The fixture contains no real account or wallet material.

The application configure path was traced as context: Oath turns SDK telemetry
off, but previously did so after singleton initialization. Only this narrow call
path is covered here; the large app service is not newly marked fully reviewed.
The factory policy now closes that initialization ordering gap. The general
client retains explicit-enable behavior for compatibility, covered by a control.

The same nine cases produce 14 expected assertions before and pass afterward.
The two controls demonstrate enabled delivery and preservation of an active trace.
A URLProtocol intercept proves cancellation reaches the actual URLSession request;
no HTTP request reaches a remote server. The default-state test uses a unique
UserDefaults suite and removes it afterward. Negative async observations are
bounded, not exhaustive concurrency proofs. Requests already sent cannot be undone.

The exact target passes SDK tests, diagnostics, source/secret checks, diagnostics
coverage and unsigned generic iOS Release compilation. Those are host/compile
results, not a device/runtime matrix or a completed whole-wallet review.
See [evidence](../evidence/events-lifecycle/manifest.json).

## Prior full GitHub run

[Run 41291217273](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41291217273)
completed all **56 jobs successfully** at audit commit
`ca8abe442ba7c0a07eb9e7018ac30d059512085a`, targeting app commit
`e7aed8c9d08357df10a4f85be7d069a66fad07f8`. Downloaded artifacts retain the
original pins, expected failing baselines, skipped cases and logs. The index
contains 60 result objects at that app target and seven baseline result objects.
These are not 67 independent suites; some jobs emit multiple nested checks.
The [manifest](../evidence/ci-progress30/manifest.json) preserves downloaded
content and normalized published hashes. This is terminal evidence for the prior
target; it is not a pass for the newly changed source or complete code coverage.
