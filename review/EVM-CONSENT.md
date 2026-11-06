# EVM signing, consent and multisig — checkpoint 35

Maintainer-commissioned, Codex-led review of Oath Wallet **5.0.3 (105)** at
`32701474fefbed3840878e35f6111e8d494e1f02`. No new application vulnerability was
confirmed in this checkpoint. No application code was changed. The whole-wallet
review remains incomplete.

## Attack hypotheses and production trace

A malicious dApp supplies transaction fields and contract calldata. A modified
stored plan or signed envelope could substitute another recipient, chain, token,
amount or fee after consent. A multisig signature set could omit required owners
or substitute an unrecognized key. These are separate trust boundaries: altering
a stored envelope is fault injection, not proof of remote filesystem access.

Production EVM signing binds the plan to its wallet, account, chain, sender,
imported-key scope and derived address. The vault checks its queued record and
plan equality after authentication and preparation. Authentication/removal
generations and task cancellation are checked around awaited work. Safe signing
also checks the exact policy and executor. These application traces are source
inspection, not a complete runtime scheduling test.

The package validates unsigned fields, reconstructs the signed wire bytes,
recovers the signing address and verifies the transaction hash. EIP-155 and
EIP-1559 include the chain ID; the supported EIP-7702 operation only removes a
delegation. Safe transaction digests bind the chain, account, recipient, value,
calldata and Safe nonce. Threshold signatures must belong to distinct policy
owners in the expected order. Factory/singleton/proxy identity and empty
guard/module state are checked against provider responses. These checks do not
turn an RPC provider into a cryptographically verified light client.

WalletConnect parsing rejects unsupported/ambiguous fields and preserves explicit
fees and nonce. Approval edits bind the spender and contract while changing only
the approved amount. The consent view has unlimited-approval and unknown/raw-call
paths. Rendered wording and every interaction were not exercised here.

## Reproduce

Use a clean checkout of the pinned app, Python 3.14.7 and compatible macOS/Xcode:

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach 32701474fefbed3840878e35f6111e8d494e1f02
python3 scripts/evm-consent-review.py wallet .work/evm-consent evidence/replay/evm-consent
python3 -m unittest discover -s tests -p test_evm_consent_review.py
```

Scratch/output directories must be new. The driver builds complete production
packages with locked dependencies. Each selected test runs in its own process
with networking denied. Keys and addresses are deterministic synthetic fixtures.
No real accounts, provider, node or broadcast is used.

## Verified local results

Xcode 27.2 (27B52), Swift 6.4.2 and Python 3.14.7: **231.096 seconds**, including
two separate fresh builds.

- **28 production methods pass, zero fail, zero skip.** Six new methods and 22
  inherited EVM, WalletConnect and permission methods are selected explicitly.
  The optional live Safe-execution method is excluded and is not counted as a pass.
- 152 native/token and legacy/type-2 plans across 38 distinct chain IDs sign,
  verify and survive serialization. **5,624 cross-chain substitutions reject.**
- **1,064 structurally valid alterations** of recipients, amounts, senders,
  nonce, gas, fee and token contract reject against the original signature.
- **1,140 individual wire-byte changes/truncations**, plus four appended-byte
  cases, reject even with a recomputed transaction hash. This is a bounded corpus.
- All **119 supported Safe owner-count/threshold policies** for 2–15 owners
  pass native and token signing: 238 positive plans. Insufficient, duplicate and
  foreign owners, reversed signature ordering and changed Safe nonce reject.
- Delegation-removal signing is checked on all 38 configured chains, with 1,406
  cross-chain authorization substitutions and 38 changed-nonce substitutions
  rejected. This verifies local binding, not on-chain support/execution everywhere.
- A disposable build deliberately omits the signed-byte equality guard. Exactly
  four expected assertions fail in one method. This mutation is a test sensitivity
  control, **not a discovered production vulnerability or app before/after fix**.

[Manifest](../evidence/5.0.3-build105/evm-consent/manifest.json) ·
[Logs and results](../evidence/5.0.3-build105/evm-consent/runs.zip) ·
[Reviewed source snapshots](../evidence/5.0.3-build105/evm-consent/validation.zip) ·
[Source/range ledger](../evidence/5.0.3-build105/evm-consent/source-binding.json).

## Limits

Fifteen hash-bound source/range dispositions remain partial. Frozen inventory
counts do not change; test success does not imply manual review of every file.
All application lifecycle interleavings, full malicious-provider/persistence
matrices, Safe contract execution, actual chain behavior, UI runtime, cryptographic
dependency implementations and shipped-binary provenance remain separate work.
Package tests cannot establish iOS Keychain or full lock-screen behavior.

## Hosted verification

The [GitHub run](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42239926754)
completed successfully at audit commit `e993017f7bb4eb1da0be59a818d05c0f1ca74cc5`.
Its downloaded artifact has the same **28 passing production methods, zero skips**
and exactly four expected mutation-control assertions. The hosted driver took
**722.551 seconds**, including two fresh package builds. The terminal run/job
states, GitHub artifact digest, source/fixture/driver hashes, dependency locks,
every log and individual case result are checked by
`tests/test_hosted_evm_consent.py`.

[Downloaded artifact and receipt](../evidence/5.0.3-build105/hosted-evm-consent/verification.json).
The pinned, read-only hosted workflow has no deployment jobs or credentials. No new
generic iOS build was run for these audit-only additions; no app-build result is
claimed. No simulator, physical device or App Store operation was performed.
