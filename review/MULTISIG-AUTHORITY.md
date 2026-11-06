# Multisignature authority — checkpoint 37

Maintainer-commissioned, Codex-led review of Oath Wallet **5.0.3 (105)** at
`32701474fefbed3840878e35f6111e8d494e1f02`. No new application vulnerability was
confirmed and no application code was changed. The whole-wallet review remains
incomplete. Checkpoint 34's hosted storage assertion remains failed and unresolved.

## Attack hypotheses and production trace

An attacker who controls fewer keys than the configured threshold must not obtain
a valid wallet signature by duplicating a signer, changing a bitmap, changing the
persisted policy or substituting a different transaction. These are consequential
fund-control hypotheses; the tested production implementations reject the cases
below.

Aptos canonicalizes distinct public keys, binds its authentication address to the
threshold and keys, and verifies ascending unique signer indices, every Ed25519
signature and the exact transaction/authenticator bytes. Sui binds equal-weight
members and threshold to the address and rejects an incorrect signature count,
out-of-range or duplicate signer attribution, altered policy and transaction intent.
THORChain canonicalizes compressed public keys, verifies member signatures and
compares the complete protobuf transaction and hash against the approved plan.

Additional source traces cover Stellar atomic signer setup, application adapters,
fresh export authorization, wallet removal generations, imported-chain/address
checks, passphrase input identity and WalletConnect session/request ownership.
Sui's journal and reconciliation compare signed transaction bytes with the approved
plan. These are source/range reviews, not executed full-app race or relay tests.

## Reproduce

Use macOS with a compatible Xcode and Python 3.14.7:

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach 32701474fefbed3840878e35f6111e8d494e1f02
python3 scripts/multisig-authority-review.py wallet .work/multisig-authority evidence/replay/multisig-authority
python3 -m unittest discover -s tests -p test_multisig_authority_review.py
```

Scratch and output directories must be new. The driver builds complete production
packages with locked dependencies twice, then executes selected methods in isolated
processes with networking denied. Keys, transactions and accounts are synthetic.
No funded account, live provider, chain submission or production secret is used.

## Verified local results

Xcode 27.2 (27B52), Swift 6.4.2 and Python 3.14.7: **200.129 seconds**, including
two fresh package builds.

- **13 production methods pass, zero fail, zero skip:** six new methods, three
  existing Aptos, two Sui and two THORChain methods.
- **527 Aptos policies** cover every threshold for 2–32 members. Valid signatures
  pass; missing keys, reconstructed under-threshold authenticators, invalid indices,
  duplicated signers and changed transaction amounts reject.
- **54 Sui policies** cover every threshold for 2–10 members. Valid signatures pass;
  missing keys and 864 changed signer-bitmap bits reject. A separate enumeration
  evaluates every **65,536** bitmap value for a two-of-three signature: the one
  correct bitmap passes and all **65,535** others reject.
- Persisted Aptos/Sui policy fixtures reject invalid thresholds, duplicate keys,
  incorrect key lengths and noncanonical order. Valid round trips preserve identity.
- **27 THORChain policies** retain amount, sequence and wire binding: 54 altered
  plans and 108 changed serialized transactions with recomputed hashes reject.
- In a separate disposable build, removing only Sui's signature-count/threshold
  equality check causes exactly **three expected assertion failures in one method**.
  The cases retain a genuine signature and the complete original policy but omit
  required cosignatures. This is a test-sensitivity control, not an app defect or
  failed-before/passed-after application repair.

[Manifest](../evidence/5.0.3-build105/multisig-authority/manifest.json) ·
[Logs and results](../evidence/5.0.3-build105/multisig-authority/runs.zip) ·
[Source snapshots](../evidence/5.0.3-build105/multisig-authority/validation.zip) ·
[Source/range ledger](../evidence/5.0.3-build105/multisig-authority/source-binding.json).

The complete audit-helper suite passes **514 tests** in 11.837 seconds. The
expanded publication corpus passes secret scanning (1.49 MB); this is not a
proof that application data can never leak.

## Coverage and limitations

The 22 hash-bound source/range dispositions remain partial. Frozen inventory
counts are unchanged. Passing a corpus does not mark unreviewed code reviewed.
Other signing schemes, arbitrary policies outside supported constructors,
full-app interleavings, UI/runtime behavior, live chain/relay integration, upstream
cryptography and source-to-shipped-binary provenance are not established by this
checkpoint. The supplemental ledger identifies each file's remaining scope.

Public main was last checked at `d1a7c769e24f6d30d37a4aa43a40dc913bfdeb1d`;
this executable evidence remains pinned to the reviewed commit above and does not
automatically qualify later code. Prior findings and failures remain unchanged.

## Hosted replay and execution boundary

The audit-only workflow is pinned, read-only and has no deployment credentials or
pull-request trigger. [GitHub run 42250948694](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42250948694)
completed successfully at audit commit `66f2bdf6453acffc57b0413116a122832a052dff`.
Its fresh builds and isolated execution took **990.271 seconds**: all 13 production
methods pass with zero skips, and the single weakened-control method produces
its three expected assertion failures. The downloaded artifact matches GitHub's
SHA-256 digest `d270cadea39e10db48ca490914b8c30d79d193cb5f939baf3d4867ddb749e620`.
Every manifest, case log and fixture is checked by the committed hosted-evidence test.
[Terminal metadata, artifact and verification receipt](../evidence/5.0.3-build105/hosted-multisig-authority/verification.json).
No new generic iOS build was run for these audit-only changes. No simulator,
physical device, local application or App Store operation was used.
