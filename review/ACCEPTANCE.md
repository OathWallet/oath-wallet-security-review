# Acceptance checklist — in progress

Progress 46 targets `eb8239ad3be4c0b0650e2e34334982ac54c15b42`. The ledger has **13,672 outstanding items**. The added Xcode package trees increase the denominator. These counts include files still awaiting a reachability determination.

- Application repository: 4,836 files, 299 reviewed, 744 partial, 11 generated-verified, 40 cosmetic and 3,742 outstanding. Website files are inventoried and excluded from the mobile verdict.
- SwiftDraw: 21 reviewed, eight partial, 324 outstanding. Other Xcode package checkouts: seven reviewed, 5,685 outstanding. BDK Rust bridge: eight reviewed, 105 outstanding. Wallet Core: 23 reviewed, 22 partial, 3,896 outstanding. The selected aezeed source ledger contains 27 reviewed and one generated-verified file. See [package provenance](RESOLVED-PACKAGES.md) and [artwork scope](ARTWORK-HOSTS-AND-DOM.md).
- OW-2026-001 and OW-2026-003 through OW-2026-031 have public source repairs and retest evidence. OW-2026-002 retains the historical binary provenance gap.
- Ten exact-app checks passed locally, including the Bitcoin package (268 passed, 60 skipped) and provider package (1296 passed, 194 skipped), the five-case SVG and eight-case URL regression pairs, and unsigned Release compilation for generic iOS. Separately, 167 dependency tests and 174 audit helper tests passed. [Evidence manifest](../evidence/artwork-host/manifest.json).
- Full CI at this source pin, the remaining code/dependency review, binary provenance and runtime gaps remain open. The last fully archived matrix is the [progress 38 run at an earlier app commit](../evidence/ci-progress38-archive-verification.json).
- The [artwork fix](https://github.com/devdasx/oath-wallet/pull/42) and the [Bitcoin test fixture fix](https://github.com/devdasx/oath-wallet/pull/43) are merged. No simulator, physical device, live transaction or App Store upload was used in this checkpoint.
