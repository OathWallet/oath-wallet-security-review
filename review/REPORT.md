# Security review progress report

Status: **IN PROGRESS — not a completed whole-wallet audit**.

Reviewer: Codex, acting at the maintainer's request. No independent security
company endorsement is implied. Baseline: Oath Wallet 4.1.15 (100),
`c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

## Method and scope

The intended scope is the full shipped app and the upstream implementations it
uses: custody, import, storage, authentication, backup, signing, transaction
review, swaps, WalletConnect, networking, diagnostics and build supply chain.
Website services are inventoried but excluded from the mobile-wallet verdict.
No production secrets or live financial transactions are used.

The inventory hashes every tracked file. Entries remain outstanding until a
specific source review and its scope are recorded. A full package test suite
does not establish full branch coverage, end-to-end chain correctness or manual
review of every file.

## Findings

- OW-2026-001: object collection bound was omitted in WalletConnect JSON parsing.
  Reproduced against production source; one-line repair passes the same corpus.
- OW-2026-002: aezeed bridge source referenced by rebuild instructions is absent
  from the public baseline. Source is now published and tested; historical binary
  equivalence remains unresolved after differing reconstruction hashes.

## Validation boundaries

Local results are recorded per command under `evidence/`. Initial package runs
used Swift's default Xcode build system and failed during resource signing.
Native-build-system reruns are separate evidence, not replacements for failures.
Generic iOS compilation does not exercise Face ID, Keychain on iOS, app lifecycle,
WalletConnect peer interaction or real transaction execution.

The existing vault harness copies production sources into a host executable and
substitutes network/hardware and selected derivation boundaries. Those limits
must accompany its results. Tests marked opt-in remain skipped.

## Outstanding work

- Complete file-by-file security dispositions and all chain integration traces.
- Review the reachable upstream cryptographic and WalletConnect implementations.
- Establish dependency/binary provenance beyond archive checksum verification.
- Add remaining adversarial, property and fault-injection cases from those traces.
- Resolve any resulting runtime-only uncertainty using narrowly scoped checks.

There is currently no basis for a whole-app completion verdict, an App Store
binary-equivalence claim, or a ranking against other wallets. The final report
must retain these gaps until evidence resolves them.

## Current evidence snapshot

Source-fix target: `ae5a35cec58f51bcfd6de3cd55950b47fa055a51`, merged through
[application PR 1](https://github.com/devdasx/oath-wallet/pull/1).
The local baseline generic-iOS Release build passed. The baseline host vault
security harness passed 158 checks. The fixed production parser passed 6,016
adversarial checks; the baseline failed exactly the object-limit check.

[GitHub run 41238400744](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41238400744)
reproduces those checks against the source-fix target and records its own
Xcode 27.1/Swift 6.4 toolchain. The generic iOS Release build and security host harness have passed on this
fixed commit; the remaining job statuses must be read directly. Scheduled jobs
are not passes. The earlier run failed the expected Xcode-version guard and was
cancelled. Local initial failures also include resource signing and AppleDouble
C-header pollution on an external volume; neither is hidden by successful reruns.

Both Wallet Core upstream release ZIP hashes match the app manifest. This is
archive integrity evidence, not source-to-binary equivalence. Its complete
3,941-file upstream inventory is separately recorded: three files were read
fully, two partially, and 3,936 remain outstanding.
The application repository inventory contains 4,635 tracked files, including
website-only changes after the baseline; website files do not change app scope.

Raw Gitleaks reported 431 matches when invoked from outside the app root. All
431 reconcile with the application's existing exact, hash-bound fixture/source
exceptions; there are zero newly unmatched fingerprints in that run. This
reconciliation is not an independent review of those exceptions. A source-root
scan and the public release boundary validator pass. Raw records are preserved.

See [method](METHOD.md), [source notes](READ-NOTES.md), and
[dependency limitations](DEPENDENCIES.md). There is no completion verdict.

## Test-suite qualification

The initial full XCTest runs exposed process-global diagnostic state: production
`OathDiagnostics.configure` initializes one outbox per process, but different test
cases attempt to install different sinks. The audit runner now uses SwiftPM's
separate XCTest processes. Original failures are retained, not relabeled passes.

Isolation does not make the whole suite pass. Remaining failures include:

- legacy diagnostic expectations for availability errors now deliberately excluded;
- TON/XRP expired-price tests expecting malformed data instead of the current
  availability-deferral error, although both paths reject the stale quote;
- four missing public account-policy endpoint registrations (Filecoin, Sei, 0G,
  IoTeX); no direct application caller of that API was found;
- a test comparing encoded JSON byte order and a context-equality assertion that
  predates additional privacy-safe context fields.

These are investigation items, not a claim that all failures are harmless. Required
package validation remains **failed** until each expectation/implementation has a
reviewed repair and a successful rerun. No production diagnostic behavior was
changed to force a green result. A separate process-isolated rerun preserves xUnit
case-level results as well as command logs.

Current source coverage: 30 fully read application-repository files, one partially
read, 4,604 outstanding. These include non-code assets and website files; counts
are a coverage ledger, not a percentage security score. The completion gate also
checks the upstream inventory and rejects outstanding dependency review.

## Published repair status

[Application PR 1](https://github.com/devdasx/oath-wallet/pull/1) is merged at
`a6138b3b532c837bcc08adb1d7135cad4d3a54b7`. The tested source target remains
`ae5a35cec58f51bcfd6de3cd55950b47fa055a51`; the original baseline is unchanged.
The repair is public source, not an App Store update.

GitHub package results available at this snapshot: OathDatabase 773 cases
(71 skipped), OathDiagnostics 120 cases (2 skipped), OathCloudBackup 58 XCTest
cases plus 1 Swift Testing case, OathAezeed 5 cases, and OathWalletHandoff 12
Swift Testing cases passed. No skipped case is counted as executed coverage.
The same fixed source also passed the 158-check security harness locally.

The complete intended review is not finished. The progress release preserves
logs, source pins and checksums so another reviewer can inspect and continue it.
It is a prerelease evidence snapshot, not a completed audit certificate.

## Follow-up source repair and evidence

Current target: `d2fccbe8e586e7fc48609a2a48fc4a55923aeaea`, merged through
[application PR 2](https://github.com/devdasx/oath-wallet/pull/2).
OW-2026-003 repairs missing public signing-policy adapters; no direct application
caller or fund-loss exploit was established. The original authority implementation
with added regression tests failed 37 assertions; the repaired targeted suite
passed all 27 cases.

The updated host runner retains one real XCTest process log per case rather than
trusting Swift parallel XML's missing skip markers. On this target, Bitcoin has
268 passed / 60 skipped / 0 failed; diagnostics has 118 passed / 2 skipped /
0 failed. The focused Ankr adapter/price/request selection has 27 passed / 0 skipped /
0 failed; this is **not** a full Ankr pass. Skipped live checks remain skipped.
The unsigned generic-iOS Release build, source boundary, Gitleaks and diagnostic
coverage checks passed locally. Exact command results are in
`evidence/followup-results.json`. The earlier failures remain in the evidence.

The remaining earlier-target CI jobs were cancelled and superseded by a full
current-target run; cancellation is not a pass. The broader Ankr diagnostic-test
failures, upstream review and binary provenance gaps remain unresolved.
