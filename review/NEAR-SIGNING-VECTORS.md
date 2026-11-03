# NEAR serialization, signatures and sliced transaction data

Before: `0614556b993f85808b13e3a69984ce36050a8dfe`.
Repair: `5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`.
This checkpoint uses the actual OathAnkr Swift package and public synthetic keys.
The immutable build-104 release baseline remains unchanged.

## Independent fixture and observed results

The locked near-api-js 7.3.1 generator constructs 72 native/token transaction
plans: two senders, three nonce boundaries, four amount boundaries and native,
token-without-storage or token-with-storage modes. Nonces include values above
JavaScript's exact Number range and UInt64.max; amounts include 2^64 and
UInt128.max minus one. These are serialization boundaries, not claims that a
particular balance, fee or transaction is valid on a live chain.

Ten additional vectors exercise classic action kinds 0 through 7: account
creation, contract deployment, function call, transfer, stake, FullAccess and
restricted access keys, key deletion and account deletion. Restricted-key
variants include bounded and unlimited allowances. SDK-generated signatures
are verified with Node crypto, and production Swift signing output is separately
verified by Node's Ed25519 implementation. Complete transaction bytes and hashes
are compared, not just self-verification by the same signer.

Four original methods passed. A fifth method exposed [OW-2026-065](../findings/OW-2026-065.md):
a nonzero-origin Data slice crashes the production transaction parser. Before
repair the exact fixture records four passing methods and one SIGTRAP. After
repair all five pass and Node verifies 82 application signatures. A separate
26-method existing-package replay, including two new regressions, passes.
Truncation of every prefix of the ten action vectors and trailing-byte controls
are rejected. Changed recipient, amount, block and signature controls are rejected.

An initial npm attempt failed because the host's default cache path was not a
directory. A later generator attempt called an SDK helper that is not exported;
it was corrected to use the SDK's actual exported key-action builders. These
setup/fixture failures are retained separately and are not application findings.
The successful original four-method run is retained as well as the failing and
repaired five-method runs. Each receipt identifies its executed driver hash;
snapshots preserve those driver versions.

## Source read

[Source bindings](../evidence/5.0.2-build104/near-signing/source-binding.json)
cover three additional partial dispositions:

- `NearSendCrypto.swift`: canonical sorted JSON arguments, little-endian Borsh
  fields, native/token/storage actions, SHA256 transaction hashes, Ed25519
  signatures, exact signed bytes and signer binding. Multisig verification is
  delegated to another implementation and is not closed by these vectors.
- `NearDecoding.swift`: account-scoped history, known/unknown asset references,
  transaction/receipt identities, duplicate-page rejection and cursor bounds.
- `NearModels.swift`: account syntax, canonical unsigned amounts, saturated
  transfer-index values, heights, timestamps and token metadata normalization.

The reader fix was traced separately through its transaction constructor. The
SDK action builders used by the generator were inspected; this is not a review
of the complete SDK or all of its transitive dependencies. The SDK is audit-only
and is not added to the application.

## Reproduce

Use the compatible pinned toolchain in the workflow; dependency installation
needs network access, while generation, Swift tests and signature verification
run with network access denied.

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach 0614556b993f85808b13e3a69984ce36050a8dfe
python3 scripts/near-signing-vectors.py wallet scratch evidence/before
# Expected nonzero exit, preserved crash:
python3 scripts/near_signing_evidence.py evidence/before --baseline
git -C wallet checkout --detach 5d91d1e4dfd36c56031c7a8fb1ee305446dc54de
python3 scripts/near-signing-vectors.py wallet scratch evidence/after --commit 5d91d1e4dfd36c56031c7a8fb1ee305446dc54de
python3 scripts/near_signing_evidence.py evidence/after
python3 scripts/near-reader-regressions.py wallet scratch/build evidence/regressions
```

[Receipts, logs and validation](../evidence/5.0.2-build104/near-signing/manifest.json).
The workflow rejects missing methods, skips, incorrect source pins and an
unexpected baseline failure. A generic process failure cannot satisfy the
expected SIGTRAP receipt.

## Remaining scope

These fixtures do not establish complete action semantics, live protocol fee
acceptance, provider honesty, all malformed/persisted combinations, multisig
coverage, every cancellation interleaving or on-device behavior. History and
metadata implementations are source-read only in this checkpoint. CryptoKit's
internal implementation is not audited here. No source-to-App-Store-binary
comparison, live chain, simulator, physical device or App Store operation occurred.
The whole-wallet audit remains incomplete.

Public repair: [PR82](https://github.com/devdasx/oath-wallet/pull/82), merge
`0b35c607bc531e2f08c4815dfa36683f806d9eb4`, byte-identical to the tested tree.
