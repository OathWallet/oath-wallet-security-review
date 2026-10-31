# TON serialization and signing review

Source: `a65601b78f86e33ebae08a754035d69c1f5f5e43`. This is a bounded
source review and host-test increment, not a completed TON or wallet audit.

## Files read and security boundaries

- `TonAmount.swift`: fixed 120-bit storage, decimal/hex parsing, comparison,
  carry/borrow and Codable handling. Public arithmetic operators have
  preconditions; callers must establish nonnegative subtraction and no overflow.
  `TonSendPlan.validate` establishes those bounds for the traced send path.
- `TonCell.swift`: cell size, reference count, depth, BOC length/count, reference
  direction, padding, CRC and hashing checks. Serialization deduplicates by hash.
  Parsing deliberately normalizes representations; it does not reject every
  unused index-table value or unreachable cell. Round trips alone are not an
  independent TON protocol oracle. Cryptographic hash collision resistance and
  Foundation/CryptoKit internals were not re-proven.
- `TonSendPlan.swift`: wallet/address/key agreement, network-specific multisig
  identity, fee reserve bounds, native and Jetton amounts, expiration and memo
  bounds. Remaining-balance arithmetic requires a validated plan. Internal
  builders do not constitute a separate authorization boundary.
- `TonSendCrypto.swift`: pinned V4R2 code-cell hash, state-init identity, signing
  mode, transaction/body binding, wrong-key rejection and verification by
  reconstructing exact bytes. This read does not audit the TVM contract's
  implementation or CryptoKit's Ed25519 implementation.
- `TonMultisig.swift`: sorted distinct signer identities, 2–7 signer limit,
  threshold, distinct network wallet IDs, exact pinned code/state checks,
  bounded dictionary reads, replay-state handling and signature-index binding.
  The encoder's observed production call uses width 8 and enumerated owner
  indices. Its internal API is not advertised as accepting arbitrary widths.
  Contract source-to-cell provenance remains outstanding.
- `TonSendProof.swift`: raw transaction/message hash agreement, bounded graph
  traversal, source/destination links, delivery and fee overflow checks. A raw
  cell's hash agreeing with an indexer's supplied hash is **not** a consensus
  inclusion proof. Account state, execution-success fields, timestamps and fees
  still depend on providers. No new provider-honesty guarantee is claimed.
- `TonSendClient.swift`: cancellation propagation, serialized/paced requests,
  network-genesis checks, wallet ownership, token ownership/metadata checks,
  quote/preflight, uncertain submission and pinned-block expiry recovery.
  The optional not-found request is the only path returning nil; ordinary
  node/simulation force unwraps do not alone demonstrate a crash. This review
  does not prove provider state authenticity or all network cancellation races.
- `TonModels.swift`: canonical raw/friendly addresses, checksums, workchain
  encoding, bounded base64, exact numeric strings, stack-address checks and
  metadata normalization. `TonJSON` aliases `SolanaJSON`; its `integer` accessor
  is unsigned, so the token-decimal upper-bound check does not admit negative
  values. Only that accessor was inspected here, not the entire JSON file.
- `WalletConnectTon.swift`: accepted methods/networks, bounded messages and
  payloads, checked total amounts, state-init/address agreement, reconstructed
  persisted request validation, exact signed-byte verification, signing-domain
  separation and proof payloads. Domain strings originate in the surrounding
  session flow, whose complete UI/authentication trace remains separate work.
- `WalletConnectTonProof.swift`: requested output order/count/values, partial
  graph status, bounced/skipped actions, checked fee accumulation and wallet-only
  fee reserves. The provider trust limitation above also applies here.
- `TonMultisigTests.swift`, `Tools/GenerateTonSendVectors.cjs`, and
  `Tools/CheckTonMultisig.swift`: existing vector, malformed-policy, recovery,
  authorization and backup harness logic was read. The first part of
  `TonSendTests.swift` was read; that whole test file remains partially reviewed.
  Existing upstream-produced vectors are not a fresh execution of the upstream
  contract compiler or an independent audit of that dependency.

No new exploitable defect was confirmed in this increment. Potential concerns
were not promoted to findings merely because code contains a force unwrap or
precondition. This statement is limited to the reads and tests above.

## New production-code properties

`scripts/ton-properties.py` creates an isolated Swift test package that depends
on the pinned **production OathAnkr module**, using `@testable import` for its
internal codecs. It neither substitutes codecs nor edits application sources.
Environment variables enabling live tests or exports are not forwarded.

