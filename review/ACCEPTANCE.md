# Acceptance checklist — in progress

Progress 44 targets `25bcf5bd3418c574d92d63c7d5d5acef39d7d75c`. The ledger has **7,593 outstanding items**. Open source dispositions, individual dependency records, and missing validation at the current target each contribute to this count.

- Application repository: 4,834 files, 294 reviewed, 62 partial, 11 generated-verified and 4,467 outstanding. Website files remain inventoried and excluded from the mobile verdict.
- Upstream Core: 23 reviewed, 22 partial and 3,896 outstanding. See the [path C API review](CORE-PATH-C-API.md) for the newly inspected interfaces.
- OW-2026-001 and OW-2026-003 through OW-2026-029 have source repairs and regression evidence. Eight Core and three aezeed repairs are integrated. OW-2026-002 retains the historical binary comparison gap.
- Current host evidence includes the six paired relay cases, SDK 260 passes/one skip, diagnostics 118 passes/two skips, 164 audit helper tests, public-source and diagnostics-coverage checks and generic unsigned iOS compilation. [Finding](../findings/OW-2026-029.md). [Release evidence](../evidence/early-relay/manifest.json).
- Prior CI evidence stays bound to its own application pin. Full validation at the current pin, remaining app and dependency source, source-to-binary provenance and unexercised runtime paths still require work.
- [Source fix](https://github.com/devdasx/oath-wallet/pull/40) merged as `e5923ad2c3218e6a8361d0d04e50367e46601b8d`. The merge tree matches the tested commit. This evidence covers public source. No App Store upload, simulator, physical-device or live transaction operation was used for these tests.
