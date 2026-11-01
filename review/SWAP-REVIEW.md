# Swap decoding, quote binding and progress review

Target: `8dcc9c4c50eae2010b648782c0582c3db70c6357` (4.1.15, build 100).
This increment reviews request/display boundaries and read-only observations.
It does not establish arbitrary-router safety or on-chain settlement correctness.

## Complete source reads

- `Packages/OathAnkr/Sources/OathAnkr/WalletConnectEVMAction.swift`: fixed-size
  standard ABI decoding, canonical address and integer padding, zero native
  value for token calls, and chain/address-scoped V3 router classification.
  Shared ERC-20/ERC-721 selectors do not by themselves prove token standards.
- `WalletConnectCallDetails.swift`: canonical offset/length/padding checks,
  chain/address router lists, 64-command budget, bounded recursion, optional
  subplan propagation, exact-in/out route direction, payer/recipient sentinels,
  V2 paths, native conversions and history-only attribution/hop-price tolerance.
  Unknown or malformed commands retain unknown status. Request bytes stay
  immutable. Deployed router bytecode/source correspondence was not verified.
- `WalletConnectSwapReview.swift`: route extraction, bound semantics, Router02
  balance sentinel and conservative adjacent wrap/unwrap folding. Multiple,
  optional and partially decoded routes retain explicit conversions. This file
  was read completely, but primary-summary completeness for mixed transfer/swap
  command batches remains an open review question below, so its disposition is
  partial rather than a resolved component review.
- `ThorchainSwapReview.swift`: bounded ASCII memo grammar, supported asset
  resolution, decimal/exponent limits, streaming/affiliate constraints, quote
  asset/destination/fee/expiry binding, minimum retention, cancellation-aware
  quote pacing and diagnostics. The provider's suggested minimum never replaces
  the signed memo's minimum. Quotes remain estimates, not execution guarantees.
- `ThorchainEVMSwapReview.swift`: native memo transfer and canonical router ABI,
  msg.value versus ERC-20 amount, hidden native-payment rejection, decimal
  conversion to protocol units, router/vault/inbound-chain recognition, halt
  flags, unambiguous available pools and exact quote query construction. Provider
  assertions about active vaults and prices remain a trust boundary.
- `ThorchainSwapProgress.swift`: inbound hash/chain/memo/coin validation, bounded
  outbound lists, positive observed amounts, output/refund distinctions and
  contradictory-stage rejection. Found and repaired
  [OW-2026-013](../findings/OW-2026-013.md), a missing Polygon address-case rule.
- `OathAtmosphere/Scanner/OathWalletConnectThorchainViews.swift` (417 lines):
  immutable request presentation, original document visibility, exact signed
  minimum, estimated fees/prices, destination details and public copying,
  progress-stage mapping, bounded polling and cancellation/memo-identity guards.
  UI layout, scene lifecycle, real biometrics and providers were not executed.
- `OathWalletConnectCallDetails.swift` (343 lines): complete read of raw data
  navigation, all-command expanded detail, swap summary, numeric/raw-unit
  fallbacks, metadata bounds and cancellation checks. Its mixed-operation primary
  summary question remains open, so this component also retains partial status.

## Additional partial traces and unresolved question

`OathWalletConnectEVMViews.swift` was read at 1–140 and 175–330, focusing on request
identity, approval metadata and the primary transaction summary; the remainder
is not covered by this increment. `OathWalletConnectService.swift:960–1015`
revalidates quoted destination addresses, binds immutable requests to pending
operations and rejects stale approval edits. Its earlier whole-file disposition
is retained, with this additional narrower trace appended. Activity detail at
78–120 demonstrates how swap progress is loaded. The THORChain client transport
and other ledger methods were inspected in part, not fully dispositioned here.

The primary EVM swap summary presents route inputs/outputs and native conversions,
while generic transfer and balance-check commands appear in the expanded call
details. The decoded model retains those commands, but the route-only summary
can omit them. An adversarial mixed batch's complete approval presentation and
whether the surrounding warnings sufficiently communicate every wallet debit
remain unresolved. This is a review lead, not yet a confirmed exploit or fixed
finding; it must not be silently counted as closed by the Polygon regression.

## Tests and limits

Whole-file test reads: `WalletConnectCallDetailsTests.swift`,
`WalletConnectSwapReviewTests.swift`, `ThorchainSwapReviewTests.swift`,
`ThorchainEVMSwapReviewTests.swift`, `ThorchainSwapProgressTests.swift`, and the
new `ThorchainSwapDestinationTests.swift`. They cover independently encoded ABI
fixtures, malformed offsets/truncation, immutable bytes, route direction,
unsupported memo/quote forms, false delivery and refund claims, and destination
identity controls. Existing opt-in public-network cases remain disabled.

The new paired test invokes the real decoder with synthetic observations and
network-denied processes; it does not copy the matching implementation. The
public EIP-55 vector is a known address-format example, not a wallet credential.
It demonstrates the Polygon defect and preserved identity checks. Broader host
results and the generic iOS build are separately source-pinned in the evidence.

No swap transaction, public-network quote, provider truth check, simulator,
physical device or App Store action was performed. A decoded intent is not a
transaction simulation or proof of contract behavior. Dependency and protocol
review gaps remain visible in the overall ledger.
