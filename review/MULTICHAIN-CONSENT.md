# Sui, NEAR and Polkadot consent — checkpoint 36

Maintainer-commissioned, Codex-led review of Oath Wallet **5.0.3 (105)** at
`32701474fefbed3840878e35f6111e8d494e1f02`. No new application vulnerability was
confirmed and no application code was changed. The whole-wallet review remains
incomplete. Checkpoint 34's hosted storage assertion remains failed and unresolved.

## Attack hypotheses and production trace

A malicious dApp could seek a signature for an altered transaction after the
user approves a different request, replay stale consent, cross a network/account
boundary, or obtain a transaction signature through a message-signing method.
NEAR access-key actions also require an explicit description of the authority
being granted or removed.

The production Sui parser validates bounded BCS data, sender and gas-owner
relationships and method/network fields. Signing binds the complete request to
the review, rejects expired/future reviews, and verifies the signing key's address.
Personal-message and transaction signatures use different intent domains. The
provider review checks chain identity, epoch, simulation success, complete balance
effects and fees; preflight rejects changed effects. Simulation is a provider
assertion, not a light-client proof or a complete description of contract authority.

NEAR parses complete Borsh actions and ordered batches, retains integer nonce
precision, and binds every signed byte to the approved request. Full-access key
creation and account deletion are explicitly described; the view retains the
authority warning. Sign-in grants use bounded function-call permissions, while
revocation must match the saved session's key and current on-chain permission.
These are source traces; the actual relay, node and rendered review were not run.

Polkadot binds genesis hash, account, signed extensions, runtime, era, nonce, tip
and method to the request/review. Provider checks reject unsupported runtime
encoding, missing balance/fee state and changed preflight results. Long signing
payloads use the configured hash rule; message signing wraps its separate domain
instead of signing raw transaction bytes.

The application adapters check wallet, account, imported-key chain and derived
address. The vault checks authentication/removal generations around awaited work;
the session service checks prepared request ownership and its reviewed submission
path. Source inspection of these ranges does not exercise every scheduling race.

## Reproduce

Use macOS with a compatible Xcode and Python 3.14.7:

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach 32701474fefbed3840878e35f6111e8d494e1f02
python3 scripts/multichain-consent-review.py wallet .work/multichain-consent evidence/replay/multichain-consent
python3 -m unittest discover -s tests -p test_multichain_consent_review.py
```

Scratch/output directories must be new. Complete production packages are built
with locked dependencies. Each selected test runs in an isolated process with
networking denied. All keys/accounts are deterministic synthetic fixtures. No
funded account, live provider, relay, node or transaction broadcast is used.

## Verified local results

Xcode 27.2 (27B52), Swift 6.4.2 and Python 3.14.7: **193.316 seconds**, including
two fresh package builds.

- **40 production methods pass, zero fail, zero skip:** seven new methods and
  33 inherited Sui, NEAR and Polkadot methods. The optional live Polkadot runtime
  method is excluded and is not counted as a pass.
- All 217 single-byte Sui alterations are evaluated. 53 are rejected by parsing;
  164 remain valid requests but cannot reuse original consent. Those 164 can be
  signed with a new matching review, preventing an always-reject false pass.
- Four personal-message fixtures cover ordinary text, base64-looking text,
  Unicode and a large message. Wrong signature domains and stale/future consent
  are rejected; exact permitted age boundaries are exercised.
- NEAR batches of every supported size, 1–16, preserve ordered transactions and
  nonce precision above the JavaScript safe-integer boundary. All 136 altered
  transaction amounts reject old consent and accept newly matching consent.
  Duplicate/reversed batches reject. Full-access, key deletion and account deletion
  fixtures retain their explicit authority descriptions and cannot substitute for
  a reviewed transfer.
- Twenty valid Polkadot payload changes across four existing SDK vectors reject
  old consent and accept matching consent. Nonce, tip, runtime versions and method
  data are covered, as are the exact allowed review-age boundaries. Message-domain
  signatures do not verify over the raw transaction payload or a different key.
- Removing only Sui's request/review equality guard in a disposable build causes
  exactly **three expected assertion failures in one method**. This is a test
  sensitivity control, not a discovered app vulnerability or app before/after fix.

[Manifest](../evidence/5.0.3-build105/multichain-consent/manifest.json) ·
[Logs and results](../evidence/5.0.3-build105/multichain-consent/runs.zip) ·
[Source snapshots](../evidence/5.0.3-build105/multichain-consent/validation.zip) ·
[Source/range ledger](../evidence/5.0.3-build105/multichain-consent/source-binding.json).

## Source drift and remaining limits

Public main was rechecked at `d1a7c769e24f6d30d37a4aa43a40dc913bfdeb1d`.
It contains subsequent website/branding changes, including a WalletConnect icon
URL and refresh-artwork changes. This checkpoint's executable evidence stays at
the exact pinned commit above; it does not automatically qualify later commits.

Fourteen hash-bound source/range dispositions remain partial. Frozen inventory
counts are unchanged; automated success does not mark unread implementations
reviewed. Full application interleavings, UI/localization runtime, node/relay
behavior, malicious-provider truth, upstream cryptographic implementations and
source-to-shipped-binary provenance remain separate work.

The hosted replay is pending; only the local results above are currently claimed.
The audit-only workflow has read-only permissions, pinned actions and no deployment
credentials. No new generic iOS build was run for audit-only changes. No simulator,
physical device or App Store operation was performed.
