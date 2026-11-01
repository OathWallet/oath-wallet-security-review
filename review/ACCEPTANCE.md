# Acceptance checklist — not complete

Progress 22 targets application commit
`2eef5a4912ce1680cd174c7596471620ffcf129e`. The completion
checker remains nonzero; its current output is retained with the evidence. This is an evidence checklist,
not a score or security certificate.

- **Full scope disposition: incomplete.** App and upstream inventories are
  hash-bound, but most implementations remain outstanding. The app ledger has
  186 reviewed, 22 partial and 10 generated-verified files out of 4,676. Core has
  21 reviewed and 20 partial files out of 3,941. Scanners/tests do not replace reads.
- **Confirmed findings: repairs published, historical assurance gap remains.**
  OW-2026-001 and OW-2026-003 through OW-2026-008 retain their verified source
  fixes. All eight DEP-CORE and all three DEP-AEZEED repairs are integrated into
  public source. OW-2026-002's missing build source is restored, but historical
  binary equivalence remains unproven. Original reproductions and failed runs
  stay published; no vulnerability-free verdict follows from these repairs.
- **Required final-target validation: incomplete.** The new cancellation target
  passes the identical ten-run regression, the full database and diagnostics
  packages, public scanning, diagnostics coverage,
  and eight enabled diagnostic modes with eight explicit control skips. The 27
  protected-startup checks passed on production-identical `66e60330`; that
  earlier source pin remains explicit. The
  initial broad networking run had nine failures;
  a second run retained one TRON test-ordering failure. After fixing that test
  predicate, the final networking suite passes 1,210 cases with 194 skips, and
  unsigned generic iOS Release compilation passes. All failed attempts remain.
  Historical GitHub run 41264051930 passed all 44 jobs on `02a6e8a`. Run
  41270221065 on `92423215` completed with 42 passing jobs and two failures:
  the cancellation race and a prerequisite dependency DNS error. Neither run
  establishes full-matrix success for this new target.
- **Dependency provenance: bounded evidence, remaining gaps.** Fresh Core
  source builds, exact patches, public inputs, command logs and artifact hashes
  are recorded. The recorded public-app build embeds the published repaired framework binaries
  byte-for-byte. This does not establish historical App Store equivalence or
  independent byte-identical Apple builds. Replacement aezeed archives have
  two-isolated-build equality; historical aezeed/Core relationships and broader
  dependency/standard-library review remain explicit gaps.
- **Clean reproducibility: partial.** Existing GitHub jobs reproduce many
  source tests without private credentials. The consolidated native Core and
  Apple preparation scripts have local results; a fresh complete execution of
  those preparation procedures on GitHub remains outstanding. Prepared input
  hashes and copied inputs are disclosed, not treated as a fresh CI build.
- **Publication: progress evidence complete for this increment.** Application
  PRs 11 and 12 are merged; progress 19 holds the repaired framework/symbol assets and
  their source-build evidence. Progress 20 adds final integration checks and
  the retained manifest failure. Progress 21 adds the TRON source trace, six new
  property cases and its exact-target package results. Progress 22 adds the
  cancellation finding/repair, diagnostic source trace and new reproducible modes. The full-scope final audit release is not yet
  justified. The [report](REPORT.md) and [integration record](CORE-APP-INTEGRATION.md)
  distinguish source repair, host tests, compilation and runtime evidence.

This increment did not launch a simulator or physical device. Earlier progress
12 contains only its stated minimal simulator C ABI test for 112 restored-path
key equivalences, not whole-app runtime validation. No funded account,
production transaction, physical-device operation, App Store upload or
submission was used in this increment. App Store equivalence is unverified.
