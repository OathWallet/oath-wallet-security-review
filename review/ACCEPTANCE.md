# Acceptance checklist — in progress

Progress 48 targets `0e611a5408cfa02c8463b4bcd74a0164522cf7a3`. The ledger has **13,836 open items**. The denominator includes implementations, partial reviews, dependency and development files awaiting reachability decisions, and validations missing at the exact app revision.

- Application repository: 4,839 files, 303 reviewed, 754 partial, 11 generated-verified, 40 cosmetic and 3,731 outstanding. The website is inventoried and excluded from mobile review.
- Two Rust registry crates add 161 files: five partial and 156 outstanding. The BDK Rust bridge has eight reviewed, two partial, 103 outstanding. Eleven other Xcode package checkouts have 5,685 outstanding. SwiftDraw has eight partial and 324 outstanding. Wallet Core has 22 partial and 3,896 outstanding. Selected aezeed has 27 reviewed and one generated-verified. [Evidence and limits](BITCOIN-SIGNER-AND-CORE.md).
- OW-2026-001 and OW-2026-003 through OW-2026-033 have merged source fixes and retests. OW-2026-002 retains its historical binary equivalence gap.
- Twelve exact-app checks passed locally. These include independent Core regtest verification, five additional opt-in Core tests, the unsigned generic iOS Release build, and its source file trace. [Evidence archive](../evidence/core-signatures/manifest.json).
- The current full GitHub matrix, remaining source and dependencies, independent binary reproduction and runtime gaps remain open. No simulator, physical device, public transaction or App Store upload was used.
