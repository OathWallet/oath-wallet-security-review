# NEAR named-account, provider and request boundaries

Read and tested source: `0614556b993f85808b13e3a69984ce36050a8dfe`.
The three reviewed files are byte-identical at the build-104 baseline and
PR81's merge. The exact source hashes and read ranges accompany this report.

## Source trace

All lines of `NearSendClient.swift`, `NearSendPlan.swift` and
`WalletConnectNear.swift` were read. Each receives a partial disposition.

- The client checks the configured network before using an endpoint. Account,
  access-key and contract queries must return the requested block hash. Named
  accounts use a query for the selected public key; ordinary signing requires
  FullAccess. The multisignature branch delegates policy and member permission
  checking to separate code that is not closed by this review.
- Quotes preserve native/token units, reserve storage, bound provider costs,
  reject invalid recipients/metadata, and check the final plan. Preflight
  refreshes account/key/fees without changing the approved plan. Nonce changes
  and increased costs require another approval rather than silent mutation.
- Submission verifies the signature and plan, then sends the original bytes.
  Recovery may replay already-authorized bytes while protocol-valid; it does
  not create a new signature. Expiry needs a block-height and unused-nonce check.
  Receipt processing binds sender/key/nonce/hash, traverses the receipt graph,
  and distinguishes the result chain from refund receipts.
- WalletConnect parsing bounds transaction count, total bytes, actions and
  per-action fields. It rejects duplicate JSON keys through the shared parser,
  unsupported actions, trailing bytes, wrong owners and non-increasing batches.
  Signing binds the reviewed request, key and 120-second consent lifetime.
  Review resolves transaction block hashes, checks access permissions, nonce
  bounds, fees and available funds before returning an approval model.

These checks rely on provider responses. Matching chain labels and block hashes
are not independent cryptographic proof of chain state. A consistently malicious
provider, endpoint changes, named-account key rotation and all multisignature
stages remain separate review obligations. Synthesized Codable restoration,
UI presentation, durable journal concurrency and full upstream implementations
are not established by this source read or test selection.

## Reproducible host evidence

Twenty-four existing production-package XCTest methods pass with zero failures
or skips: 14 `NearSendBoundaryTests`, seven `WalletConnectNearTests` and three
`WalletConnectNearReviewTests`. Each method runs in its own process and retains
its log and checksum. Both test discovery and execution run with networking
denied. Compilation may resolve public dependencies before the denied-network
test step. The separate Swift Testing selection has zero matching methods;
the reported 24 are actual XCTest passes, not that empty selection.

The tests use injected synthetic transports, public deterministic test keys and
existing SDK fixtures. This checkpoint does not generate or independently
revalidate those upstream vectors. It exercises provider errors, restricted
permissions, block/nonce/fee changes, exact atomic amounts, storage reserve,
same-byte retry, malformed request buffers, signing ownership, access grants
and finality transitions. No new application defect was confirmed by this run.

From a clean public application checkout at the exact tested commit:

```sh
python3 scripts/near-provider-boundaries.py /path/to/wallet /path/to/scratch /path/to/evidence
```

The driver pins the source, clears inherited provider/live-test flags, checks
the exact 24 method identities, rejects skips/duplicates/empty selections and
verifies all case-log hashes. It leaves tracked application source unchanged.
Tool versions, initial compilation, formal replay and source hashes are retained
in [the evidence manifest](../evidence/5.0.2-build104/near-provider-boundaries/manifest.json).
No simulator, device, blockchain provider or App Store operation was performed.

## Hosted replay

[Run 41603474540](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41603474540) completed successfully at audit commit `592d1520c44fe60debe8d613d3fe64c07eb3aa82`, testing application commit `0614556b993f85808b13e3a69984ce36050a8dfe`. The downloaded archive digest, 33 receipt-file hashes, all 24 method identities and case-log hashes, and executed driver hash were verified. [Archived receipts](../evidence/5.0.2-build104/hosted-near-provider/manifest.json). This closes the hosted replay requirement for this selection only.
