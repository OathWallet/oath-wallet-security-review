# Acceptance checklist — in progress

Progress 45 targets `1dbe6cbabb7397ad86be917e034fb88884fbca8d`. The ledger has **7,905 outstanding items**. This checkpoint adds SwiftDraw's previously unenumerated upstream files; counts across checkpoints have different denominators.

- Application repository: 4,835 files, 296 reviewed, 741 partial, 11 generated-verified, 40 cosmetic and 3,747 outstanding. Website files are inventoried and excluded from the mobile verdict.
- SwiftDraw: 353 upstream files, two reviewed, two partial and 349 outstanding. Wallet Core: 23 reviewed, 22 partial and 3,896 outstanding. The aezeed inventory remains separate. [Asset scope and review boundaries](TOKEN-ARTWORK.md).
- OW-2026-001 and OW-2026-003 through OW-2026-030 have public source repairs and test evidence. Eight Core and three aezeed repairs are integrated. OW-2026-002 retains the historical binary-equivalence gap.
- Current evidence includes five paired SVG cases, 84 artwork package passes/ten skips, 118 diagnostics passes/two skips, 168 audit helper tests, public-source validation, diagnostics coverage, bundle inspection and an unsigned generic iOS Release build. [Paired evidence](../evidence/svg-graph/manifest.json).
- Historical GitHub run 41345235526 passed 64 jobs. Its 65 passing result records are tied to the prior progress 38 app pin; seven expected baseline failures have their own pins. [Verified CI artifacts](../evidence/ci-progress38-archive-verification.json). Full CI at the current target, outstanding source and dependencies, source-to-binary provenance and runtime gaps still require work.
- [Source fix](https://github.com/devdasx/oath-wallet/pull/41) merged as `e3c0bc5921492349dad1aaacb90d02eebe366a43`. The merge tree equals the tested commit. No App Store upload, simulator, device operation or live transaction occurred in this checkpoint.
