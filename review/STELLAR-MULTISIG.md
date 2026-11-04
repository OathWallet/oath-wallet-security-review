# Stellar multisignature policy and signing — build 104 checkpoint 22

The whole-wallet audit remains incomplete. This checkpoint reviews the public
5.0.2 (104) prerelease at `c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`.
No new confirmed defect or application implementation change is claimed.

## Source review and boundaries

`StellarMultisig.swift`, `OathStellarMultisigSetup.swift`, and
`OathStellarWallet.swift` were read in full. The review traces policy structure,
bootstrap/configured Horizon state, signing-key membership, signature ordering,
atomic signer installation, master-key disabling, wallet/account binding,
quote preparation and the setup screen's authorization handoff. The related
send service, plan/XDR implementation and recovery-material checks were also
inspected; this checkpoint does not replace their earlier dispositions.

[Exact source hashes and read ranges](../evidence/5.0.2-build104/stellar-multisig/source-binding.json).
The three newly examined files remain **partially reviewed**. Source inspection
of UI and wallet integration is distinct from the package host tests below.
No simulator, UI interaction or authentication lifecycle test was performed.

Two investigated concerns are not findings: reserve arithmetic is bounded by
provider-state limits before multiplication; decoded policies are validated by
the public plan/sign/verify path before use. The tests exercise the latter
boundary, including negative and extreme decoded threshold values. They do not
establish that every internal helper is safe when called outside its contract.

## Executed production tests

Six new test methods and four existing adjacent methods all pass in a fresh
checkout and native SwiftPM build. Every host test runs with network denied.
Synthetic repeated-byte keys are deliberately public fixtures, never funded
wallets. The fixture imports the production OathAnkr module.

- All **209** supported combinations of 2–20 signers and thresholds 1–N:
  valid states accepted; wrong account, lower/higher thresholds, missing or
  active master, foreign/duplicate signers, wrong weights/types rejected.
- Untouched bootstrap state: exactly one master at weight one and all three
  thresholds zero; altered state is rejected.
- Thirteen JSON-decoded policy changes: invalid threshold extremes, signer
  count/uniqueness/order/address and account binding cannot reach signing or
  validate an existing signed send.
- All 209 combinations sign and verify using exactly the required distinct
  keys; too few/many, duplicate, foreign and disabled-master keys are rejected.
- Thirteen forged signature/envelope variants plus four changed plan fields
  are rejected, including swapped signatures, wrong lengths, altered hash,
  extra bytes, network, recipient, sequence and amount.
- All 209 bootstrap configuration envelopes are decoded by pinned Soneso SDK
  3.12.0 (`b5dac0a6e8ff312d597c9a3b4269b03131d66e0d`). They contain N signer
  installations followed by one master-disable/three-threshold operation,
  with no operation source override or unrelated SetOptions fields. Only the
  bootstrap master can authorize configuration.
- Four existing methods retain 20 SDK vectors across five policies/four
  operation kinds, malformed-policy/signature checks, changed on-chain policy
  and wrong-network no-broadcast assertions using an in-memory transport.

This is bounded agreement with the pinned SDK, not a complete independent SDK
review or proof of live protocol execution. Production source remains unchanged.

[Fixture](../fixtures/stellar-multisig/StellarMultisigReviewTests.swift) ·
[Results, hashes and limits](../evidence/5.0.2-build104/stellar-multisig/manifest.json).

## Negative control

A disposable mutation changes exact threshold equality to less-than-or-equal.
The policy matrix produces **627 expected assertion failures**: each of three
thresholds across all 209 policies. The mutated copy is rebuilt before execution
and its tracked source is restored afterward. Passing and deliberately failing
runs have separate source/executable hashes and logs. This is a test-sensitivity
experiment, not a production defect or a repair claim.

## Reproduce

With Xcode 27.1 and Python, using fresh paths:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-stellar-source
git -C /tmp/oath-stellar-source checkout --detach c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
python3 scripts/stellar-multisig-review.py /tmp/oath-stellar-source /tmp/oath-multisig-replay /tmp/oath-multisig-results
python3 scripts/stellar-multisig-mutation.py /tmp/oath-multisig-replay /tmp/oath-multisig-results /tmp/oath-multisig-mutation
python3 -m unittest discover -s tests -p test_stellar_multisig_review.py
```

Dependency downloads occur only during build. The workflow pins actions,
source, SDK, Python and Xcode; repository access is read-only, and it has no
secrets, deployment step or pull-request execution on the dedicated runner.
The new workflow's status is separate from the local passing results.

## Earlier GitHub replays verified

The completed [timestamp repair replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41738980809)
reproduces three passes/three SIGTRAPs before the fix, six passes after it, and
40 adjacent passes. [Downloaded evidence](../evidence/5.0.2-build104/hosted-stellar-plan-timestamps/verification.json)
checks GitHub's artifact digest and every report/log hash.

The completed [persistence replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41740254836)
reproduces all 31 selected passes, with the live method excluded.
[Downloaded evidence](../evidence/5.0.2-build104/hosted-stellar-persistence/verification.json)
checks the artifact digest and report/log hashes. Historical local reports are
preserved rather than rewritten to pretend they already contained these runs.

All 410 audit helper tests pass, including six evidence checks for this checkpoint.
The changed review files and expanded new archives pass the redacted secret scan;
this scan does not cover the full Git history.

## Remaining work

The completion gate still reports **16,917 outstanding review/validation items**;
this is not a vulnerability count. The compiler-input ledger has 227 reviewed,
175 partially reviewed, 1,476 outstanding, 460 generated/verified and 20
generated inputs needing trace.

Outstanding work includes end-to-end setup/authentication lifecycle races,
Soroban multisignature simulation and authorization, malicious provider-state
combinations, runtime secret lifetimes, additional recovery/derivation paths,
reachable SDK internals and source-to-binary provenance. The new policy tests
cannot promote these areas to complete. This is a maintainer-commissioned,
Codex-led review, not independent certification or a zero-vulnerability claim.

No new generic iOS build is claimed for this audit-only checkpoint. Checkpoint
19 records the unsigned Release build of the identical application tree.
No simulator, device, live RPC, real secret, funded transaction or App Store
Connect operation was used.
