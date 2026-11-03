# Pending Connect work and wallet removal

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

[OW-2026-062](../findings/OW-2026-062.md) records the confirmed behavior, severity,
app call-path trace and legacy cleanup exception. This is a bounded database
review, not a completed lifecycle or wallet audit.

## Reproduce from public source

On a compatible macOS/Xcode host, from this audit repository:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git .work/removal

git -C .work/removal checkout --detach 31178e42e40d67218c2b52eda0024a5b4224f376
python3 scripts/connect-removal.py .work/removal .work/removal-build .work/removal-results/before --phase before

git -C .work/removal checkout --detach 610f2fbcfa1b9a08bf9cfd9b439247324bf5366a
python3 scripts/connect-removal.py .work/removal .work/removal-build .work/removal-results/compatibility --phase compatibility

git -C .work/removal checkout --detach 0e91ce56f91ef56b3e45629967e01e449be0052f
python3 scripts/connect-removal.py .work/removal .work/removal-build .work/removal-results/after --phase after
```

The wrapper checks exact clean revisions, exact test identities, statuses and
process exits. It expects the original two methods and intermediate compatibility
method to fail; a green wrapper means those failures were reproduced, not hidden.
Logs retain the original nonzero test-process exit. Three helper tests ensure
missing, duplicate, skipped or wrong-result methods are rejected.

The first four test methods are unchanged from reproduction to final repair.
The fifth compatibility method is unchanged from its failing reproduction to
final repair. Signed XRP uses a real synthetic transaction and reopened database;
the seven-table matrix uses synthetic schema-valid rows, not valid transactions
for all chains. Full reset still hides pending recovery, rejects a late settlement,
erases the journal and rejects journal recreation for the erased wallet.

Local final validation uses Xcode 27.0 / Swift 6.4. The read-only pinned
[GitHub workflow](../.github/workflows/connect-removal.yml) uses Xcode 27.1;
its result is reported separately. No deployment credentials or App Store jobs.

[Manifest and retained logs](../evidence/5.0.1-build103/connect-removal/manifest.json)
include the original failures, intermediate repair, compatibility regression,
final validation, clean-checkout replay, source hashes and merge identity.
The complete source review and signing/removal race analysis remain unfinished.
