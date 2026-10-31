# Oath Wallet security review progress report

**IN PROGRESS. This is not a completed whole-wallet audit.**

This is a maintainer-commissioned, Codex-led security review. It is not an
independent certification, a guarantee of zero vulnerabilities, or an App Store
binary-equivalence claim. The baseline is Oath Wallet **4.1.15 (100)**,
`c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

Current review target: **`90b5b28a6f3852319a24d74143863f2b57837c4d`**.
Merged in [application PR 7](https://github.com/devdasx/oath-wallet/pull/7),
merge `89ca689a5af845943da0269e5c84ae16972eb657`. This adds a test-fixture repair
to the previously reviewed `a65601b` production source. Publication and CI evidence
for this target are recorded in `scope/source.json`. These are public-source repairs;
no App Store upload or submission was performed. Later source revisions do not
automatically inherit these results.

## Scope and coverage

The intended scope is the full shipped app and reachable dependencies: custody,
creation/import, storage, authorization, backup, signing, transaction review,
swaps, WalletConnect, providers, diagnostics and build supply chain. Website
files are inventoried but excluded from the mobile-wallet verdict. No production
secrets, funded accounts, live financial transactions or physical devices are used.

The application ledger contains 4,639 files: 132 reviewed, 8 partially reviewed, 4,499 outstanding. The Wallet Core upstream
ledger contains 3,941 files: three reviewed, two partially reviewed, 3,936
outstanding. The selected aezeed Go dependency ledger adds 28 files: 7 reviewed, 1 partially reviewed, 1 wordlist verified as data, 19 outstanding.
Standard-library implementation review remains a separate outstanding boundary.
These counts are dispositions, not a security score. Tests and scanners never
convert unread code into reviewed code. See the machine-readable ledgers under
[scope](../scope) and the exact [read notes](READ-NOTES.md).

## Findings and repair status

- [OW-2026-001](../findings/OW-2026-001.md), low: missing object-collection limit in
  the production WalletConnect JSON decoder. Baseline reproduction failed exactly
  one of 6,016 checks; the repaired decoder passed the same corpus. Fixed and retested.
- [OW-2026-002](../findings/OW-2026-002.md), assurance gap: the baseline omitted the
  bridge source needed to rebuild its aezeed archives. Source, pinned modules,
  generators and tests are published. Reconstruction matches seed vectors and
  archive sizes but **not archive hashes**. Historical source-to-binary equivalence
  remains unresolved; bundled binaries were not replaced.
- [OW-2026-003](../findings/OW-2026-003.md), informational coverage defect: four EVM
  public account-policy adapters were absent. Fixed with mocked chain-ID and policy
  tests. No direct app caller or fund-loss exploit was established.

- [OW-2026-004](../findings/OW-2026-004.md), medium: plaintext type-2 envelopes
  reached the encrypted relay request dispatcher without a topic key. The same
  four-case regression reports two failures before repair and zero after repair.
  Valid encrypted type-0/type-1 messages still dispatch; tampering is rejected.
  No end-to-end signing bypass or fund loss is demonstrated.

- [OW-2026-005](../findings/OW-2026-005.md), medium: an encrypted response on
  another topic could consume a pending request with the same ID. The identical
  four-case corpus has two failures before repair and four passes after repair.
  Eight additional tests cover separate authentication topics, persistence,
  legacy records and routing-field injection. Old pending Notify handshakes
  remain an unverified boundary of that unused product; no real peer test is claimed.

- [OW-2026-006](../findings/OW-2026-006.md), low: repeated URI decoding
  reinterpreted relay-data contents as a replacement pairing key. The app accepted
  the synthetic input. Eight identical cases give 3 pass/5 fail before and
  8 pass after. Query boundaries and serialization are repaired; this does not
  establish unauthorized signing or fund loss.

Original findings, failed runs and retests remain available. No finding is erased
or downgraded merely to produce a passing summary.

## Current-target validation

On `90b5b28`, all 14 send-status host tests and all five Solana property cases
passed. Diagnostics reports 118 passes and two explicit skips. Public source,
secret-scan and diagnostics-coverage checks passed, as did unsigned generic iOS
Release compilation. No runtime UI or App Store verification is claimed. The
new full CI matrix is pending; these targeted passes do not complete the audit.

## Preserved a65601b local validation

The [TON review increment](TON-BOUNDARIES.md) adds five production-module property
tests on the same `a65601b` source: 1,004 independent amount vectors, 256 cell
graphs, 4,096 byte mutations and dictionary/structural limits. All five cases
passed. [Final evidence](../evidence/ton-properties/final/ton-properties.json)
and the initial harness-reporting failure are both retained. No new application
vulnerability was confirmed in that increment. The audit-helper suite now has
36 passing tests; the new properties have a dedicated audit-only CI job.
The amount oracle uses Python integer arithmetic; cell round trips are not
independent consensus verification or exhaustive fuzzing.

[Results](../evidence/uri-boundary/results.json),
[identical-corpus reproduction](../evidence/uri-boundary/reproduction/results.json),
[app entry trace](../evidence/uri-boundary/reproduction/app-boundary.json), and
[published hashes](../evidence/uri-boundary/manifest.json) identify `a65601b`:

- Pairing URI: five failed cases before, eight passed after; production app-parser
  trace passes five assertions without pairing or opening any connection.
- SDK: 56 passed, one intentional skip, including 13 existing upstream URI cases.
  The skipped Verify fixture passes in its own process.
- Scanner: 13,635 assertions, 715 synthetic QR image round trips, 42 chains,
  260 public BIP39 vectors in ten languages. Link checks: 145 assertions;
  recognizer/capture-state lifecycle checks: 2,021 assertions.
- Diagnostics: 118 passed, two explicit skips. Source-boundary validation,
  root secret scan and diagnostics coverage passed.
- Generic unsigned iOS Release build passed in 36.29 seconds using the existing
  isolated cache. Source identity was checked before and after compilation.

See [input review notes](INPUT-BOUNDARIES.md) for exact read dispositions and
remaining runtime/dependency boundaries. The audit runner now exposes only the
three offline scanner modes, validates their final assertion summaries, and
adds these checks to CI. The 31 helper tests pass. Actionlint passes with only
its unknown `xcode-27` runner-label diagnostic explicitly excluded; the standard
invocation does report that label and is not claimed to pass unmodified.
The new 90b5b28 full GitHub matrix has not completed. No simulator, phone,
real pairing peer or App Store operation was used.

## Authorization and CI-failure follow-up

The TON application trace now adds **19 passing authorization assertions** on
`a65601b`, including lock/reopen and cancellation during unfinished preparation.
The exact dependency-pinned result and adapter limitations are documented in
[TON boundaries](TON-BOUNDARIES.md#application-authorization-and-recovery-increment).

The full GitHub run `41248923305` exposed an app-parser compilation timeout
and a database deadline-observation `invalidTransition`. Original failures are
retained. The runner records timeout failures and kills only its own children;
its cold-build allowance increased from 360 to 900 seconds. The cold GitHub
boundary rerun [41250799019](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41250799019)
now passes inventory, parser, relay boundary and TON jobs. Full host, dependency,
entropy and Release-build jobs were deliberately skipped in that boundary-only
run; it is not a successful full matrix. See its [exact result records and durable
archive hash](../evidence/ci-41250799019-boundaries.json).

The database test fixture raced a running worker: signed rows are already eligible
for confirmation, but the fixture attempted a later synthetic signed-to-broadcast
transition. Production correctly rejected that stale transition. Test-only commit
`90b5b28a6f3852319a24d74143863f2b57837c4d` stops the synthetic transition while
the worker is active and adds an explicit confirmation-before-broadcast case.
All 14 send-status host tests pass. The new test checks that stale broadcast cannot
undo confirmation, change signed bytes or recreate a job. No production transition
rule was relaxed. [Before/after evidence](../evidence/status-fixture/results.json)
keeps the original CI failure distinct from the corrected local test run.
Its unsigned generic iOS Release build, public-source validation, secret scan
and diagnostics checks passed. The test-only source is merged in [PR 7](https://github.com/devdasx/oath-wallet/pull/7).
Its branch commit is the new review target. Earlier a65601b results remain pinned
to that source; a new full matrix is required for the test-fixed target.

The [a65601b full matrix](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41248923305)
finished with 37 successful jobs and three failures:
raw Go advisories, the old app-parser timeout and the database fixture race.
[Final metadata](../evidence/ci-run-41248923305-final.json) and
[34 hash-verified result records](../evidence/ci-41248923305-results.json) preserve
the completed outcome and durable evidence archive.
The raw Go vulnerability scan remains a failing check with documented
reachability/provenance gaps. Passing compilation cannot override those gaps.

## Solana source and adversarial-test increment

The [Solana review](SOLANA-BOUNDARIES.md) traces wallet binding, native/SPL plans,
multisig serialization and WalletConnect parsing/signature preservation through
fourteen complete source files. The initial four production-module tests pass:
528 independent Python Base58 vectors, all truncations of three public SDK
transaction fixtures, signature-slot preservation and 2,048 deterministic
mutations (703 accepted with checked invariants, 1,345 rejected during parsing).
The extended five-case run also passes 1,038 independent modular-arithmetic
checks of the public-input curve predicate. All 39 audit-helper unit tests pass.
The audit-only workflow adds a dedicated source-pinned Solana job. This is
bounded host evidence, not consensus verification or a completed Solana review.

## Preserved e352f56 local validation

[Results](../evidence/response-topic/results.json),
[identical-corpus reproduction](../evidence/response-topic/reproduction/results.json),
and [published hashes](../evidence/response-topic/manifest.json) identify
`e352f56d0fb3be035c3600e646e3f9133adb9ef4`:

- Cross-topic response corpus: two expected baseline failures; four fixed passes.
- Eight new routing/restart/legacy/injection checks pass.
- Full SDK: 35 passed, one intentional skip. The skipped case passes separately.
- Diagnostics: 118 passed, two explicit skips, zero failures.
- Generic iOS Release compilation passed without signing, using an isolated
  incremental cache; no source changes occurred during that build.
- Source-boundary validation, root secret scan and diagnostic coverage pass.

The reply-topic field is local routing metadata, excluded from JSON-RPC. Legacy
ordinary records decode unchanged; legacy authentication records recover their
expected topic from the stored requester public key. No wallet storage identity,
transaction encoding or signing secret was migrated. The full current-source
GitHub matrix remains incomplete, and no simulator or actual peer was used.

## Preserved f506dd8 local validation

[OW-2026-004 evidence](../evidence/relay-envelope/results.json), the
[reproduction](../evidence/relay-envelope/reproduction/results.json), and its
[hash manifest](../evidence/relay-envelope/manifest.json) identify source
`f506dd8b820476296a6348c0ccbbdc42164c21f5`:

- Four relay boundary regressions: two expected baseline failures, four fixed passes.
- Full SDK host tests: 23 passed, one intentional skip. The skipped case passes separately.
- Diagnostics: 118 passed, two explicit skips, zero failures.
- Stable-source generic iOS Release compilation passed without signing.
- Public-source boundary, root secret scan and diagnostics coverage passed.

One runner attempt undercounted a case because a known SwiftPM warning was
interleaved in a test-result line; its failure is preserved alongside the tested
parser repair and later successful run. A build overlapping an early reproduction
is explicitly excluded as final-source identity evidence; the subsequent stable
build is used. The current full GitHub matrix is not yet complete.

The earlier d2fccbe8 CI run [41241757605](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41241757605)
finished with 31 successful jobs and three failures: the retained raw module
advisory scan, the subsequently corrected OathAnkr test expectations/timeout, and
a Sui host job whose detailed artifact failed to upload (ENOTFOUND). A subsequent
local Sui check passed nine cases on f23413c; the CI command failure's cause is
not established. These are not silently converted to successful CI outcomes.

The later [f23413c CI rerun](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41244250116)
finished with **33 successful jobs and one failure**. Every host job, inventory,
parser, aezeed-source and unsigned generic iOS build job succeeded. The failure
is the retained raw Go module advisory scan: 40 unique advisories. The separate
selected-source triage does not prove the historical binary is unaffected.
[Final metadata](../evidence/ci-run-41244250116-final.json),
[29 hash-verified result records and durable archive identity](../evidence/ci-41244250116-results.json)
retain this outcome; the prior progress snapshot remains unchanged. OathAnkr
reports 1,208 passed and 194 explicitly skipped, with no failures. This does not
establish the cause of the older Sui failure or validate the current a65601b
source. Its separate full matrix is still incomplete.

## Preserved validation on the previous source commit

[Exact results](../evidence/diagnostic-repair-results.json) and per-case logs for
`f23413c848d202c2b3c7061bdb349e07144ab0a2` (not relabeled as current-target results):

- OathAnkr host package: **1,208 passed, 194 explicitly skipped, zero failed**.
- OathDiagnostics host package: **118 passed, 2 explicitly skipped, zero failed**.
- Generic iOS **Release compilation passed without signing**.
- Public-source boundary validation, Gitleaks root scan and the diagnostic
  coverage guard passed. The latter observed 713 catch sites; it is not an
  independent review of all those sites.

Eighteen old diagnostics tests expected excluded availability failures to enter
the local outbox. The repairs retain real recovery/cancellation assertions and
add retained validation-error controls, chain/correlation checks and privacy
checks. Production diagnostic behavior was not changed to satisfy tests. The
76 official Squads vectors now run in four bounded 19-vector cases, retaining
all message, signature, serialization and size assertions. The original single
case exceeded the audit runner's 120-second limit; its failed log is preserved.

Earlier commits have additional host and GitHub evidence, including parser,
backup, database, authentication, lifecycle, signing and security checks. Those
passes are **not relabeled as final-commit passes**. Every new full GitHub matrix
must independently run on its exact pin; queued or cancelled jobs are not passes.
The required final matrix is not yet complete. Each run records its real toolchain.

## Dependency evidence

Wallet Core 4.8.4 release ZIP hashes match the app manifest; its source tag pins
`d40d24a63d92619167903369308bf0e2f7eb3a59`. This verifies downloaded archive
integrity, not source-to-binary identity.

The aezeed source graph was resolved for arm64 macOS, iOS and iOS Simulator
compilation targets with Go 1.26.5. No simulator was launched. Forty retained
module advisory records identify affected packages absent from all three selected
graphs. Exact import metadata, explicit advisory aliases, module versions and
regression-tested triage are retained. Raw OSV failures remain visible; this is
source-level non-reachability evidence, **not clearance of historical binaries**.

Five RFC 7914 known-answer vectors and 1,000 deterministic bitstream cases pass
against the pinned production dependency implementations. Existing upstream AEZ,
BStream, scrypt, PBKDF2 and Blake2b tests also pass with the race detector. All
2,048 aezeed words and their order match the app and pinned Wallet Core resources.
The 1 GiB RFC vector, timing/side-channel measurements, complete memory-erasure
proof, and unread cryptographic implementations remain outside these results.

## Evidence boundaries and outstanding work

The host harnesses substitute selected OS, networking, hardware and derivation
boundaries. Generic compilation does not exercise Face ID, real iOS Keychain,
WalletConnect peers or transaction broadcasts. Runtime and visual checks were
not performed in this review update. Opt-in live tests remain skipped.

Swift 6.4 parallel XML omitted skip markers in an earlier run. The audit now
retains a separate XCTest process log and classifies its actual result, with
Swift Testing reported separately. Earlier misleading XML remains as historical
evidence with this qualification. Initial build-environment failures are also
retained; they are not called production vulnerabilities.

Remaining work includes outstanding application/chain source, reachable Reown and
cryptographic code, dependency/binary provenance, additional adversarial tests,
and the exact final-source CI matrix. The completion checker rejects these gaps.
There is **no whole-wallet successful-completion verdict**.
