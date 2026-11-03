# Restore-model lifecycle host checks

From a clean public application checkout at
`a904515793b087289140e4411924f030b3fe61ff`:

```sh
python3 scripts/cloud-restore-lifecycle.py /path/to/oath-wallet /tmp/restore-checks
python3 scripts/cloud-restore-lifecycle.py /path/to/oath-wallet /tmp/restore-mutant --mutate-catch-guard
```

Run these commands in this review repository with Xcode's Swift 6 compiler on
macOS. No private credentials or network access are needed for the test execution.
The application checkout must have the exact commit and no uncommitted inputs.

The script copies the production `OathCloudRestoreModel.swift`, removing only
the two imports supplied by synthetic adapters. The model body is unchanged in
the production run. Its source bytes also match the build 103 baseline. The
compiler uses Swift 6 mode; the resulting host process has network access denied.

Continuation barriers deliberately hold downloads and local-save callbacks.
Failure processing and save return are observed before checking the model's
state. Bounded condition polling yields to the executor and fails on timeout;
there is no fixed sleep that assumes a callback already ran. Twenty-two named
checks cover selection, duplicate requests, progress, success, error mapping,
account changes and cancellation-resistant late completions.

The negative control removes one error-path generation/attempt/cancellation
guard from a temporary model copy. It must produce exactly three named failures
and nineteen passes. This is a deliberately broken test variant, **not a finding
against production source**. The application checkout is never modified.

Cloud account verification, discovery, downloads, cryptographic opening,
restored-wallet validation, diagnostics and local persistence are synthetic
boundaries. The password adapter only returns a prescribed error: this does not
test password encryption or validation. The fixture supplies invalid, nonsecret
bytes and does not contact iCloud, open a real database, use a real wallet, launch
UIKit or use a simulator/device. It does not test the 30-second discovery timeout,
all actor interleavings, OS suspension, full session/vault commit behavior or
memory erasure. Those remain separate obligations.

The initial passing run is retained alongside the final exact-case parser run
and deliberate mutation. The parser rejects missing, renamed, duplicate or
unexpected case results, incorrect summaries and unexpected process exits.
