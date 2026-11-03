# Wallet removal, pending journals and interrupted persistence

OW-2026-062 fixed omission of pending Connect rows from removal preflight.
The next experiment confirms a distinct time-of-check/time-of-use problem:
another writer can insert a pending row after preflight. The durable reservation
repair is documented in [OW-2026-063](../findings/OW-2026-063.md).

## Test boundaries

- Paired fixture: actual encrypted vault, imported-key XRP signing/verifying,
  real SQLite journal and retention path. A gated in-memory credential store
  controls the write boundary. HD profiles and unrelated services retain the
  inherited host substitutes; no broadcast or WalletConnect relay is used.
- Interrupted recovery: 30 checks spanning passcode, synthetic biometrics and
  device-key access, before and after the encrypted commit. A SQLite trigger
  deliberately rejects lifecycle metadata writes for the post-commit scenarios.
  Cold vault/database instances reconcile retained state and release the fence.
- Database package: actual signed-XRP reservation ordering, unrelated wallets,
  group rollback, duplicate reservations, stale token cleanup, restart/reset,
  upgrade preservation and a schema-only pending insert/update matrix for
  ordinary sends and seven Connect journal tables.
- Migration fixtures must register the same SQLite metadata helper as the app.
  The first new upgrade fixture omitted it and failed. That setup failure is
  retained separately from the application race and its before/after tests.

## Reproduction

Use a clean source checkout and the exact commits in the evidence manifest:

```sh
git -C /path/to/oath-wallet checkout --detach 82ea45249ae40e5ab0be39d671fbfc96b6e43069
python3 scripts/connect-removal-race.py /path/to/oath-wallet .work/race-build .work/race/before --commit 82ea45249ae40e5ab0be39d671fbfc96b6e43069 --before
```

Run the same command against the pinned final repair without `--before`, then
with `--recovery` for the separate 30-case restart fixture. The script clones the
selected source and changes only the host launch wrapper to build first and run
the resulting binary with networking denied. It records the original/executed
harness hashes, test fixture hash, source revision, log hash and each case name.
It requires the exact expected four failures before and none after; zero selected
tests, renamed/missing cases and an incorrect process exit fail validation.

The hosted workflow separately builds the exact final app in unsigned iOS
Release configuration. It has read-only permissions, pinned actions, no release
credentials and no App Store job. Local compilation, host checks and hosted
results are reported separately.

## Remaining scope

This closes the reproduced overlap between new pending journal insertion and
authorized removal. It does not complete every asynchronous signing/account
read/lock sequence, full Connect service integration, OS credential behavior,
UI flow or live transaction recovery. Existing partial coverage dispositions
remain partial. Exact baseline and repaired revisions stay distinct.

## Supplemental source read

The 137-line `OathWalletRemovalModel.swift` was reread in full and is unchanged
between baseline, reproduction and repair. It binds removal IDs and recently
deleted membership to the action, creates a grant only after authorization,
rejects stale authorization generations, cancels grants by identity, and gives
confirmed mutation ownership to the session. The last-wallet path requires the
additional confirmation for retained deleted wallets. Navigation follows a
successful session result; failed writes keep the error notice. The existing
lifecycle harness exercises model cancellation, wrong PIN, confirmation,
duplicate confirmation and failed writes. Native-alert presentation timing is
not established by these host checks. The earlier file disposition is retained;
this supplemental read does not promote other files or add a UI pass.

## Source revisions and retained test corrections

Final repair: `b1f1b120947062aec871cb7fdc4439e88042cda3`. Production code is
identical to `f75ed392064e38883598ec37884456f25a472826`; only an unrelated Aptos
host assertion changed afterward. The broad lifecycle (144), reset (37),
authentication (158), biometric fallback (123) and protected-startup (28) checks
retain their exact f75 source pin. The 158 authentication checks appear twice
in the output summary and are counted only once.

The first full database run failed the newly added upgrade fixture because it
had not registered the production SQLite metadata helper. That setup is fixed.
The next full run passed that method but missed an asynchronous Aptos diagnostic:
it assumed a 100 ms delay guaranteed delivery. An unchanged isolated rerun passed.
The fixture now waits up to five seconds for its specific newly emitted event;
absence still fails. This changes test synchronization, not production diagnostics.
Both failures and the isolated rerun remain in the evidence.

An initial scanner invocation used an absolute target outside the app directory,
so all 432 existing relative ignore fingerprints failed to match. Normalizing
them matched the existing, unchanged reviewed exceptions exactly. The final
scan runs from the checkout with `gitleaks dir .`; the public validator also
checks the exception file hashes. No new exception was introduced.

## Final results

[PR #77](https://github.com/devdasx/oath-wallet/pull/77) merges the source repair.
The final pin passes 23 race checks, 30 recovery checks, 748 database tests
(72 explicit skips) and 119 diagnostics tests (two skips). Public-source and
secret scanning and diagnostic coverage pass. Generic unsigned iOS Release
compilation succeeds in 10.50 seconds using an existing isolated build cache;
this is not a clean-from-empty or runtime result. All 315 audit-helper tests pass.

[Durable manifest and logs](../evidence/5.0.1-build103/connect-removal-race/manifest.json)
include hashes of original and sanitized log bytes. The final source and merged
application/test files are identical; only intervening website files differ.
The new [hosted workflow](../.github/workflows/connect-removal-race.yml) is a
separate replay and compilation check; a configured or started job is not yet
a verified hosted result.

The previous delayed-authentication workflow
[41577528851](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41577528851)
completed successfully. Downloaded archive size/digest, exact source/fixture/
harness identities, log hashes and 38-case normal/mutant outcomes matched local
evidence. Its [receipt](../evidence/5.0.1-build103/ci-retests/connect-removal-auth-github.json)
and original archive accompany checkpoint 21. This supersedes checkpoint 20's
running snapshot without changing the older evidence.
