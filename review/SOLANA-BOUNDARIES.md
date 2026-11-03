# Solana signing and parsing review — bounded increment

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Source: `a65601b78f86e33ebae08a754035d69c1f5f5e43`.
This is source inspection plus explicitly scoped host evidence. It does not
complete the Solana or whole-wallet review.

## Complete files read

The ledger records exact hashes for `OathSolanaSigning`, `OathSolanaMultisig`,
`OathSolanaWallet`, `SolanaSendPlan`, `SolanaSendCrypto`, `SolanaMultisig`,
`SolanaMultisigCrypto`, `WalletConnectSolana` and `WalletConnectSolanaClient`.
The follow-up reads also cover `SolanaCurve`, `SolanaModels`, `SolanaSendClient`,
`SolanaMultisigClient` and application `OathSolanaSendService` in full.
Only the Solana signing methods in the much larger `OathWalletVault` were read
in this increment; the rest of that file remains under its existing disposition.

- Wallet/account/network and derived-address agreement gate application signing.
  Imported keys and mnemonic derivation use distinct paths. Multisig signing
  checks the stored policy against the reviewed plan and resolves precisely the
  needed signing members. Resetting mutable Data buffers does not establish that
  every runtime copy of a private value was erased.
- Native send plans validate bounded fee/rent inputs before performing derived
  arithmetic. Native amounts, SPL source totals, token fees, mint/program identity,
  memo size, payment references and expiration are checked. The public computed
  amount properties are not independent validation boundaries; callers still
  have to supply a validated plan.
- Locally constructed messages encode exact integer amounts and enforce the
  packet-size limit. Associated-account and multisig address derivation rejects
  on-curve hashes through `SolanaCurve`; that public-input curve implementation was subsequently read in full.
  Its limb arithmetic and modular square-root check are separate from CryptoKit
  private-key signing; no constant-time signing claim follows from this helper. Transfer references cannot become writable/signing accounts
  through another instruction.
- Squads serialization binds fixed policy, member roles, thresholds, addresses,
  transaction index and all stages. Signing requires the exact key set; verification
  reconstructs each message and verifies every signature. This does not establish
  deployed Squads program correctness, upgrade authority or source-to-program
  identity. The subsequent client trace checks owner/discriminator/threshold/index on
  returned program data, but still trusts RPC and does not verify deployed
  program bytecode against source.
- WalletConnect parses legacy and version-0 wire bytes with bounded canonical
  short-vector lengths, unique static keys, account-index limits and existing
  signature validation. It replaces only the selected signature slot; it does
  not rebuild the dApp's instructions or replace its blockhash. Text signing
  admits bounded printable UTF-8 and excludes transaction-header byte values
  supported by this parser. This is not a semantic approval of arbitrary dApp
  program instructions.
- Lookup-table resolution and simulation are cluster-bound. The review exposes
  partial writable-account inspection; native/token changes depend on RPC state
  and simulation honesty. Durable-nonce checks bind current nonce bytes and the
  authority. Simulation success is neither a consensus proof nor a guarantee of
  eventual transaction effects. Request consent UI and all service races still
  require their own trace.

No new exploitable vulnerability was confirmed in these source reads. That
statement is limited to this work; passing tests and a reviewed-file marker do
not establish absence of defects.

## Reproducible additional tests

`scripts/solana-properties.py` compiles the production OathAnkr package at its
pinned dependency revisions, using the existing independently generated legacy,
versioned-lookup and partial-signature fixtures. Its new fixture adds 528 Python
big-integer Base58 oracles, every truncation of those three transaction inputs,
noncanonical length cases, signature-slot preservation and 2,048 seeded byte
mutations. Accepted mutations must retain every byte outside the chosen signature
slot and pass production signature verification. Rejected mutations are counted
only during parsing; later assertion or signing failures are never swallowed.

The test is bounded and deterministic, not exhaustive fuzzing or an independent
cryptographic implementation. There are no blockchain calls, simulator runs,
physical-device operations, real credentials or funded transactions.

Observed result: all four host cases passed on the pinned source. Of 2,048
mutations, 703 parsed and satisfied the signing/preservation invariants; 1,345
were rejected during parsing. Runtime was 3.25 seconds, with 127.26 seconds
including compilation. Seed: `0x4f415448534f4c31`. Exact dependencies, fixture
hashes, oracle, log and result are under `evidence/solana-properties/initial`.
The two new result-parser/oracle tests pass as part of 38 audit-tool unit tests.

## Provider, journal and replay follow-up

The complete client reads trace genesis checks, bounded response bodies and
request concurrency, minimum-slot guards, SPL ownership/extension policy, exact
integer fee arithmetic, simulation, signed-byte receipts and archival expiry.
Only explicit retryable transport/RPC errors fall back. Diagnostic simulation
messages use a classification allowlist rather than provider logs. Multisig payer
selection excludes executable/non-system/data accounts; quote selection is frozen
in the signed plan. Preparation-stage replay verifies exact transaction bytes;
approvals and transfer belong to the final stage. Provider honesty, program
upgrades and a real cluster remain separate unverified boundaries.

The application service reserves local state and runs preflight inside the
vault's authorization callback, checks cancellation, persists the signature before
broadcast, and returns an acknowledged outcome even if later local bookkeeping
fails. Draft/queued failures cancel; signed/broadcast failures retain recovery
bytes. Its per-send `flights` set excludes background checking during submission.
The database test-fixture race did not use that service coordination, and the
source trace does not show the same confirmation/broadcast race through this
service. Cross-process coordination and every UI authorization path are not
established by this read.

`SolanaJSON` preserves u64/i64 before falling back to Decimal; identity decoding
is byte-bounded Base58. This generic RPC model has no explicit recursive-depth
limit itself; it relies on the Foundation decoder and the client's body limit.
A dedicated resource-exhaustion test is still needed before asserting its full
malformed-provider robustness. This is an outstanding test boundary, not a
confirmed exploit or a passing result.

## Independent field-arithmetic follow-up

A fifth production-module test compares `SolanaCurve.isPoint` with 1,038
Python modular-arithmetic vectors: boundary encodings around 2^255-19,
512 seeded 255-bit inputs, and both sign bits for every y coordinate. The oracle
uses the Edwards equation, modular inversion and Euler's criterion rather than
the Swift implementation's 16-limb multiplication and square-root loop. It tests
curve-point existence, not subgroup membership or signing-key validity; the
helper is used only to exclude on-curve program-derived addresses.

All five cases passed in the extended run (131.32 seconds including compilation).
The initial four-case evidence is retained unchanged. The additional oracle test
brings the audit-tool suite to 39 passing cases. Exact extended evidence is in
`evidence/solana-properties/curve-extension`; this is still bounded input coverage,
not a proof over all encodings or an independent Solana consensus implementation.

After the test-fixture repair was merged, the same five cases were rerun on
`90b5b28a6f3852319a24d74143863f2b57837c4d`: all passed (86.06 seconds
including compilation). Production Solana files are unchanged between these
pins, but the separate `test-fixed-target` evidence retains the exact new source.
