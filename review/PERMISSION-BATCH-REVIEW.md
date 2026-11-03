# Permission batch authorization and lifetime review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Target: `da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b` (4.1.15, build 100).
This is a source review plus bounded macOS host execution, not an iOS runtime,
provider or protocol-certification claim.

## Files read and questions answered

- `Packages/OathAnkr/Sources/OathAnkr/Permissions.swift`: reviewed the whole
  removal model, input parsing, numeric bounds and fixed ABI encoders. Inputs
  cannot supply arbitrary calldata. Permit2 nonce increments are bounded to
  uint48; Solana limits the token program IDs; TRON validates its control model.
  The called identity, crypto and control implementations retain their own
  separate dispositions. Contract semantics and deployed bytecode provenance
  are not established by this read.
- `PermissionBatchScope.swift`: complete read of validated plan factories and
  equality/fee-ceiling binding. Zero-amount native removal requirements remain.
  Synthesized decoding can bypass the initializer, but each signer constructs
  a freshly validated requested scope and matches the granted fields; no bypass
  was established in the traced path.
- `PermissionReviewSelection.swift`: complete read of immutable wallet/items,
  nonempty/unique/maximum-count presentation selection and allowance formatting.
- `PermissionPreparation.swift`: complete read of cancellation before/after
  preparation, chain/operation context and exclusions limited to unsigned
  insufficient-funds errors. The original error is returned; no signing occurs.
- `PermissionBatchExecutor.swift`: complete read of sequential processing,
  bounded busy deferral, per-item authorization and cancellation, finish/error
  handling. Authorization before execution alone does not cover suspension
  inside a signer; OW-2026-011 supplies that missing enforcement.
- `Packages/OathDatabase/Sources/OathDatabase/PermissionBatch.swift`: complete
  read of schema/foreign keys/reset guards, wallet/account binding, duplicate
  and payload limits, transaction boundaries, unfinished-only state writes,
  resource checks and signed-journal reconciliation. History pruning excludes
  active/submitted batches. The SQL journal is authoritative after interruption;
  no new bytes should be generated for a previously journaled item.
- `OathAtmosphere/Permissions/OathPermissionBatchCoordinator.swift`: complete
  read of job ownership, start failures, grant cleanup, fresh quotes, scope
  comparison, existing signed-byte check and error/reconciliation handling.
  UIKit background expiration cancels the job and releases the OS assertion;
  screen dismissal does not cancel already approved work. UIBackgroundTask
  behavior was source-reviewed, not executed on iOS in this increment.
- `OathPermissionService.swift`: complete read of discovery aggregation,
  optional identity lookups, cached-candidate rechecks, owner/network matching,
  removal-only quote dispatch, existing send-service dispatch and confirmed
  transaction rechecks. Provider failure retains partial/unknown coverage.
  Identity labels do not confer signing authority. Provider implementations,
  malicious-indexer completeness and live chain behavior are separate gaps.
- `OathPermissionBatchReview.swift`: complete source read of immutable selection,
  wallet/unlock guards, bounded four-worker preparation, fee summary,
  confirmation, fresh authentication and coordinator ownership. UI rendering,
  actor scheduling under scene changes, localization and real biometrics were
  not runtime-tested. No new defect beyond OW-2026-011 was established here.

## Partial files and reproduction

`OathWalletVault.swift` remains **partially reviewed**: grant creation,
consumption/end, the three signers and shared lock/authentication checks were
traced, not every method in this large actor. `Tools/CheckMultiWallet.py` remains
partial: the new mode and selected adapters were reviewed; tests replace some
platform/HD implementations and do not prove whole-app behavior. The new
`Tools/CheckPermissionBatchRaces.swift` was read completely for gate ordering,
public synthetic credentials, cleanup, actual signing/verifying, failure
classification and exact counts.

[OW-2026-011](../findings/OW-2026-011.md) records the confirmed defect, source
lines, fix, same-fixture results and limitations. The harness first rejects
replay while preparation is held, establishing that revocation occurs after
scope consumption. Controls cover valid grants, ending an unrelated UUID,
locking and cancellation. A fake monotonic grant clock isolates expiry from
transaction-plan age. Three repetitions each before/after deny network access.

Review dispositions are pinned to file hashes. Reading these files does not
mark called implementations, upstream crypto, providers, lifecycle UI or
unrelated source as reviewed. Whole-wallet completion remains outstanding.
