# NEAR multisig activation and bootstrap authority

Build 104 checkpoint 11. App source:
`5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`. No production change or new
confirmed application defect is claimed. The full wallet audit remains open.

## Source trace

The complete `OathNearSendService.swift` and `OathNearMultisigSetup.swift` files
were read. Their bytes equal the immutable build-104 baseline. Both now have
**partial** review dispositions, with exact hashes/read ranges in the
[source binding](../evidence/5.0.2-build104/near-multisig-activation/source-binding.json).
This is source review, not UI execution.

The setup service obtains the wallet's validated policy and NEAR account,
reconciles pending signed/broadcast sends, and suppresses a new setup quote
while queued/signed/broadcast work exists for that account. The shared submission
path reserves and preflights the exact plan during authentication, journals the
signature before broadcasting, and preserves signed work after a transport error.
The app-lifetime service's in-flight set prevents reconciliation of the same
send ID during its active submission. It is not a per-account concurrency lock;
the database reservation separately excludes overlapping sender work.

The setup model checks unlocked/loading/sending state around refresh, checks
cancellation after the provider result, and clears stale quotes before loading.
Activation starts an app-lifetime submission and retains pending state while
reconciliation runs. Passcode retry and cancellation have distinct paths. The
screen displays setup funding and fees and only exposes activation while it has
a quote, is unlocked and is active. These observations do not prove visual
layout, OS authentication, every lifecycle interleaving or persistence behavior.

Supporting excerpts in `OathWalletVault.signNearSend`, `NearSend.swift` and
`SendReconciliation.swift` were traced: signing is bound to the exact queued
wallet/account/asset/plan and rechecks authorization across suspensions; the
journal verifies the signature before saving; recovery decodes and verifies the
stored bytes and retries them unchanged. This checkpoint does not newly mark
those entire supporting files reviewed. Previously reviewed recovery-material
adapters were reread without extending their dependency coverage.

## Synthetic-provider activation tests

Six host XCTest methods exercise the actual package client and crypto code:

- Absent and zero-balance bootstrap/deployed accounts return a funding requirement
  and no actionable plan. The expected storage reserve and fee arithmetic are
  independently calculated from fixture constants and the pinned artifact size.
- Funded bootstrap and deployed states yield separate deploy and secure plans.
  Each plan signs one transaction using the bootstrap key. Only a configuration
  without that full-access key is reported configured with no next plan.
- Wrong bootstrap identity, restricted bootstrap permission, duplicate bootstrap
  entries and exhausted nonces are rejected in both pre-deploy and deployed states.
- Preflight rejects a changed phase, nonce, increased cost or insufficient funds
  for both activation stages instead of silently replacing the reviewed plan.
- A held account-state reply released after task cancellation cannot produce an
  activation plan or trigger a broadcast.
- Deployment and bootstrap removal each submit their original signed bytes and
  reconcile after JSON reconstruction with a new empty client cache. The
  synthetic provider advances the state explicitly; the next setup is read only
  after the prior transaction has a validated final receipt.

These tests do **not** execute the contract or simulate its action effects. They
exercise provider-response handling and stage gating. A synthetic final receipt
is not a blockchain proof. Local host tool versions and all case logs are retained
in the [evidence manifest](../evidence/5.0.2-build104/near-multisig-activation/manifest.json).

## Sensitivity and remaining scope

A separate scratch mutation removes only the bootstrap-public-key equality
condition in the pre-deploy branch. The unexpected-authority test must fail;
five controls must retain their passing results. The production checkout is
unchanged and every executed source hash is recorded. This is a deliberate
negative control, not an application patch.

Full service/model/database integration, real biometric/passcode flows, chain
execution, bootstrap-removal atomicity on-chain, all cancellation interleavings,
and shipped-WASM reproduction remain outstanding. Tests do not promote partial
source dispositions to complete. No live provider, funded transaction, simulator,
physical device or App Store operation is involved.

## Reproduction

Use a clean public checkout at the exact pin, macOS/Xcode with Swift 6.4 and
Python 3.11 or newer. Use fresh scratch/output paths. Compilation may resolve
public dependencies; each test process is denied network access.

```sh
python3 scripts/near-multisig-activation.py wallet scratch/control evidence/local/control
python3 scripts/near-multisig-activation.py wallet scratch/mutant evidence/local/mutant --mutant
python3 -m unittest discover -s tests -p test_near_multisig_activation.py
```

The separate audit workflow pins action revisions, Python, app source and the
Xcode/Swift requirement. It has read-only permissions, no deployment secrets,
no outside-contribution trigger and durable failure artifacts. Hosted results
will be reported separately from the local test evidence.

## Recorded result

The final local control passes all six methods. The mutation passes five and
fails exactly the bootstrap-authority method. All 366 audit-helper tests pass;
the expanded evidence and new test sources pass the secret scan. Equivalent
initial successful runs are retained in the archive before a whitespace-only
driver cleanup; final results bind to the published driver hash.
The preceding lifecycle workflow [41617104807](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41617104807)
had started but had no final result when this checkpoint was prepared. Its
completion is not inferred from the local pass.
