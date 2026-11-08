# Solana and TON message boundaries — checkpoint 39

Maintainer-commissioned, Codex-led review at public application commit
`f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e`, 5.0.3 (105). This is not independent
certification. No new application vulnerability was confirmed in this increment.
The whole-wallet review remains incomplete.

## Attack hypothesis and traced implementation

A malicious connected dApp might disguise transaction-signing bytes as a personal
message, or reuse a signature under a different domain, account or request. The
production parsers, cryptography and wallet adapters were traced at this exact
commit. No substitute signing implementation is used in the tests.

Solana personal messages must be bounded UTF-8 text without selected control and
invisible characters. The first byte must be printable. The shipped transaction
parser accepts legacy and version-zero wires: a legacy message begins with its
required signature count (1–19 in this parser), and a version-zero message begins
with 0x80. Those prefixes cannot pass the personal-message gate. The app binds
the signing key to the requested account and replaces only its own transaction
signature. This is an argument for the currently implemented wire formats, not a
promise about future protocol formats. [Solana transaction reference](https://solana.com/docs/core/transactions).

TON sign-data and connection-proof signatures hash structured domains distinct
from the transaction signing-cell hash. Text and binary messages have different
type prefixes; cell messages bind a schema checksum, timestamp, account and
domain. The app takes the sign-data domain from the session peer URL and requires
a proof proposal's domain to match its proposer URL. The wallet adapter checks
wallet ID, chain, derived address and exact request/plan pairing. Peer metadata
alone is not proof of ownership of a website; relay verification and rendered
consent remain distinct boundaries.

Sui and Polkadot message separation was already exercised in checkpoint 36.
Those results retain their earlier source pin rather than being silently counted
again as current-commit execution here.

## Local execution and sensitivity control

The driver creates two fresh archives of the complete production package and
injects the same seven-method fixture. Each selected method executes in a separate
network-denied host process. Dependency lockfiles, source manifests, toolchains,
executables and every case log are hashed.

- **27 production methods passed, zero failures and zero skips**: seven new
  methods, 15 existing Solana methods and five existing TON methods.
- Every possible leading byte is exercised for a Solana challenge. All 95
  printable ASCII prefixes are accepted and produce valid signatures; the other
  161 single-byte prefixes are rejected. This is not an exhaustive Unicode corpus.
- All three inherited Solana transaction vectors pass transaction verification
  but their message and wire bytes are rejected as personal messages. Wrong-key
  signing and altered-message verification fail. Twelve embedded controls are
  rejected; ordinary Unicode, tab/newline, and the 4,096-byte limit remain usable.
- All three TON data formats and the proof vector match the existing SDK reference
  digests/signatures. A changed domain, account, timestamp or payload cannot reuse
  the original signature. Four transaction hashes supplied as text, binary or
  proof challenges do not receive a usable raw transaction signature. Text and
  binary encoding of the same content produce different digests.
- Removing only the text/binary domain bytes in a disposable build produces
  exactly **one expected assertion failure**. The two test domains have equal
  lengths, so a retained length field cannot accidentally satisfy the assertion.
  This is a mutation sensitivity control, not a discovered vulnerability.
- Total local driver duration: **190.165 seconds**, including fresh production
  and mutation builds of 89.850 and 88.731 seconds. These are test durations,
  not application performance measurements.

The inherited SDK vectors are copied and hash-bound from the reviewed application
commit. They were not regenerated in this checkpoint. Their valid signature
controls are checked independently with CryptoKit, without requiring identical
signature bytes from different signing implementations.

[Manifest](../evidence/5.0.3-build105/message-domains/manifest.json) ·
[Logs/results](../evidence/5.0.3-build105/message-domains/runs.zip) ·
[Source and vectors](../evidence/5.0.3-build105/message-domains/validation.zip) ·
[Source/range ledger](../evidence/5.0.3-build105/message-domains/source-binding.json).

## Reproduction and remaining scope

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e
python3 scripts/message-domain-review.py wallet .work/message-domains evidence/replay/message-domains
python3 -m unittest discover -s tests -p test_message_domain_review.py
```

Use the audit release's recorded macOS/Xcode toolchain and new scratch/output
directories. A crash, timeout or unrelated assertion does not qualify as the
expected mutation result.

## Verified GitHub replay

[Run 42261460895](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42261460895) completed successfully at audit commit `571fdf769a6e8ee7d88713ea05825c561b76d605`. The downloaded archive matches GitHub’s SHA-256 and size; source, fixture, helper, dependency lock and every case log match their manifests. Its 27 production methods pass with zero skips and its deliberate mutation produces exactly one expected failed assertion. Total hosted duration was 912.624 seconds. [Durable receipt](../evidence/5.0.3-build105/hosted-message-domains/verification.json).

The original local manifest retains its historical pending-replay state; this later receipt supersedes that state without replacing the earlier evidence.

Five source/range dispositions remain partial; two vector files are classified
as test fixtures. The frozen inventory is unchanged. Full UI/lifecycle behavior,
all Unicode rendering, external dApp verification, signature replay policies of
third-party services, upstream cryptography and source-to-shipped-binary provenance
remain separate review areas. Personal signing can still authorize off-chain
actions; passing these tests does not make arbitrary messages safe to sign.
Checkpoint 34's hosted backup-exclusion assertion remains failed and unresolved.

No application code changed in this checkpoint. Checkpoint 38 separately builds
this exact application commit for generic unsigned iOS; no redundant app build
is claimed for these audit-only files. No simulator, physical device, live-chain
transaction or App Store operation was performed.
