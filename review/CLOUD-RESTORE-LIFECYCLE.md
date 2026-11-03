# Cloud restore lifecycle and backup queue follow-up

Four full source reads cover the restore model, restore content/password view,
backup service and backup database operations. Their bytes match both the
build 103 baseline and tested commit `a904515793b087289140e4411924f030b3fe61ff`.
[Exact hashes and ranges](../evidence/5.0.1-build103/restore-lifecycle/source.json).
All four dispositions remain partial: full cloud, cryptographic, database and UI
behavior is not established by this source review or isolated model test.

The restore model checks generation, cancellation and attempt identity across
download, decryption, account verification and local-save completion. Discovery
account failure stops pending work and clears the selection. Wrong-password
errors replace the input-view identity, and the password form clears its local
string before submission and on disappearance. The model's discovery timeout
and OS lifecycle behavior were source-read, not runtime-tested here.

Twenty-two checks exercise the unchanged production model with controlled
synthetic boundaries. They cover duplicate requests, current progress, successful
save, prescribed wrong-password errors, account changes, canceled read errors,
late local-save completion and discovery invalidation. A deliberately removed
error-path ownership guard causes exactly three failures. This confirms that the
checks detect those stale-state updates; it is not a newly discovered defect.
[Reproduce and inspect limits](../fixtures/cloud-restore-lifecycle/README.md).

Additional source tracing in the tested app followed `OathWalletSession` lines
1205–1208 and 1268–1332, and `OathWalletVault` lines 1593–1630 and 1804–1846.
The session forwards cancellation into wallet work; vault operations check the
authentication generation before the encrypted commit and between subsequent
database steps. A commit already completed before cancellation is not rolled
back. Session recovery reconciles the actual selection after an interrupted SQL
or presentation step. These excerpts do not constitute a full new review of the
large session/vault files or a tested storage-failure matrix.

The backup service owns queued ciphertext uploads separately from foreground
preparation. Generation checks and account identity delimit late upload events.
Database updates match backup identity and enabled status, and confirmed uploads
cannot be downgraded by an older callback. The queue retains its own recovery
obligations; this follow-up does not claim new live-cloud or durable-write tests.

The current package reader/writer implementations were also inspected in light
of the earlier OW-2026-051/052 fixes. Their source differs from the historical
baseline, so this inspection does not promote that baseline's package coverage.
Ancestor-directory races, live iCloud behavior and source-to-platform guarantees
remain separately scoped limitations. No additional confirmed application defect
was established in this follow-up. No app source or App Store build was changed.
