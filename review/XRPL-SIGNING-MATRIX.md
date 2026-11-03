# XRP signing, canonical bytes and threshold policy

Read/test source: `6783750661c43d3511d8973a2de77106fdf2001d`.
Baseline: build 103, `c7acd23bb139864a40273f405d18b479589d2b20`.
The five source files listed in the [source receipt](../evidence/5.0.1-build103/xrpl-signing/source.json)
have identical bytes in both commits. The amount helper repair remains separately
tracked by OW-2026-060; no new application change was made for this matrix.

## Evidence

Four real OathAnkr XCTest methods pass, with no skips. They compare **61 complete
signed transactions and their hashes** against the pinned XRPL JavaScript SDK,
and **13 RIPEMD-160 outputs** against Node's OpenSSL-backed implementation.
The matrix includes native/issued/MPT payments, AccountDelete, SignerListSet,
AccountSet master disabling, TrustSet and MPTokenAuthorize. It covers absent,
zero and maximum destination tags; issued minimum/maximum positive values;
and thresholds 1, 2, 4 and 8 with eight distinct signers.

The same methods reject changes to signed plan fields, appended transaction
bytes with a recomputed transaction hash, a wrong transaction hash, changed
signature bytes, missing signers and duplicate signer entries. The production
signer and verifier are linked from the real Swift package, including its
secp256k1 dependency; they are not copied implementations or test substitutes.
The only source overlay is the test file. All tracked application source stays
unchanged, verified after execution. Network access is denied for both the
formal fixture generator and XCTest execution.

[Reproduction commands and exact scope](../fixtures/xrpl-signing/README.md) ·
[Evidence manifest](../evidence/5.0.1-build103/xrpl-signing/manifest.json).
An initial npm setup error from a non-directory default cache is preserved;
installation with an isolated cache succeeded. The initial package experiment
and formal replay both pass. Toolchain metadata explicitly records local
Xcode 27.0, Node 26.5.0 and npm 11.17.0. GitHub uses a separately pinned toolchain;
its result is not inferred from the local run.

## Manual source review

The complete `XrplSendCrypto.swift` and `XrplMultisig.swift` were read. Inspection
covers the single/multisign domain prefixes, signed-field ordering, token amount
encodings, account identifier derivation, deterministic low-S signing calls,
verification against expected plan bytes, exact signer counts and account-ID
ordering. These checks follow the [canonical binary format](https://xrpl.org/docs/references/protocol/binary-format).
The SDK comparison supplies an independently implemented reference, not a proof
that either implementation or the protocol is defect-free.

The complete 627-line `XrplSendClient.swift` was read, including pinned ledger
reads, quote bounds, simulation, same-byte submission/reconciliation, multisig
setup and WalletConnect methods. Its provider, lifecycle and authorization
paths are **not** covered by these signing vectors. One follow-up hypothesis
requires a controlled reproduction: the WalletConnect simulation branch checks
`engine_result` but does not visibly apply the ordinary send branch's separate
`meta.TransactionResult` check. This is not yet a confirmed finding or a claim
that an actual unsuccessful transaction was approved or broadcast.

The two existing SDK-vector generators were read as well; they use deterministic
public test entropy. This expanded generator is separate from those scripts;
this checkpoint does not claim to regenerate every historical fixture.

## Still open

All five file dispositions remain partial. This matrix does not establish full
provider-response correctness, WalletConnect codec/runtime validation, application
approval UI, journal durability, transaction finality, live ledger acceptance,
all malformed input classes, cryptographic side channels or complete upstream
source/binary provenance. It found no new confirmed defect in the exercised
matrix. No simulator, physical device or App Store operation was performed.
The previous unsigned iOS build is retained as previous evidence, not a newly
performed build for this audit-only change.
