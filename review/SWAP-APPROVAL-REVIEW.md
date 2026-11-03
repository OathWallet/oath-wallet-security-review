# Ordered router operations at the approval boundary

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Target: `e46fff5686db48a40103c9dbffe5e830cfc5548a`.
This follows the explicit mixed-operation question from progress 27. The
production-model collision is now reproduced and repaired as
[OW-2026-014](../findings/OW-2026-014.md).

## Source review

- `WalletConnectSwapReview.swift`: full read; compact route summaries and native
  folding now coexist with the untouched ordered decoded commands and deadline.
  Presentation retains extra transfers, conditions, unknown commands and optional
  flags instead of treating the exchange route as the full transaction.
- `WalletConnectCallDetails.swift`: previous complete parser review plus the
  transfer-source correction. Permit2 draws from the request sender; sweep and
  transfer draw from router funds. No changes to allowed selectors, addresses,
  ABI validation, recursion budget, execution or signing.
- `OathWalletConnectCallDetails.swift`: full original read plus the complete
  extraction/refactor. A shared command/value component feeds both first approval
  and expanded details. Numeric conversion, raw-unit fallback, recipient identity,
  source account, optional and unknown notices are retained; folded native
  conversions appear in the ordered command list too. Metadata is display-only.
- `OathWalletConnectEVMViews.swift`: complete 675-line read, including approval
  limits, exact account/contract navigation, bounded amount parsing, fee fields,
  completion/replacement status, gas receive QR/copy, cancellation and local
  diagnostics. The first screen now renders command lists even without a swap.
  Existing service revision/authentication binding is unchanged. Scene rendering,
  biometric authorization and actual user navigation are not runtime-verified.
- `WalletConnectApprovalOperationsTests.swift` and the independent standard-library
  fixture encoder: complete read. Equal-route pairs differ only by additional
  commands or their recipient/amount/order/optional semantics. Strict-chain and
  unknown-command controls ensure the test did not weaken request recognition.
- `WalletConnectSwapReviewTests.swift`: previous complete read plus assertions
  retaining folded, unknown, nested and transfer-only commands with their sources.

## Independent cross-check and evidence limits

Pinned ethers 6.15.0 independently decodes and re-encodes all ten generated ABI
vectors and checks their intended field semantics. Its transitive package lock
is in `fixtures/approval-abi`; this is a test-tool dependency, not an app addition.
The verifier is not a review of all ethers internals or a contract simulation.
The upstream Uniswap dispatcher comparison is pinned to
`edf19bfde87e6cf5b29046f6ca2f483a4ffd6ae6`. Correspondence to every deployed
router's bytecode remains unproven and must not be inferred from this review.

The paired fixture runs in network-denied processes, not on a chain. The first
approval's SwiftUI call graph was inspected and compiled; no simulator or device
was launched. The reader should distinguish these layers from end-to-end signing
or a real malicious transaction. The full dependency/application ledger remains
incomplete. No App Store operation is included.

## Separately observed CI failure

Run 41282913488, source `da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b`, has one
networking-package failure: `SolanaMultisigTests/testOfficialSquadsSPLVectors`
exceeded the per-process 120-second limit. Its log has a start event and timeout,
not an assertion mismatch. That test loops over 19 independent SDK vectors.
The original failed log and package summary are preserved. A prior local run on
`8dcc9c4` passed it in 45.722 seconds. Timing variability is not by itself proof
that the CI failure is harmless or repaired; it remains an explicit follow-up.


## Final local verification

At `e46fff5686db48a40103c9dbffe5e830cfc5548a`, networking has 1,224 passing cases
and 194 skips; diagnostics has 118 passing cases and two skips. Generic unsigned
iOS Release compilation, source/secret checks and diagnostic coverage pass.
The earlier broader run on `3e553d5` failed one test's positional-field assertion;
its log is retained. The final assertion selects fields by semantic labels.
The unchanged before/after fixture and vector hashes, binary hashes, toolchains,
durations and normalized process logs are in the durable evidence manifest.
