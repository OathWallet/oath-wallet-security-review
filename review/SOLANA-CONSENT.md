# Solana WalletConnect delegation consent

This is a maintainer-commissioned, Codex-led review. The whole-wallet audit
remains incomplete; this checkpoint is not independent certification.

## Exact source and finding

OW-2026-073 records the omission reported by Ibnu. The vulnerable baseline is
the released 5.0.2 (104) source `7ffd0f449c3312d9fafd01eda59c6b9eb813f9ca`.
The existing repair is `7c79fe5bf89de44168fc9bc25e7e781d9051fdfe`. The retest
pins public 5.0.3 (105) source `247ac898168cc8f97be28398c69337f569fb5f96`.
No claim extends automatically to a later commit or to the App Store binary.

The old review model included fee, programs, balance changes and slot, but no
token permissions. The paired fixture holds all four constant and changes the
delegate in a simulated post-transaction token account. On the baseline the
two review values compare equal. On repaired source they differ. This validates
the missing consent information; it is not a local-validator execution or a
demonstration of transferred funds.

The repair preserves the signed wire message and existing authorization gates.
It reads permissions per account, avoiding aggregation of separate allowances
for accounts sharing one mint. Direct requests remain visible even when an
allowance already exists or is revoked later in the same transaction. Changes
made through an inner invocation are detected when they affect simulated final
account state. The UI includes spender, amount, before/requested/after state and
an unlimited warning. The service compares permissions again before signing.

## Source review disposition

[The source binding](../evidence/5.0.3-build105/solana-consent/source-binding.json)
records the exact hashes and line ranges read. The parser, permission decoder,
review client, display code and selected preparation/signing service paths are
**partially reviewed**. Passing tests do not promote entire files to reviewed.
The frozen build-104 inventory stays unchanged; these later-source dispositions
are an additive ledger. Static program indices are checked by the transaction
parser before the display accesses them; the suspected loaded-program-index
display issue was not confirmed.

Remaining scope includes full lifecycle/cancellation integration, SwiftUI
rendering and accessibility, provider honesty, all Token-2022 extensions,
arbitrary program effects beyond the presented balance/permission model, and
real validator behavior. Final account snapshots do not prove every intermediate
CPI effect. No claim is made that every possible instruction is semantically
understood, or that future execution must equal simulation.

## Reproducible paired execution

On macOS with the recorded compatible Xcode/Swift toolchain and Python 3.14:

```sh
git clone https://github.com/OathWallet/oath-wallet-security-review.git review
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach 247ac898168cc8f97be28398c69337f569fb5f96
cd review
python3 scripts/solana-consent-review.py ../wallet ../consent-build ../consent-results
python3 -m unittest discover -s tests -p test_solana_consent_review.py
```

Use an exact audit release tag for historical reproduction. Scratch/output
directories must not already exist. The script requires a clean pinned source
checkout, verifies the existing fixture byte-for-byte, verifies repair ancestry,
archives production packages at both pins and uses independent build folders.
SwiftPM dependencies are constrained by each recorded lockfile. Compilation can
download public dependencies; each test process runs with networking denied.
Test discovery stderr is kept separate from selectors.

The baseline is accepted only when exactly the expected assertion fails; a
compile error, crash, skip, timeout or unrelated failure is not reproduction.
After the repair, the same regression and all selected WalletConnectSolana
methods run in isolated host processes with a maximum of four concurrent jobs.
The fixture, production-source manifests, dependency lock, executable hashes,
toolchain, case logs, durations and exit codes are retained.

## Observed results

Local run: **one expected failure before; 36 passes after; zero skips**.
Elapsed driver time: **213.321 seconds**, including separate fresh compilation.
This is test duration, not a wallet performance measurement.

The passing methods cover direct/checked approvals on both token programs,
finite/zero/repeated/unlimited amounts, replacement and revocation, independent
same-mint accounts, simulated inner-invocation and lookup-address changes,
unknown token precision, malformed authority data, the writable-account cap,
permission-only consent changes, ordinary transfers, cluster identities, nonce
handling, signature preservation, preflight and batch boundaries.

[Local evidence manifest](../evidence/5.0.3-build105/solana-consent/manifest.json)
identifies the downloadable archives. The first attempt compiled but failed at
test discovery because a compiler warning interleaved with selector output.
**No test executed in that attempt.** Its sanitized logs remain in `attempt1.zip`;
it is excluded from the successful before/after evidence.

The audit workflow replays the exact pins without deployment credentials or
signing certificates. Hosted execution is reported separately when its artifact
has been downloaded and verified. No new generic iOS build, simulator run,
physical-device operation, application release or App Store upload is claimed
by this audit-only checkpoint.

## Earlier scanner checkpoint follow-up

[GitHub run 41755387724](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/41755387724) succeeded at audit commit `ac0529e016687be0ea35d75b524df5e9a76ec658`. Its original archive was downloaded and matched GitHub's SHA-256 digest; embedded result, source and case-log hashes were verified.
[Receipt](../evidence/5.0.2-build104/hosted-scanner-state/verification.json).
This closes the earlier hosted-evidence gap for that scanner checkpoint only.
