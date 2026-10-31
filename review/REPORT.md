# Security review progress report

Status: **IN PROGRESS — not a completed whole-wallet audit**.

Reviewer: Codex, acting at the maintainer's request. No independent security
company endorsement is implied. Baseline: Oath Wallet 4.1.15 (100),
`c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

## Method and scope

The intended scope is the full shipped app and the upstream implementations it
uses: custody, import, storage, authentication, backup, signing, transaction
review, swaps, WalletConnect, networking, diagnostics and build supply chain.
Website services are inventoried but excluded from the mobile-wallet verdict.
No production secrets or live financial transactions are used.

The inventory hashes every tracked file. Entries remain outstanding until a
specific source review and its scope are recorded. A full package test suite
does not establish full branch coverage, end-to-end chain correctness or manual
review of every file.

## Findings

- OW-2026-001: object collection bound was omitted in WalletConnect JSON parsing.
  Reproduced against production source; one-line repair passes the same corpus.
- OW-2026-002: aezeed bridge source referenced by rebuild instructions is absent
  from the public baseline. Source publication and validation are required.

## Validation boundaries

Local results are recorded per command under `evidence/`. Initial package runs
used Swift's default Xcode build system and failed during resource signing.
Native-build-system reruns are separate evidence, not replacements for failures.
Generic iOS compilation does not exercise Face ID, Keychain on iOS, app lifecycle,
WalletConnect peer interaction or real transaction execution.

The existing vault harness copies production sources into a host executable and
substitutes network/hardware and selected derivation boundaries. Those limits
must accompany its results. Tests marked opt-in remain skipped.

## Outstanding work

- Complete file-by-file security dispositions and all chain integration traces.
- Review the reachable upstream cryptographic and WalletConnect implementations.
- Establish dependency/binary provenance beyond archive checksum verification.
- Add remaining adversarial, property and fault-injection cases from those traces.
- Resolve any resulting runtime-only uncertainty using narrowly scoped checks.

There is currently no basis for a whole-app completion verdict, an App Store
binary-equivalence claim, or a ranking against other wallets. The final report
must retain these gaps until evidence resolves them.
