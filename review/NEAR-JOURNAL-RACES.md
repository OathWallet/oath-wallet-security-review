# NEAR journal concurrency and terminal receipts

Build 104 checkpoint 12. Application source is pinned to
`5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`. This review uses production
SQLite/GRDB code and synthetic Ed25519 signatures. No chain transaction is sent.

## Source dispositions

The complete `NearSend.swift`, `OathNearSendModel.swift` and
`NearSendJournalTests.swift` files were read. Their exact hashes and read ranges
are in the [source binding](../evidence/5.0.2-build104/near-journal-races/source-binding.json).
They are byte-identical to the immutable build-104 baseline. The two production
files receive **partial** dispositions. The existing six-method test file is
reviewed as test code; this does not close the implementation's broader scope.

The journal validates mainnet, account/wallet ownership, asset identity and
amount/recipient binding before reserving a sender. It checks other pending
native sends and WalletConnect submissions inside its database write, including
duplicate imports of the same account. Signature persistence verifies the plan
and signature before inserting transaction/activity rows and changing send state.
Settlement verifies the stored signature again. Unknown outcomes do not settle;
accepted acknowledgements record submission without changing terminal state.
Confirmed/failed outcomes require fee and block data, and expiry cannot replace
a fee-consuming failure. These checks depend on the upstream client establishing
receipt validity; the journal alone is not a blockchain verifier.

The send model invalidates a generation on cancellation. Quote and submission
callbacks check generation and task cancellation before updating presentation.
The surrounding `OathSendFlow` source explicitly calls `near.cancel()` when
leaving review, losing permission to use the wallet, or disappearing. Thus the
model's unlocked check cannot be assessed separately from those callbacks.
The flow was consulted for that integration only, not newly marked fully reviewed.
Actual SwiftUI lifecycle delivery, OS authentication and the full service/model
combination remain outside these database tests.

## Test scope

The runner selects the six existing journal tests plus three new methods:

1. Eight two-task races release both requests through a shared barrier and attempt
   to reserve the same sender in two imported wallets. Exactly one reservation
   must succeed; one must report busy. SQLite must retain exactly one plan, one
   queued send and one untouched draft. The test does not prescribe a winner or
   assert that all possible schedules were explored.
2. Confirmed, failed and expired journals are reopened through a new database
   instance. Repeated late accepted/unknown replies must preserve state, failure,
   fees, height, timestamps, refresh/status counts and the original signed bytes.
   Lookup from the other wallet must remain empty. Reopening a connection is not
   process-crash or power-loss simulation.
3. Nine malformed receipt variants test hash, missing/negative fees, block bounds,
   and forbidden acknowledgement/expiry fields. Rejection must leave the signed
   journal and related transaction fields/counts unchanged. This is not exhaustive
   malformed-input fuzzing or proof of provider authenticity.

A separate scratch mutation bypasses only the sender-reservation predicate.
The expected failing methods are the new simultaneous-reservation test and the
existing cross-wallet reservation and unknown-broadcast reservation tests. The
original checkout remains unchanged. All processes run with networking denied.

## Reproduction

Use a clean checkout of the exact app source pin, Python 3.11 or newer and macOS
with Swift 6.4. The dependency resolver may download public packages at build time;
the test executables are separately denied network access. Use fresh paths:

```sh
python3 scripts/near-journal-races.py wallet scratch/control evidence/local/control
python3 scripts/near-journal-races.py wallet scratch/mutant evidence/local/mutant --mutant
```

No simulation of funded sends, real provider, application UI, simulator, physical
device or App Store operation is included. Passing host tests do not prove all
storage errors, process interruptions, authorization interleavings or multisig
activation integration. The full wallet review remains incomplete.

## Recorded results

All nine selected production-source methods pass locally. The scratch mutation
produces exactly the three expected failures and six passing controls. All 368
audit-helper tests pass; the changed files and expanded new evidence pass secret
scanning. Exact tool versions, durations, case logs and source hashes are retained
in the [manifest](../evidence/5.0.2-build104/near-journal-races/manifest.json).
No new production defect was confirmed by this selection. No new generic iOS
build was needed because application source did not change.

At preparation time, the preceding [lifecycle workflow](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41617104807)
was running and [activation workflow](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41618881396)
was queued. This checkpoint does not claim their outcomes or a hosted journal pass.
