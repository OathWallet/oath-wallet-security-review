# EVM transaction review — scoped progress

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Reviewed source: `6124254d43ee7a98d4a364639671ccfc52155396` (4.1.15, build 100).
This increment repairs [OW-2026-009](../findings/OW-2026-009.md), a missing
response-size check. It is not a complete EVM, swap, permission or dApp audit.

## Source trace

- `EVMSendPlan.swift` validates canonical uint256 amounts, fee arithmetic,
  quote age, sender/recipient identity, nonce bounds, available balances and
  mutually exclusive call/removal/multisig modes. Pending reservations bind
  network and sender, prohibit overlapping nonce ranges, and reserve native
  costs across duplicate imports. EIP-7702 removal reserves two nonces.
- `EVMSendCrypto.swift` constructs native/ERC-20, EIP-155 and type-2/type-4
  payloads from the approved plan. Signing validates the plan and key owner;
  verification reconstructs exact bytes and hash, recovers the expected signer,
  and separately checks the EIP-7702 authorization. This trace does not replace
  upstream secp256k1/Keccak review or independent protocol-vector validation.
- `EVMSendClient.swift` binds RPC batches to chain identity, bounds gas/fees,
  validates quote inputs and pinned-block continuity, and simulates the final
  payload. The repaired standalone chain check now has the same size bound as
  a batch. A broadcast acknowledgment is distinct from receipt confirmation;
  recovery checks signed hash, sender, recipient, chain, nonce, calldata and fees.
  Inclusion/reorg checks and token Transfer logs remain provider-reported
  evidence, not independently verified consensus proofs.
- `OathEVMSendService.swift` validates wallet/account bindings, uses stable
  WalletConnect request IDs, reserves the plan, delegates authorization to the
  vault, checks cancellation, and journals exact signed bytes before broadcast.
  Its error path distinguishes an unsigned rejection from a committed signature
  that still belongs to the durable recovery worker. The separate authorization,
  permission, swap and WalletConnect lifecycle implementations remain boundaries.
- `OathDatabase/EVMSend.swift` checks account/asset identity when queueing,
  enforces sender-wide reservations, verifies exact signed bytes before journaling,
  and validates receipt state transitions. Balance refreshes discard a snapshot
  when the same send settled while its provider read was in flight. Database
  deletion concurrency, all shared transition helpers and runtime worker
  interactions are not declared complete by this file trace.
- `OathEVMSendModel.swift` uses generation checks and cancellation to reject
  stale quote/submission UI completions. Passcode and biometric failures retain
  their separate UI paths. This is source inspection, not a visual/runtime test.
- `EVMMultisigPolicy.swift` was read for sorted distinct owners, thresholds,
  executor separation, deterministic deployment data, EIP-712 domain binding,
  signature membership/order and exact outer-transaction verification. The Safe
  deployment bytecode, upstream contract implementation, and on-chain state
  checks in the separate multisig client remain outstanding review boundaries.

## Explicit remaining questions

`EVMSendCrypto.unsignedBytes` is also a public sizing helper used before full
quote validation. Its type-4 field encoder adds one to the nonce. The current
quote caller checks the delegation nonce bound before fee sizing, and signing
and verification validate it before encoding. No reachable app crash or
signing bypass was established here. Malformed direct calls to the public
helper and wider API precondition consistency remain an explicit review lead;
they are not covered by the response-size repair.

The network constants and exceptional finality/fee policies were read, but
this increment did not independently verify every chain's live protocol or
deployment identity. Signer-library provenance and broad parser property tests
remain separate coverage items. Reviewed file dispositions describe their own
control flow; they do not transitively mark called implementations reviewed.

## Evidence and limits

The new response-boundary test invokes the production RPC method through an
in-memory `AnkrTransport`. It supplies no credentials or real signed transaction.
The exact-limit controls prove that rejection is due to response size rather
than invalid JSON, HTTP status, response ID or chain identity. Before/after
processes run with networking denied and retain logs and binary/fixture hashes.

Broader results and actual toolchain versions are recorded under
[`evidence/evm-response-boundary`](../evidence/evm-response-boundary). The current
source pin and check statuses are machine-readable; historical runs are retained
under their original commits. No whole-wallet completion or App Store equivalence
claim follows from this increment.

## Completed checks on this exact source

- OathAnkr: 1,407 selected, 1,213 passed, 194 explicit skips, no failures.
  An explicit 12-class EVM/send/permission subset has 66 passes and five skips;
  those are included in the package totals, not extra tests. The existing
  EVMSendTests run 36 repository signing fixtures; their JavaScript vector
  generator was not rerun in this increment.
- OathDiagnostics: 118 passed, two explicit skips, no failures.
- App EVM authorization harness: 22 checks passed using the production vault,
  PIN handling and imported-key signer with a synthetic biometric store.
  This does not exercise real Face ID, HD derivation or the full iOS interface.
- Public-source/Gitleaks validation and diagnostic coverage passed.
- Generic unsigned iOS Release compilation passed in 167.79 seconds using an
  explicitly reused isolated build directory. The source change recompiled
  OathAnkr; this is not a fresh-from-empty build claim.
- 92 audit-helper tests passed. Workflow lint reports its existing unknown
  `xcode-27` label; filtering only that exact warning yields a pass. Both logs
  and an initial unsupported-linter-argument attempt are retained.

The new GitHub job reproduces the regression-only and fixed revisions separately,
with pinned actions, read-only permissions, and no deployment secrets. Fresh
GitHub execution remains pending; local passes do not establish a passing CI
matrix. No simulator, physical-device or App Store operation occurred.

## Follow-up: delegation nonce and Safe contract boundaries

The previously open direct-helper nonce lead is now reproduced and repaired
in [OW-2026-010](../findings/OW-2026-010.md). The original quote/signing caller
checks remain intact; the finding does not establish a reachable app exploit.
The [Safe cross-check](SAFE-CONTRACT-CROSSCHECK.md) extends source review into
the multisig client and selected pinned upstream contract semantics. The earlier
counts above remain historical results on their stated source, not new results.
