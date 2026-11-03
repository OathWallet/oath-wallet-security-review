# Oath Wallet 5.0.2 (104) — active prerelease audit

The current target is `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`,
[tag v5.0.2-build104](https://github.com/devdasx/oath-wallet/releases/tag/v5.0.2-build104).
It includes the public repairs merged through PR #77. It is a GitHub prerelease;
no upload, submission, withdrawal or other App Store Connect action is included.
The separate 5.0.1 (103) submission is unchanged.

## Continuity of evidence

The earlier [build-103 series](RELEASE-5.0.1-103.md) and its release assets remain
historical evidence. Before/after failures, source pins, tags and checksums have
not been changed to pretend they tested a later version. Earlier report pages
and release descriptions point to this current target.

The target transition compares file hashes: 1,158 identical file dispositions
carry their original scoped evidence forward; 36 changed files are reopened
for review. Their old dispositions remain archived. New and otherwise unreviewed
files remain outstanding. Dependency and network-entry inventories are regenerated.
Existing compiler-input traces remain pinned to the builds that produced them;
a fresh build-104 trace is separate. Fix ancestry is recorded per finding and
is not treated as a test result.

[Transition details](../evidence/5.0.2-build104/target-transition.json) ·
[Current source inventory](../scope/inventory.json) ·
[Archived build-103 inventory](../scope/history/5.0.1-build103/inventory.json).

## Review status

The whole-wallet review remains incomplete. All unresolved findings, coverage,
dependency provenance and runtime limitations remain explicit. Passing new
release checks does not certify zero vulnerabilities or equivalence with an
Apple-distributed binary. Tests below describe only the checks actually run.

## New exact-target validation

On `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`:

- Database: 748 passed, 72 explicit skips, zero failures.
- Diagnostics: 119 passed, two explicit skips, zero failures.
- Public-source/secret checks and diagnostic coverage passed.
- Generic unsigned iOS Release build passed; the built Info.plist reports
  version 5.0.2 and build 104. An existing isolated build cache was reused.
- Compiler trace: 2,358 non-toolchain inputs and 47 compilation units. Its
  source hashes are bound to this build. This is not full symbol reachability.
- Audit helpers: 319 passed. Three initial helper failures exposed historical
  assertions using the current inventory; they now read the archived build-103
  inventory. Original failures remain in the evidence.

[Validation and logs](../evidence/5.0.2-build104/validation/manifest.json) ·
[Compiled inputs](../evidence/5.0.2-build104/compiler/release-inputs.json) ·
[Compiled-input dispositions](../evidence/5.0.2-build104/compiler/dispositions.json).

The compiler ledger has 227 reviewed, 122 partially reviewed, 1,529 outstanding,
460 generated-and-verified and 20 generated inputs needing trace. These reflect
exact hash matches and reopened changed files, not a completed audit.

## Checkpoint 2 — later public repair

The immutable tag above remains the baseline. PR81 merges tested repair
`0614556b993f85808b13e3a69984ce36050a8dfe` as
`501915920e99475e63af5fcb9e658f3c834f3cc8`. Local focused and broader tests pass;
hosted replay is pending. [Exact results, attempts and scope](CONNECT-REMOVAL-READ.md).
No historical source pin or test result has been rewritten. The current inventory
continues to describe the baseline; later-source coverage is explicitly linked
by source hashes in this checkpoint.
