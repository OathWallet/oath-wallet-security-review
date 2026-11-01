# Acceptance checklist — in progress

Progress 47 targets `55f4e809ba46881b1d6d454cdce3ef62a627df85`. The ledger contains **13,675 outstanding items**, including source still awaiting reachability classification and validations still required at this exact pin.

- Application repository: 4,837 files, 300 reviewed, 745 partial, 11 generated-verified, 40 cosmetic, 3,741 outstanding. The website is inventoried separately from mobile review.
- SwiftDraw has 324 outstanding and eight partial files. The other eleven Xcode package trees have 5,685 outstanding files or gitlinks. BDK FFI has 105 outstanding files. Wallet Core has 3,896 outstanding and 22 partial files. The selected aezeed ledger has 27 reviewed files and one generated-verified file. [Scope and provenance](RESOLVED-PACKAGES.md).
- OW-2026-001 and OW-2026-003 through OW-2026-032 have merged public source repairs and retests; OW-2026-002 retains a historical binary equivalence gap.
- Nine exact-app checks passed locally, including generic unsigned iOS Release compilation, 271 Bitcoin and 118 diagnostics test passes, and paired packet, parent, URL and SVG regressions. The current checkpoint also passed 177 audit helper tests. [Evidence](../evidence/psbt-size/manifest.json).
- Full CI for the final target, remaining implementation coverage, dependency source-to-binary verification and runtime questions remain open. No physical device, simulator, live Bitcoin transaction or App Store operation was used in this checkpoint.
