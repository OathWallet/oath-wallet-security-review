# Solana stake authority — checkpoint 38

Maintainer-commissioned, Codex-led review of public Oath Wallet **5.0.3 (105)**.
The whole-wallet review remains incomplete and is not independent certification.

## Finding and exact source

[OW-2026-077](../findings/OW-2026-077.md) is a **Medium misleading-authorization**
finding. Baseline `393c29cbae673f60f1df6ac9636af908ae789649` can present a stake
withdrawal-authority change as a fee-only transaction. Repair
`f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e` rejects the unsupported operation.
The focused [PR #117](https://github.com/OathWallet/oath-wallet/pull/117) is open and has not been merged. Its build receipt identifies the tested repair;
source availability is separate from Apple distribution.

The attack requires a connected malicious dApp, an account whose signing key
controls a stake account, and user approval/signing of the request. Solana stake
withdrawer authority can replace withdrawal and staking authority and, subject to
stake activation/lockup rules, withdraw funds. A transfer of this authority does
not itself need to change the connected wallet's SOL balance. The old review
inspects writable accounts but models only that native balance and SPL token
balances/delegations, so it silently omits stake control and stake-held SOL.
The UI then has no stake permission/withdrawal effect to display. Raw instructions
are separately accessible and general warnings exist; neither is evidence that
a dedicated stake warning was shown. This is not an authentication bypass.

The production service invokes the review both during request preparation and
again before signing. A rejection therefore stops the app's signing path; there
is no preparation fallback in the traced code. The repair rejects all direct
Stake Program instructions until a dedicated review is available. For other
programs, it rejects simulated stake account data/lamport/owner changes, creation
and closure. An unchanged stake account remains compatible. This intentionally
makes staking operations unavailable through the generic WalletConnect review;
it does not change wallet storage, signatures, ordinary SOL/SPL sends or backups.

The authoritative source reference is
[`solana-program/stake` at e64c0c3](https://github.com/solana-program/stake/tree/e64c0c3c3dfd22f88b9fdea29b4a65b804ae554a):
`interface/src/state.rs` defines `StakeStateV2`, `Meta` and `Authorized`;
`program/src/processor.rs` implements authority replacement and withdrawal.
The reference receipt records exact file hashes and reviewed ranges. This is
protocol-semantics review, not an audit of the entire stake program.

## Reproduce the actual application package

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e
python3 scripts/solana-stake-authority-review.py wallet .work/stake evidence/replay/stake
python3 -m unittest discover -s tests -p test_solana_stake_authority_review.py
```

Use the pinned audit release and its recorded macOS/Xcode toolchain. Scratch and
output directories must be new. Dependencies are locked. The driver builds two
fresh complete production packages, injects identical fixtures, hashes the source,
lockfile and executables, and runs methods in separate network-denied processes.
An unrelated failure, crash, timeout or skip cannot qualify as reproduction.

Nine new methods use ten independently generated `@solana/web3.js` 1.98.4 legacy
and version-zero transaction vectors. Both independent SDK signatures and
production signatures verify against the exact same message. Direct stake and
withdrawal instructions are SDK-generated; account state and the custom-program
CPI effects are injected synthetic responses. No validator was executed and no
custom program or funds were deployed.

## Local results

- **Before:** two controls pass; seven methods fail with **44 expected assertions**.
- **After:** all **67** selected Solana WalletConnect methods pass, zero fail and
  zero skip, including all nine new methods.
- **204.415 seconds** for the paired driver, including fresh builds of 109.458
  and 84.697 seconds. These are test durations, not app latency measurements.
- Covers staker/withdrawer replacement, three signing methods, legacy/v0 wires,
  direct no-op authority requests, CPI state changes, withdrawal, creation,
  closure and malformed account snapshots. The ordinary unchanged-stake control
  remains accepted. Existing Solana token/delegation, nonce, context, signature
  and buffer regressions remain in the selection.
- Diagnostics: **119 passed, two explicitly skipped**, no failures in the full
  suite; the isolated opt-in trace test passes separately with networking denied.
  The original skips are retained rather than relabeled as suite passes.
- Source-boundary, direct secret scan and diagnostics coverage checks pass.
- Unsigned generic iOS Release build: passed at the exact repair commit in **377.511 seconds**.

[Manifest](../evidence/5.0.3-build105/solana-stake-authority/manifest.json) ·
[Paired results](../evidence/5.0.3-build105/solana-stake-authority/runs.zip) ·
[Validation and exploratory evidence](../evidence/5.0.3-build105/solana-stake-authority/validation.zip) ·
[Source/range ledger](../evidence/5.0.3-build105/solana-stake-authority/source-binding.json).

The first exploratory fixture incorrectly required signature-byte equality
between CryptoKit and the SDK. Its 38 assertions comprise 28 stake-review
failures and ten invalid signature-equality expectations. Both signatures verify;
the corrected eight-method probe records only the 28 stake failures. The final
nine-method paired suite adds 16 malformed-snapshot cases and records the 44
expected failures above. The original logs, corrected eight-method fixture and final paired fixture are preserved. The initial erroneous fixture source was overwritten during correction; its original source bytes are not claimed preserved. A failed
npm installation caused by a pre-existing cache path is also retained; a fresh
isolated cache succeeded without changing user configuration.

The complete audit-helper suite passes **522 tests** in 11.663 seconds. The new
checkpoint and expanded evidence (3.93 MB) pass secret scanning. The completion
gate still reports **16,916 outstanding review items**, not vulnerabilities.

## Coverage, publication and remaining gaps

Seven hash-bound source/range dispositions are supplemental. The frozen inventory remains
unchanged. A passing test does not mark an entire file reviewed. This checkpoint
does not prove provider honesty, every intermediate CPI effect, full UI/lifecycle
integration, live chain execution or a source-to-App-Store-binary match. Other
arbitrary programs and Token-2022 extensions remain separate review areas.
Checkpoint 34's hosted backup-exclusion assertion remains failed and unresolved.
No claim extends automatically to later source commits.

Hosted replay: pending. No simulator, physical device, App Store operation or
other application was used. The repair is not claimed available in Apple's
currently distributed build.
