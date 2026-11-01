# Permission discovery, presentation and readback review

Target: `8f5c27c030fdd85e1d5c3c18d9da8aa92ac04c79` (4.1.15, build 100).
This increment follows the [batch authorization review](PERMISSION-BATCH-REVIEW.md).
File reads, host tests and iOS compilation have separate evidence boundaries.

## Production source read

- `Packages/OathAnkr/Sources/OathAnkr/PermissionDiscovery.swift`: whole file.
  Traced network/owner validation, EVM event candidates, removed-log rejection,
  cursor-loop and page bounds, response-byte limits, fresh on-chain rechecks,
  partial coverage and cancellation. TRON uses bounded pages and current
  allowances. Candidate caps can be exceeded by the final bounded page; no
  unbounded loop or arbitrary-signing path was established. A provider can omit
  candidates; neither this review nor the UI proves discovery completeness.
- `Packages/OathDatabase/Sources/OathDatabase/Permissions.swift`: whole file.
  Read journal/history/scans, owner/account/wallet binding, bounded history and
  scan sizes, status writes and tracking cleanup. Found and repaired
  [OW-2026-012](../findings/OW-2026-012.md). Account/crypto implementations called
  here retain their own dispositions.
- `OathAtmosphere/Permissions/OathPermissionsModel.swift`: whole file.
  Traced selected-wallet generations, cached scans, bounded concurrent identity
  and network reads, refresh admission and stale-result rejection. The unguarded
  `reloadHistory` helper has no caller in this pinned tree; its presence alone
  is not a confirmed stale-wallet defect. Runtime scheduling remains untested.
- `OathPermissionReview.swift`: whole file. Traced immutable permission input,
  cancellation around quotes, scoped vault signing, fee and confirmation copy,
  history observation and public-address copying. No reachable wrong-wallet
  signature was established. Display labels drawn from the mutable shared model
  still depend on the enclosing navigation lifetime; no UI proof is claimed.
- `OathPermissionContractPage.swift`: whole file. Input/network validation,
  busy-state restrictions, manual lookup, wallet identity checks around saving,
  and stale model-update guards were read. Identity labels do not grant signing
  permission. Live token identity and provider correctness were not checked.
- `OathPermissionsPage.swift`: whole file. Reviewed wallet selection, scoped
  tasks, immutable batch selection, history observation, verified-removal
  filtering, watch-only restrictions and retry/navigation paths. The relation
  between batch state and history explains OW-2026-012's possible presentation
  consequence. No screenshot, accessibility or device lifecycle check occurred.
- `OathAtmosphere/Send/OathSendStatusTracking.swift`: whole file. Traced the
  application worker registry/lifecycle, scoped pending/confirmed readback,
  background expiration and stop behavior. OS scheduling was source-read only.
- `Packages/OathDatabase/Sources/OathDatabase/SendStatusTracking.swift`: whole
  file. Reviewed eligibility, persisted leases, owner restart, bounded workers,
  flight-ID exclusion, epochs, retry deadlines and atomic lease completion.
  The single worker avoids concurrent checks for one send. Therefore the
  duplicate API regression does not establish a normal-app callback race.

## Test and fixture source read

Whole-file reads cover `PermissionTests.swift`, `PermissionBatchExecutorTests.swift`,
`PermissionReviewSelectionTests.swift`, `PermissionCheckInputTests.swift`,
`PermissionPreparationTests.swift`, `PermissionPublicTests.swift`, and
`PermissionReadOnlyLiveTests.swift` in OathAnkr; `PermissionBatchTests.swift`,
`PermissionPersistenceTests.swift`, and the new
`PermissionReadbackIdempotencyTests.swift` in OathDatabase;
`SendStatusTrackingTests.swift` (all 441 lines, including lease exclusion,
restart, cancellation, migration/index preservation and deadline observation); and
`Tools/CheckPermissionBatchAuthorization.swift`.

The older persistence test checked that a late callback preserved history but
did not assert batch consistency. The new fixture tests both records before
reconciliation, plus restart, reorganization, job cleanup and wallet isolation.
Tests with provider/testnet/loopback environment opt-ins remain skipped when
not enabled. An inspected test file is not evidence that its optional test ran.

`Tools/PreparePermissionLocalFixture.cjs` and
`Tools/PreparePermissionDelegationFixture.cjs` were read completely. They prepare
synthetic Ganache/Anvil contracts on loopback; they were not executed here.
Their external module path has no verified adjacent lockfile in this environment,
so clean-checkout fixture recreation and contract equivalence remain gaps.

## Evidence boundaries

The paired readback test runs at the public database API with production SQL,
imported-key signing and journals. Each case process denies network access.
Baseline and fix use the same fixture; original failing logs are retained.
Broader database/networking suites explicitly report skips. Results obtained on
`da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b` retain that source pin and do not count
as final-target validation. Current-target results are separately recorded.

These file dispositions mean the listed source was read, not that dependencies,
providers, deployed contracts, iOS rendering or every race have been proven safe.
No additional confirmed finding beyond OW-2026-012 is claimed in this increment.
No simulator, physical device, funded transaction or App Store operation was used.
