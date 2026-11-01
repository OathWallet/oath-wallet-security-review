# Acceptance checklist — not complete

- **Full scope disposition:** incomplete. Application and upstream file inventories
  exist, but most implementation files are still outstanding. Inventorying or
  scanning a file is not a source review.
- **Confirmed findings:** OW-2026-001, OW-2026-003, OW-2026-004 OW-2026-005 and OW-2026-006 have targeted source repairs and retests. OW-2026-002's absent
  build source is repaired; historical binary equivalence remains unresolved.
  OW-2026-007 additionally repairs restored Ed25519 path metadata with actual
  failed-before/passed-after tests; unused dependency API hazards remain explicit.
- **Required final validation:** incomplete. The current 02a6e8a target passed unsigned generic-iOS Release compilation; each new target needs its own build. The corrected Bitcoin suite passes with 60 explicit skips. OathAnkr now passes 1,208 host cases with 194 explicit skips on f23413c;
  the complete current-target host matrix has not finished.
- **Dependency provenance:** archive checksums and pinned source identities are
  recorded. Wallet Core and historical aezeed source-to-binary relationships remain unproven.
  Replacement aezeed archives match two isolated builds with the recorded toolchain;
  module advisories and reachable-symbol results have different scopes.
- **Clean reproducibility:** GitHub's disposable clean runners reproduced the
  parser before/after result, bridge tests, several packages, security host checks
  and unsigned compilation without private credentials. Whole-matrix success has
  not been established.
- **Publication:** public review repository, application repair and review links
  are published. Progress tagged releases preserve explicitly incomplete progress
  snapshots. A final audit release is not yet justified. Progress 9 adds reproducible replacement aezeed archives,
  C ABI and AES primitive checks, and six additional dependency source reads.
  Original failed jobs and historical archive gaps remain in the record. Progress 10
  completes the selected third-party Go file dispositions, with three unrepaired
  unused-API hazards explicitly documented and reproduced. This does not close
  the standard-library or whole-application review gaps.
  Progress 11 adds mnemonic, derivation-path, HMAC/PBKDF2 and passphrase boundary
  evidence, with 7,692 outstanding completion items. Child-derivation failure
  propagation and secret-copy lifetime remain explicit open review leads.
  Progress 14 adds 23 hash-bound file dispositions, 197 multisig serialization
  checks, a passing current-source backup suite, and constructor/lifetime
  characterizations. Four Core API/hygiene limitations remain unrepaired and
  qualified separately from established application vulnerabilities.

Progress 12 includes a minimal simulator-hosted C ABI check of the shipped Core
framework for 112 restored-path key equivalences. This resolves that stated
runtime concern only; it is not whole-app runtime validation. No physical device,
funded account, production transaction, App Store upload or submission was used
for the audit. App Store equivalence remains unverified.
