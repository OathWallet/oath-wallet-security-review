# Stellar saved-plan timestamps — build 104 checkpoint 19

This is a bounded source and regression review for Oath 5.0.2 (104)
prerelease. The complete wallet audit remains incomplete.

Before: `152e094f85f196479d2ab08856eaf3b0264cd6c1`.
Repair: `814596f8bb25a2c32ea25bba1fb036aee3303ca6`.

## Confirmed repair

[OW-2026-072](../findings/OW-2026-072.md) removes a trapping timestamp
conversion from structural validation of saved Stellar transactions. Three
isolated cases crash the old production implementation; all six methods pass
after repair. This is a public API and malformed saved-data robustness result,
not a demonstrated remotely triggerable exploit or loss of funds.

Normal quote creation uses local time. Reconciliation must be able to verify
old signed bytes, so disabling the quote's age limit is intentional. The fix
adds a checked conversion at that boundary without reinstating the age limit
or changing valid transactions. A persisted JSON round trip verifies against
the original signature and retains the same transaction bytes.

## Harness corrections and evidence boundaries

The first fixture did not compile because one throwing test expression lacked
`try`. It executed no tests. After correction, the initial baseline reproduced
three crashes. A shared SwiftPM build directory then reused the **identical
baseline test executable** while retesting the changed checkout. That attempt
is invalid as a source-to-executable binding and is not a failed repair result.
Its executable hashes, logs, driver and results remain in
[`attempts.zip`](../evidence/5.0.2-build104/stellar-plan-timestamps/attempts.zip).

The final driver requires a fresh build directory for every replay. Fresh
before/after builds produce different executable hashes and reproduce the
three-crashes-to-six-passes result. One restart also correctly refused an
untracked fixture overlay before compilation; it was retried from a clean
baseline checkout. [Attempt record](../evidence/5.0.2-build104/stellar-plan-timestamps/attempts.json).

Runtime networking is denied and the environment excludes all live-test
opt-ins. Keys and transaction data are synthetic. No simulator, physical
device, live provider, broadcast or App Store operation is included.

## Source coverage

Five complete baseline files were read and compared against the immutable
build-104 inventory; all retain **partial** review dispositions:

- `StellarSendPlan.swift`: persisted fields, structural and age validation,
  reserve/fee arithmetic, branch-specific amount and authorization rules.
- `StellarSendClient.swift`: response size/typed absence, account and network
  binding, ledger freshness, guarded reserve/sequence arithmetic, simulation,
  quote preparation, signed submission, reconciliation and WalletConnect
  review/submission. Reading these paths does not prove hostile-provider or
  cross-provider interleaving coverage.
- `StellarSend.swift`: plan JSON persistence, duplicate-account reservations,
  signature journaling, receipt validation, terminal-state preservation and
  balance-refresh scheduling. The timestamp fixture does not exercise a real
  database reopen; it exercises the decoded plan and production verifier.
- `SendReconciliation.swift`: stored-plan and signed-payload loading followed
  by exact verification and pending-send reconciliation. Its other chain
  adapters remain subject to their separate review scopes.
- `OathStellarSendService.swift`: local draft preparation, authorization handoff,
  durable signature recording, acknowledged-result preservation, cancellation
  handling and in-flight reconciliation exclusion. UI/runtime and concurrent
  authorization behavior are not established by the package tests here.

[Exact ranges and before/repair hashes](../evidence/5.0.2-build104/stellar-plan-timestamps/source-binding.json).
No file is marked fully reviewed because a scanner or test passes.

## Reproduction

Run from a clean audit checkout on the pinned macOS/Xcode toolchain:

```sh
python3 scripts/stellar-plan-timestamps.py /path/to/baseline /tmp/stellar-before /tmp/stellar-before-results --baseline --expected-commit 152e094f85f196479d2ab08856eaf3b0264cd6c1
python3 scripts/stellar-plan-timestamps.py /path/to/repair /tmp/stellar-after /tmp/stellar-after-results --expected-commit 814596f8bb25a2c32ea25bba1fb036aee3303ca6
python3 scripts/xdr-scale-regressions.py /tmp/stellar-after/source /tmp/stellar-after/build /tmp/stellar-adjacent-results --expected-commit 814596f8bb25a2c32ea25bba1fb036aee3303ca6
```

The dedicated workflow uses pinned sources, actions and tool versions, read-only
permissions, and no deployment secrets or outside pull-request execution.
Local and GitHub results are separate evidence.

## Additional validation

All 40 adjacent Stellar/Polkadot send, multisignature and WalletConnect methods
pass; seven live methods are explicitly excluded. Diagnostics execute 121
methods: 119 pass and two optional methods skip. Public-release validation,
diagnostics coverage and the application secret scan pass. Generic unsigned
iOS Release compilation succeeds and its product reports 5.0.2 (104).
The complete public merge tree matches the tested repair tree. All 394 audit
helper tests pass. The completion gate still reports 16,917 outstanding review
or validation items; this is not a count of vulnerabilities.

The first evidence-helper run also exposed an incorrectly adapted expected
count (50 instead of the actual 40 adjacent methods). Only the helper was
corrected; the application fixture and recorded production results are unchanged.

## Earlier hosted results

The [history restart replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41731731469)
reproduces one passing control, two assertion failures and one SIGTRAP before,
then four repaired passes and 22 adjacent passes. The
[Sui signing replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41734504160)
reproduces one passing control/two SIGTRAPs, then three repaired passes and 34
signing methods. Downloaded GitHub archive digests, result hashes, source pins
and contained log hashes were verified. These receipts supplement their
original checkpoints; the original results are unchanged.

The full helper run initially detected an altered inherited build-103
disposition entry. That historical entry was restored unchanged; the additional
partial read is recorded in the current inventory and source-binding ledger.
The original failing log and the successful rerun are both retained.

## Remaining review

Complete SDK operation semantics, source-to-binary provenance, app-level
authorization interleavings, corrupt-database recovery policy, every supported
chain and the complete dependency inventory remain open. This review does not
establish an independently certified audit, zero vulnerabilities or equivalence
with an installed App Store binary.
