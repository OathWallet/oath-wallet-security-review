# Acceptance checklist — not complete

Progress 28 targets application commit
`e46fff5686db48a40103c9dbffe5e830cfc5548a`. The completion checker reports
**7,615 outstanding items**. This is an evidence checklist, not a security score
or certificate.

- **Full scope disposition: incomplete.** The app ledger has 242 reviewed,
  31 partial, 10 generated-verified and 4,525 outstanding files out of 4,808.
  Website changes are inventoried but excluded from the mobile-wallet verdict.
  Core retains 21 reviewed, 20 partial and 3,900 outstanding files. Tests do not
  automatically review dependencies or resolve runtime/protocol questions.
- **Confirmed findings: repairs published; historical assurance gap remains.**
  OW-2026-001 and OW-2026-003 through OW-2026-014 retain source fixes and tests.
  All eight DEP-CORE and three DEP-AEZEED repairs are integrated. OW-2026-002's
  missing source is restored, but historical binary equality remains unproven.
  The latest finding resolves the previously open mixed-operation approval lead.
- **Required final-target validation: incomplete.** Current target passes nine
  repeated approval-model executions, OathAnkr (1,224 passed/194 skipped),
  diagnostics (118 passed/two skipped), public scanning, diagnostic coverage and
  generic unsigned iOS Release compilation. Ten ABI vectors pass an independent
  ethers 6.15.0 cross-check and a clean locked installation. The baseline retains
  30 expected assertion failures and three passing control executions. The first
  broader post-fix run failed one positional-field assertion; its failed log is
  retained and the corrected semantic-field assertion passes. Other required
  checks retain their original pins; the full final-target GitHub matrix is not
  verified.
- **Dependency provenance: remaining gaps.** Repaired source-built Core Apple
  artifacts and replacement aezeed archive equality are separately recorded.
  Historical App Store equivalence, broad upstream review, live protocols and
  deployed-contract correspondence remain incomplete.
- **Clean reproducibility: partial.** Paired CI uses pinned actions, source,
  read-only permissions, a GitHub-hosted runner and no deployment credentials.
  Prior-source run 41282913488 has a retained Solana SDK-vector timeout at 120
  seconds. A later local pass does not resolve that GitHub failure. The newly
  added paired job and final-target full matrix still need their own CI result.
- **Publication: progress only.** Application [PR 21](https://github.com/devdasx/oath-wallet/pull/21) is merged as
  `2629e43b5392406ac6011c11b1fa5325870de558`, with an identical tested source tree.
  Earlier releases retain findings, failed attempts and source-pinned results.
  Final full-scope completion is not justified.

No simulator, physical device, funded account, production transaction or App
Store operation occurred in this increment. Earlier progress 12 contains only
its explicitly scoped simulator C ABI check, not whole-app runtime validation.
