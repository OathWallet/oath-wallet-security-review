# Acceptance checklist — not complete

Progress 41 targets `8508d02deaf965dbe6f46b3c0ca637074234e5da`. **7,590 outstanding items** remain;
this is an evidence checklist, not a security score.

- **Scope incomplete.** 4,821 application-repository files: 293 reviewed,
  60 partial, 11 generated-verified and 4,457 outstanding.
  Website files are inventoried but excluded from the mobile verdict. Core
  remains 21 reviewed, 20 partial and 3,900 outstanding. Tests never automatically
  mark a source implementation reviewed. RPCHistory and the relay responder
  are reopened for incomplete concurrency and transport-contract coverage.
- **Confirmed findings retain repairs and limits.** OW-2026-001 and
  OW-2026-003 through OW-2026-026 have source fixes and tests. All eight DEP-CORE
  and three DEP-AEZEED repairs are integrated. OW-2026-002's missing source is
  restored; historical binary equality remains unproven.
- **Current checks partial.** The routing corpus has 18 assertions across eight
  failed cases and four passing controls before; all 12 pass after. SDK has
  229 passes/one skip; diagnostics 118/two skips. Source/secret checks,
  diagnostics coverage, 154 helper tests and generic unsigned iOS Release
  compilation pass. Full current-target CI and all other required checks at
  this exact pin are not yet verified. Older results retain their source pins.
- **Prior CI preserved.** Run 41337776806 completed 57 successful jobs at
  app target 4cfeb14c. Its 58 passing result records and seven expected historical
  failures are archived; all 65 log hashes were verified. Other queued or
  running matrices are not represented as final-target passes.
- **Reproducibility and provenance partial.** Pinned read-only workflows have no
  deployment credentials. Routing tests use complete production responders,
  memory stores, a host URL callback and a relay endpoint recorder. Live relay,
  UIKit opening and actual domain association are not tested. Generic outgoing
  transport contracts and concurrent history replacement remain gaps. Repaired
  Core/aezeed artifact provenance, historical binary equivalence and remaining
  upstream review keep their separately documented limits.
- **Publication is progress only.** [Source repair](https://github.com/devdasx/oath-wallet/pull/36) merged as `0d0f31e4c1f2c77263742d3c796ceb3788634166`.
  Application source matches the tested pin, with 97 website-only differences.
  Original failures remain public. Full-scope completion is not justified.

No App Store upload/submission, live transaction, simulator or physical-device
operation occurred for this checkpoint.
