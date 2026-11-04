# Backup settings lifecycle — build 104 checkpoint 25

The whole-wallet audit remains incomplete. This checkpoint reviews public
5.0.2 (104) application source at
`c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`. No new confirmed application defect
or application source change is claimed.

## Source scope

OathAllWalletBackupPage.swift (199 lines), OathCloudBackupSection.swift (180
lines), and OathCloudBackupService.swift (232 lines) were read in full. The
first two previously outstanding files receive partial dispositions. The
already partially reviewed service gains this additional evidence.
[Hashes and read ranges](../evidence/5.0.2-build104/backup-settings/source-binding.json)
match the frozen build-104 inventory. Historical build-103 dispositions are
unchanged.

The views gate backup creation on unlocked/changing-wallet state and show
queued work separately from confirmed upload. The models own preparation tasks
and invalidate operation identity when canceled. The service checks generation
and account identity around encryption and queue preparation, then resumes
committed ciphertext separately from the settings page. Reset waits for secret
preparation and invalidates cloud locations. Source tracing of those service
branches is not a test of their live-cloud execution.

## Production-model tests

The helper extracts the complete production OathCloudBackupModel class unchanged,
omitting only the SwiftUI view and replacing framework imports with Foundation
and Observation. A same-file test extension exposes its private task handle so
assertions can await the entire production catch/defer path. No production
statement is changed in the passing run. The compiled model, source hash,
fixture hash, executable hash, toolchain and logs are retained.

Synthetic database, cloud service, diagnostics and vault boundaries never touch
real storage or iCloud. Service continuations deliberately ignore cancellation
until the test releases them. There are no arbitrary sleeps: each test waits for
entry, starts a new operation, releases the old operation, awaits its full task,
then checks state while the new operation remains held.

All **52 single-wallet model checks pass**:

- Late success and failure from each of create, disable and retry cannot clear a
  newer create's progress/task or alter its error state. The newer service call
  enters once and completes normally when released.
- Current success/failure for all three operations remains visible and finishes
  the task, ensuring that suppression is limited to obsolete callbacks.
- A duplicate create does not start another service call while preparing.
- Cancellation clears presentation immediately; its later failure remains hidden.

The existing unchanged all-wallet model fixture also passes **15 checks** at
this same current app commit. It exercises controlled old successful/failed
record reads versus a new batch and legitimate current read failure. This is a
current retest of [OW-2026-059](../findings/OW-2026-059.md), not a new repair.
Earlier before/after evidence retains its historical source pins.

## Negative control

In a disposable extracted model only, remove the `finish` operation-identity
guard. Recompile and rerun the identical fixture. It yields **40 passing / 12
expected failing checks**: each old success/failure clears the newer progress
and task. Case identities, counts, normal nonzero exit and distinct executable
hashes are verified. This weakened model is not application source.

[Execution archive and manifest](../evidence/5.0.2-build104/backup-settings/manifest.json) ·
[Fixture](../fixtures/backup-settings/Checks.swift).

## Reproduce

Use Xcode 27.1 and Python with fresh scratch/output directories:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-settings-source
git -C /tmp/oath-settings-source checkout --detach c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
python3 scripts/backup-settings-review.py /tmp/oath-settings-source /tmp/oath-settings-work /tmp/oath-settings-results
python3 -m unittest discover -s tests -p test_backup_settings_review.py
```

The workflow pins source, actions, Python and Xcode, uses read-only permissions,
and contains no deployment secrets or outside-PR execution. Runtime networking
is denied. A new GitHub replay is separate from completed local results.

## Limits

The model test does not execute SwiftUI, production encryption, the durable
queue/database, account switching, metadata callback lifetime or live iCloud.
A stubbed service can prove model behavior across controlled awaits; it cannot
prove the service implementation itself. Actual sheet dismissal, observation
cancellation and simultaneous reset/disable/queue scheduling remain outstanding.
These bounded checks do not promote any implementation file to fully reviewed.

No new generic iOS build was performed: checkpoint 19 retains the unsigned
Release build for the unchanged app commit. No simulator, physical device,
funded transaction, real wallet credential or App Store Connect action was used.
This is a maintainer-commissioned, Codex-led review, not independent certification.

## Earlier GitHub backup replay

[Run 41753493347](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41753493347)
completed at audit commit `02f491149832c6ce8b62e25eb18dd7eef92f7f18`.
It reproduced three historical failing methods/six assertions, three current
passing methods, and the pristine package's 64 XCTest plus one Swift Testing
passes. Downloaded artifact, report, case-log, fixture/driver hashes and distinct
stage executables were verified. [Receipt](../evidence/5.0.2-build104/hosted-cloud-file-recheck/verification.json).

The completion gate remains open with 16,916 review/validation items, not
vulnerabilities. Direct compiler inputs now include 227 reviewed, 180 partially
reviewed, 1,471 outstanding, 460 generated/verified and 20 requiring trace.

All 430 audit helper tests pass, including six checks for the retained model
results, exact mutation, partial source scope, historical finding separation,
hosted backup receipt and execution boundaries.
