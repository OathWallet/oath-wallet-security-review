# Backup file boundaries — build 104 checkpoint 24

The whole-wallet audit remains incomplete. This is a current-source retest of
the existing OW-2026-051 and OW-2026-052 repairs, not a new application fix.
The tested public 5.0.2 (104) source is
`c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`. Historical results retain their pins.

## Source review

CloudDrive.swift (216 lines) and CloudRestore.swift (224 lines) were read in
full. The review follows account identity and generation checks, reset barriers,
bounded file reads, exclusive file publication, upload acknowledgements,
metadata scoping, download cancellation and discovery. Both receive **partial**
dispositions: actual iCloud identity changes, metadata callback lifetime and
File Provider behavior have not been validated end to end.

Package.swift (12 lines) receives a reviewed disposition for its manifest only:
one library, one test target, Swift 6 mode, platform minima, a local diagnostics
dependency and no manifest-declared plugin, binary or remote dependency. This
does not promote the implementation or transitive dependency to reviewed.

[Hashes and exact read ranges](../evidence/5.0.2-build104/cloud-file-recheck/source-binding.json)
match the frozen build-104 inventory. Existing fixture code was inspected for
the experiment; passing package tests do not mark all package files reviewed.

## Real before/after execution

Fresh disposable checkouts and distinct native SwiftPM build directories are
used for historical `c7acd23bb139864a40273f405d18b479589d2b20`, current regression
replay and the pristine current package. All test execution denies network.

The same three regression methods test:

- Cached regular-file metadata followed by replacement of the final entry with
  a symlink. The old reader accepts the unrelated synthetic sentinel; the
  current reader rejects it using descriptor-based validation and O_NOFOLLOW.
- A dangling symlink at the destination. The old writer replaces it; the
  current writer returns a conflict and preserves the directory entry.
- An exclusive competing creator between the missing-file check and publication.
  The old writer overwrites its bytes; the current exclusive rename preserves
  them and reports conflict.

The historical build records **three failing methods / six assertion failures**;
the current build records **three passing methods**. The third case adds an
explicit test-only interleaving hook immediately before publication in each
disposable source. It performs real filesystem operations with synthetic bytes;
it is deterministic fault injection, not evidence of a live iCloud race. Patches
and original/compiled writer hashes are retained. All tracked source is restored.

Separately, a **pristine current package** with no hook or added fixture passes
all **64 discovered XCTest methods plus one Swift Testing reset-barrier test**.
Coverage includes encrypted round trips, wrong-password/tamper rejection, bounded
documents, backup batching, restore cancellation/timeouts, file races, upload
scope and reset rejection. This is the existing package suite, not exhaustive
adversarial coverage. No tests were skipped. The three compiled executable
hashes are distinct, and every retained log is checksum-verified.

[Archive and manifest](../evidence/5.0.2-build104/cloud-file-recheck/manifest.json) ·
[OW-2026-051](../findings/OW-2026-051.md) ·
[OW-2026-052](../findings/OW-2026-052.md).

## Reproduce

Use Xcode 27.1 and Python, with fresh scratch/output paths:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-backup-source
git -C /tmp/oath-backup-source checkout --detach c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
python3 scripts/cloud-file-recheck.py /tmp/oath-backup-source /tmp/oath-backup-replay /tmp/oath-backup-results
python3 -m unittest discover -s tests -p test_cloud_file_recheck.py
```

The audit workflow pins actions, Python, Xcode and application commits. It has
read-only permissions, no deployment credentials and no outside-PR execution.
Local execution is complete; a GitHub replay is reported separately when its
downloaded evidence has been verified.

## Remaining limits

The reader protects the final directory entry; ancestor-directory replacement
is not established safe by these tests. Filesystem results apply to this macOS
host, not every iCloud File Provider or volume. Observation stop/publish races,
account switching during live transfers, crash/power-loss durability and full
application restoration remain open. The package README contains an older
version label and is not used as current build evidence.

No new confirmed defect or application source change is claimed. No new generic
iOS build was performed; checkpoint 19 retains the build evidence for this
unchanged app commit. No simulator, physical device, live cloud transfer, real
wallet secret or App Store Connect operation was used. This remains a
maintainer-commissioned, Codex-led review, not independent certification.

## Evidence validation and earlier hosted replay

The first helper-suite run rejected a documentation-ledger edit because it
would replace historical build-103 dispositions with current hashes. The
historical ledger is preserved; new reads live in the current inventory and
source-binding record. The failed helper log is retained separately. This was
an audit bookkeeping correction, not an application defect or failed app test.

The preceding [Stellar provider GitHub replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41752223483)
completed successfully at audit commit
`742c27d43ef42f626210756e1ca633aa2448a117`: twelve methods passed, and the
deliberate authorization mutation produced its one expected assertion failure.
The downloaded artifact digest, all report/log hashes, pinned fixture/driver
hashes and distinct executable hashes were verified.
[Receipt](../evidence/5.0.2-build104/hosted-stellar-provider/verification.json).

All 424 audit helper tests pass after that bookkeeping correction. The
completion gate still reports 16,916 outstanding review/validation items,
not vulnerabilities. The compiler-input ledger records 227 reviewed,
178 partially reviewed, 1,473 outstanding, 460 generated/verified and 20
requiring a generated-source trace. A new package-manifest disposition is
outside that direct compiler-input count.
