# NEAR multisig boundaries and upstream provenance

Application source: `5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`.
Upstream: `near/core-contracts` at `1b0436c96379c63aee7d2429c6d5d24019031ab8`.
This is an incremental, incomplete review. No new application defect was
confirmed by the checks below.

## Application source trace

The complete `NearMultisig.swift` and `NearMultisigClient.swift` files were read.
Their hashes are unchanged from the immutable build-104 baseline. Both receive
**partial** dispositions, with the unresolved work below retained.

The policy restricts member count, key size, uniqueness, sorting and quorum;
the bootstrap public key must differ from all members. Deployment and removal
of the bootstrap full-access key are distinct stages. Configuration checks
bind the deployed code hash, membership, threshold, every restricted key's
receiver and method list, and the absence of unexpected full-access keys.

Signing reconstructs every transaction and binds each part's public key,
nonce, complete bytes, signature and hash. Transfer submission proceeds one
part at a time. Proposal receipts must return the chosen request ID before any
confirmation is released. The on-chain request payload is compared with the
approved intent before confirmations. Recovery reuses signed bytes; an absent
receipt is not treated as proof that a transaction did not execute. Expiry
requires an unused nonce. Final receipt caching is bounded.

## Tests actually run

Ten existing production-package XCTest methods passed on the macOS host,
with network access denied during discovery and execution; none was skipped.
They cover setup/secure/transfer signing across quorum sizes, invalid policies,
missing/duplicate/foreign keys, intent or part-order changes, token storage and
exact amounts, artifact digest and bootstrap generation, changed contract or
permissions, request-payload mismatch, returned-ID mismatch, and pending status.
These are existing tests with synthetic providers, not ten newly discovered
bugs, an independent contract execution, or a complete state-machine matrix.

[Case logs and source bindings](../evidence/5.0.2-build104/near-multisig/manifest.json).

## Upstream artifact and implementation

All four bundled copies match the pinned upstream commit byte-for-byte: the
WASM artifact, Rust source, MIT license and Apache license. WASM SHA-256 is
`f3f9ee3e5e29d020dc73f581ff1490c03dff875ed01327dfebbe666724930a76`.
This establishes artifact provenance, **not a verified source-to-binary rebuild**.
The upstream build script uses an unpinned `stable` Rust toolchain.

The 878-line Rust file, including its unit tests, was read, along with the
integration test, manifest, build script and README. The trace covers membership
checks, per-member request limits, cooldown deletion, duplicate confirmations,
quorum execution, key permissions and request removal. The upstream contract
also exposes quorum-authorized membership, code and permission changes that the
app does not expose. The README's callback description is not proof of runtime
behavior; the implementation returns promises and removes requests at execution.
The allowlist names `add_and_confirm_request` while the exported helper is named
`add_request_and_confirm`; the app uses separate `add_request` and `confirm`
calls, so this mismatch was not demonstrated to break the app's transfer path.
Membership-change interactions with already collected confirmations remain an
open review question, not a confirmed vulnerability.

The locked upstream test attempt failed before executing contract tests. An
initial offline attempt encountered a non-directory default Cargo cache. The
second used dedicated cache and build directories, but dependency compilation
failed in `wasmer-runtime-core-near` and `librocksdb-sys` with Rust/Cargo 1.96.1.
Both original logs are retained. No dependencies were upgraded to manufacture
a passing result. A compatible contract runtime and reproducible WASM build
remain outstanding. The lock inventory includes development dependencies and
does not claim that every listed crate ships in the artifact.

## Reproduce

Use the pinned macOS/Xcode/Python toolchain from the audit workflow. Builds may
fetch public dependencies; test execution is network-denied.

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach 5d91d1e4dfd36c56031c7a8fb1ee305446dc54de
git clone https://github.com/near/core-contracts.git near-contract
git -C near-contract checkout --detach 1b0436c96379c63aee7d2429c6d5d24019031ab8
python3 scripts/near_contract_provenance.py wallet near-contract evidence/provenance.json
python3 scripts/near-multisig-boundaries.py wallet scratch evidence/host
```

## Remaining scope

Required follow-up includes independent multisig transaction vectors, full
staged submission/restart and cancellation matrices, upstream contract runtime
and dependency review, membership-change semantics, and the source-to-WASM
build relationship. A passing app test does not close any of these gaps.
No app code changed in this checkpoint. No new iOS build was needed for these
audit-only additions; checkpoint 5's build retains its exact source pin.
No simulator, physical device, funded transaction or App Store operation occurred.

The first audit-helper run detected a stale published compiler ledger after the
canonical dispositions were updated (348 passes, one reporting assertion failure).
The compiler join was regenerated at its canonical output path; the original
failed run is preserved separately from the retest. This is audit bookkeeping,
not an application failure.