- 1,004 120-bit amount vectors use Python's arbitrary-precision integer
  arithmetic as an independent arithmetic oracle. Parsing, representation,
  subtraction, serialization and boundary rejection are checked.
- Bit widths 0–64 cover zero, maximum and seeded values; invalid widths and
  overflow values must fail.
- 256 generated cell graphs cover empty, partial-byte and maximum-size cells.
  4,096 seeded byte mutations produced 2,559 accepted, reserialized inputs and
  1,537 rejected inputs. Acceptance of a different valid cell is expected.
- Cell size/reference/depth/byte-size limits, all truncations of the depth-128
  fixture and self/out-of-range references are rejected.
- Dictionary subsets of sizes 1–256 must retain identities and values; leaf
  limits, duplicate keys and malformed widths fail. 64-bit replay-key boundaries
  include zero, the high bit and UInt64.max.

Five XCTest cases passed on the Mac. The final run took 12.48 seconds including
an incremental build; test execution took about 7 seconds. This is not a phone
performance measurement or exhaustive fuzzing. Seed: `0x4f415448544f4e31`.
The runner forces the exact remote revisions from the reviewed package lockfile.
The fixed seed, generated oracle, logs, dependencies and hashes are retained in
`evidence/ton-properties`.

The first harness run's test cases passed but the result parser incorrectly
reported zero because it expected the legacy XCTest name format. That failed
harness result is retained under `initial`. The parser now accepts the two
explicit formats and rejects empty, duplicate, skipped-only or failing runs.
Three helper tests cover that reporting boundary and the deterministic oracle.
The final mutation test also separates parse rejection from a failure to
serialize an accepted cell, avoiding a swallowed test failure.

## Remaining scope

No simulator, physical device, actual peer, blockchain request or transaction was
used. These tests do not establish full TON smart-contract correctness, all
provider failure modes, live inclusion/replay behavior, all UI authorization
paths, dependency provenance or side-channel resistance. Existing source fixes
and findings remain unchanged. The whole-wallet review remains incomplete.

## Application authorization and recovery increment

The next read follows TON into `OathTonWallet`, `OathTonMultisig`,
`OathTonSendService`, `OathTonSendModel`, `OathSendDiagnostics`, the database's
`TonSend` and `WalletConnectTonJournal`, and cloud backup's `TonMultisigRecovery`.
The three corresponding journal/backup test files and
`Tools/CheckTonSendAuthorization.swift` were read as well. Exact file hashes are
in the coverage ledger. Only relevant portions of `OathWalletVault` and
`Tools/CheckMultiWallet.py` were inspected here; their other portions remain gaps.

- Wallet/account/network identity and public-key/address agreement precede TON
  signing. Imported-key and mnemonic paths remain distinct. Multisig recovery
  validates threshold/key structure; cryptographic key agreement occurs in the
  application. Structural backup validation alone does not prove ownership.
- The app-lifetime send service excludes an actively submitted send from its
  status checker, commits signed bytes before broadcast, distinguishes an
  acknowledgement from uncertain delivery and keeps pending recovery durable.
  A returned unknown outcome is not a claimed successful blockchain transfer.
- The UI model uses generation and cancellation checks for quote/authentication
  work. The database binds requests to accounts/assets, verifies journaled
  signatures, excludes conflicting pending work and preserves monotonic receipt
  handling. Shared preparation joins reservation and preflight; authentication
  and cancellation still gate signing afterward.
- Existing `Data` reset calls are not proof that every compiler/runtime copy of
  sensitive material has been erased. Hardware Keychain/biometric behavior and
  UI lifecycle execution were not tested by these host adapters.

The new `scripts/ton-authorization.py` uses the existing host harness with a new
entry point. It compiles the production vault, journal and imported-key TON
signer, while retaining the original synthetic biometric, HD and network
adapters. It **does not execute the complete app send service or its UI**.
Remote dependencies are forced to the exact revisions in the reviewed database
package lockfile. The temporary harness adaptation and fixture are public.

All **19 assertions passed**, including the existing wrong-PIN, biometric
fallback, cross-wallet, read-barrier and stale-authorization checks. New checks
hold preparation unfinished, then lock/reopen or cancel before releasing it;
no signed payload may be journaled. Preparation errors propagate, a mismatched
asset fails, and fresh authorization subsequently signs and verifies correctly.
Controlled continuations, not timing sleeps, govern those preparation races.
The pinned run took 148.60 seconds including compilation. Its log, dependency
lock and fixture hash are under `evidence/ton-authorization/pinned`; the initial
run is retained separately. No funds, wallet secrets, device or blockchain was
used. These checks do not establish every chain's authorization correctness.
