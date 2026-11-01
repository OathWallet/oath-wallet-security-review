# Acceptance checklist — not complete

Progress 43 targets `4cb121a588583b9b0adef626c05cbedafce3a759`. **7,594 outstanding items** remain;
this is an evidence checklist, not a security score.

- **Scope incomplete.** 4,823 application-repository files: 293 reviewed,
  62 partial, 11 generated-verified and 4,457 outstanding.
  Website files are inventoried but excluded from the mobile verdict. Core
  remains 21 reviewed, 20 partial and 3,900 outstanding. Tests do not automatically
  review source. History and transports retain acknowledgement, generic routing,
  pre-send, persistence and cross-process limitations.
- **Confirmed findings retain repairs and limits.** OW-2026-001 and OW-2026-003
  through OW-2026-028 have source fixes and tests. Eight DEP-CORE and three
  DEP-AEZEED repairs are integrated. OW-2026-002's missing source is restored;
  historical binary equality remains unproven.
- **Current checks partial.** Six stale-completion cases produce 10 assertions
  before; eight controls pass and all 14 pass after. SDK has 254 passes/one skip;
  diagnostics 118/two skips. Source/secret checks, diagnostics coverage,
  162 helper tests and generic unsigned iOS Release compilation pass. Full
  current-target CI and all other required checks at this exact pin are not
  yet verified. Earlier results retain their source pins.
- **Prior CI preserved.** Run 41337776806 completed 57 successful jobs at
  app target 4cfeb14c. Its 58 passing result records and seven expected historical
  failures are archived; all 65 log hashes were verified. Other running/queued
  matrices are not represented as final-target passes.
- **Reproducibility and provenance partial.** Read-only pinned workflows have
  no deployment credentials. Complete transport/history code is exercised with
  memory keys, synthetic link/relay endpoints and repeated ACKs. Legacy-record
  decoding and unchanged RPC wire fields are checked. Live relay timing,
  accepted-message recall, full peer handshakes, older concurrent writers and
  cross-process access are not proved. Core/aezeed provenance, historical binary
  equivalence and remaining upstream work retain their separate limits.
- **Publication is progress only.** [Source repair](https://github.com/devdasx/oath-wallet/pull/39) merged as `da45a6b791a67f41073a85b4f1db67f9ca6318c5`.
  Application source matches the tested pin, with 116 website and website-deployment differences.
  Original failures remain public. Full-scope completion is not justified.

No App Store upload/submission, live transaction, simulator or physical-device
operation occurred for this checkpoint.
