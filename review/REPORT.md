# Oath Wallet security review progress report

**IN PROGRESS. This is not a completed whole-wallet audit.**

This is a maintainer-commissioned, Codex-led security review. It is not an
independent certification, a guarantee of zero vulnerabilities, or an App Store
binary-equivalence claim. The baseline is Oath Wallet **4.1.15 (100)**,
`c7cdbde5e9f136b595500e92fbc904b107dcd8ee`.

Current review target: **`da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b`**.
[OW-2026-011](../findings/OW-2026-011.md) repairs permission-grant revocation
across asynchronous preparation in EVM, TRON and Solana signing. The same
84-assertion corpus runs three times before and after: 27 expected failures
before, all 252 assertions pass after. [PR 15](https://github.com/devdasx/oath-wallet/pull/15) is merged with the same
source tree. Prior findings and failed attempts remain visible below. No App Store upload or submission is included.

The previous target `27fcf5f58f6169e1a40fb6afced883bc736d124d` was merged by
[application PR 11](https://github.com/devdasx/oath-wallet/pull/11), merge
`99742291d6124fd2628bbf1653ec0ba5f121456f`, with an identical source tree.
All eight confirmed Core findings have source-built Apple artifacts selected
by the public app; the three aezeed repairs remain included. Their original
[integration evidence](CORE-APP-INTEGRATION.md) stays bound to that earlier
commit. Results do not automatically transfer to later revisions.

## Scope and coverage

The intended scope is the full shipped app and reachable dependencies: custody,
creation/import, storage, authorization, backup, signing, transaction review,
swaps, WalletConnect, providers, diagnostics and build supply chain. Website
files are inventoried but excluded from the mobile-wallet verdict. No production
secrets, funded accounts, live financial transactions or physical devices are used.

The application ledger contains 4,679 files: 202 reviewed, 29 partially reviewed,
10 generated artifacts verified, 4,438 outstanding. The Wallet Core upstream
ledger contains 3,941 files: 21 reviewed, 20 partially reviewed, 3,900 outstanding.
The selected aezeed Go dependency ledger adds 28 files: 27 reviewed and 1 wordlist verified as data. The source review records three
defects in Go dependency APIs outside the traced Oath call path; the
[original reproductions](AEZEED-DEPENDENCY-REVIEW.md) and
[verified source/archive repairs](AEZEED-DEPENDENCY-REPAIRS.md) remain public.
The Core findings retain their [child-derivation review](CHILD-DERIVATION-REVIEW.md),
[constructor/lifetime reproductions](CONSTRUCTOR-LIFETIME-RESULTS.md),
[first four source patches](CORE-SOURCE-REPAIRS.md),
[extended-key repair](CORE-NATIVE-AND-EXTENDED-KEY.md),
[buffer-alias repair](CORE-DATA-ALIAS.md),
[result-state repair](CORE-RESULT-STATE.md) and
[signing/parser repair](CORE-SIGNING-PARSE.md). No reachable Oath exploit was
established for these dependency APIs. The combined eight-repair native build
passes 2,363 C++ tests and 113 C cryptography checks; both generic Apple
framework archives and packaging also pass.

At the prior `27fcf5f` target, [public app integration](CORE-APP-INTEGRATION.md) passes unsigned generic
iOS Release compilation, 158 targeted security checks, diagnostics coverage,
public-source scanning, and 118 diagnostics tests with two explicit skips.
The two embedded Core framework executable files match the published repaired
artifacts byte-for-byte. This does not establish an App Store binary comparison
or a complete final-target test matrix. Historical failures and the original
integration-outstanding checkpoints remain available.
Standard-library implementation review remains a separate outstanding boundary.
These counts are dispositions, not a security score. Tests and scanners never
convert unread code into reviewed code. See the machine-readable ledgers under
[scope](../scope) and the exact [read notes](READ-NOTES.md).

The [TRON trace and production-code corpus](TRON-SEND-TRACE.md) adds six passing
property cases, nine existing authorization checks, and current-target package
results: OathAnkr 1,208 passed/194 skipped, OathDatabase 703 passed/71 skipped,
zero failures. These results do not establish live-provider or UI behavior.
No new production defect was confirmed. The new CI job is configured but its
GitHub execution remains unverified; no app source was changed.

## Findings and repair status

- [OW-2026-001](../findings/OW-2026-001.md), low: missing object-collection limit in
  the production WalletConnect JSON decoder. Baseline reproduction failed exactly
  one of 6,016 checks; the repaired decoder passed the same corpus. Fixed and retested.
- [OW-2026-002](../findings/OW-2026-002.md), assurance gap: the baseline omitted the
  bridge source needed to rebuild its aezeed archives. Source, pinned modules,
  generators and tests are published. The new replacement archives now reproduce byte-for-byte across two isolated
  builds with the recorded toolchain, while seed and import compatibility tests pass.
  Historical source-to-binary equivalence remains unresolved; its failed comparisons
  are preserved separately from the new artifacts.
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

## Preserved f7441b8 validation

On `f7441b8`, seven OathAezeed host tests and 22 aezeed wallet-integration checks
passed. The targeted Bitcoin subset passed 27 tests with one explicit skip;
diagnostics passed 118 with two explicit skips. Public validation, secret scanning,
diagnostics coverage, Go race/vet/module checks, regenerated seed-fixture equality,
and unsigned generic iOS Release compilation passed. No full Bitcoin-suite or
whole-wallet result is inferred from these targeted checks.

The new [aezeed reproduction review](AEZEED-REPRODUCIBLE-BUILD.md) retains the
before/after timestamp and plist-order failures and two matching final builds.
Six additional Go files have source-review dispositions. Three independent ct64
tests passed: all 16,384 S-box lane comparisons, 768 AES differential samples,
a public known-answer vector, short-buffer rejection, and post-reset rejection.
The audit helper suite passes 46 cases. New CI steps check artifact hashes and
execute the primitive tests; the final-target full matrix has not yet completed.

## Preserved 90b5b28 validation

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
WalletConnect peers or transaction broadcasts. The only simulator runtime checks in progress 12 exercise Core C ABI derivation
with public fixtures; full-app runtime and visual checks were not performed. Opt-in live tests remain skipped.

Swift 6.4 parallel XML omitted skip markers in an earlier run. The audit now
retains a separate XCTest process log and classifies its actual result, with
Swift Testing reported separately. Earlier misleading XML remains as historical
evidence with this qualification. Initial build-environment failures are also
retained; they are not called production vulnerabilities.

Remaining work includes outstanding application/chain source, reachable Reown and
cryptographic code, dependency/binary provenance, additional adversarial tests,
and the exact final-source CI matrix. The completion checker rejects these gaps.
There is **no whole-wallet successful-completion verdict**.

## Progress 10 — selected Go dependency review

The remaining 14 selected Go files were read in full and their hashes reverified.
The expanded harness separates ten positive validation cases from three reproduced,
unrepaired hazards in APIs outside Oath's traced call path. See
[the dependency review](AEZEED-DEPENDENCY-REVIEW.md). This increment changes audit
evidence, not application code; progress-9 exact-pin build evidence still applies.
The full review and current-target CI matrix remain incomplete.

## Progress 11 — mnemonic and derivation boundaries

The actual pinned C/C++ mnemonic, derivation parser, HMAC and PBKDF2 implementations
passed the new macOS AddressSanitizer/UndefinedBehaviorSanitizer harness. It covers
150 seed vectors, 2,048 word indices, 40,000 bounded malformed inputs, 242 HMAC
vectors and 288 PBKDF2 vectors. Eleven Swift checks passed against Oath's actual
passphrase guard without sanitizers. Forty-nine audit-helper tests passed.

Eleven upstream files and the application passphrase guard now have explicit
source-review dispositions; HDWallet/PrivateKey and BIP32 leads remain partial.
The result retains low-level zero-round and passphrase-truncation behavior as
characterizations, not newly repaired wallet bugs. See
[the complete scope and reproduction notes](MNEMONIC-DERIVATION-REVIEW.md).
The review harness's initial extraction/header failures are retained alongside
the subsequent passing results. No application source changed in this increment;
the prior exact f7441b8 generic-iOS Release build remains the compilation evidence.

There are 7,692 outstanding items in the current completion ledger. The older
CI run and final-target matrix are not replaced by these local boundary passes.
No successful whole-wallet conclusion or App Store equivalence is claimed.

## Progress 12 — restoration path repair

[OW-2026-007](../findings/OW-2026-007.md) is fixed and merged. The identical
host regression fails before the fix and passes 140 checks afterward. A separate
minimal process using the actual Core 4.8.4 simulator framework confirms 112 key
equalities across seven chains, eight paths and two public seeds. Host derivation
is substituted; the framework experiment and application host tests are distinct.
The recovered key is preserved, including root-path backup round trips.

On the current target, diagnostics passed 118 tests with two explicit skips;
public-source and secret scans, diagnostics coverage, and unsigned generic iOS
Release compilation passed. Fifty-two audit-helper tests passed. The full
current-target GitHub matrix has not yet completed. See [the review and exact
reproduction commands](RESTORED-PATHS.md) and [results](../evidence/restored-path/results.json).

The earlier GitHub run 41250786693 finished with 40 successful jobs and one failed
scanner job: raw OSV module advisories keep that check red. This is evidence for
its older a65601b source, not the new target. The progress-11 upstream mnemonic
job passed on GitHub against f7441b8; that full matrix remains in progress.
No successful whole-wallet verdict is issued. Remaining derivation, secret-lifetime,
application/dependency review and provenance gaps stay explicit.

## Progress 13 — upstream child derivation and API failures

The production C derivation harness passed 52 official SLIP-0010 vectors,
1,920 independent hardened-path cases, 33 public/private child comparisons,
20,000 malformed extended-key calls and two unchanged-on-failure checks with
ASan/UBSan. Fifty-five audit-helper tests passed. Its static-library runner,
fixture provenance, compiler identity, input hashes, logs and initial unsuccessful
direct-link attempt are retained in [the evidence](../evidence/child-derivation).
The harness is now part of the pinned GitHub workflow; its new CI run must be
evaluated independently from the completed local result.

Two separate subprocesses reproduce a null dereference for an invalid curve and
a missing Nano public-key-generation branch. These dependency API failures are
**unrepaired**, not successful fix regressions. The traced app path does not
establish reachability; ordinary Core Nano public-key generation uses a different
implementation. See [scope, source lines and reproductions](CHILD-DERIVATION-REVIEW.md).

The 32-byte HDWallet constructor lead was narrowed by inspecting all matched
application constructor calls and the explicit upstream specialization uses.
No application patch was justified by that trace. Secret lifetime, transitive
cryptography and other caller contracts remain open. No new application source
change, simulator/device use, App Store upload or submission occurred in this
increment. The completion ledger still reports 7,695 outstanding items; it does
not convert passing derivation tests into complete file coverage.

## Progress 14 — multisig recovery and constructor lifetime

Twenty-three additional files now have hash-bound source-review dispositions,
covering the multisig recovery documents, wallet adapters, dispatch and two
backup test files. Three already-reviewed files received additional scope notes.
The current-target backup package passed 58 XCTest cases plus one Swift Testing
case, with zero skips. The new production-package mutation harness passed 197
serialization checks across eleven recovery families. It does not substitute
fake identities for crypto validation and then claim signing was tested; its
scope is strictly serialization. See [review notes](MULTISIG-RECOVERY-REVIEW.md).

An isolated compilation of exact upstream constructor/destructor bodies, their
real class header and production mnemonic/KDF implementations passed 22 positive
checks in each of two assertion configurations. Separate deterministic cases
reproduce the invalid 32-byte mnemonic/entropy API behavior and an entropy
allocation that remains unwiped immediately before free. These unrepaired
dependency limitations are not newly fixed app vulnerabilities. Source call
tracing still selects the safe 64-byte specialization for Oath's creation paths.
See [method and qualifications](CONSTRUCTOR-LIFETIME-RESULTS.md) and
[complete retained results](../evidence/constructor-multisig).

No application source changed; the existing exact-target generic iOS build
remains the build evidence. The new audit workflows need their own GitHub run.
The full matrix, transitive dependency review, broader secret lifetime and
binary-provenance gaps remain open. The completion ledger now has 7,671
outstanding items. No simulator, device or App Store operation occurred in this
audit increment.

## Progress 15 — dependency source repairs and paired retests

The four Core defects documented in progress 13/14 now have a published patch
and paired before/after host evidence. Invalid curves reject safely, Nano key
caching matches the separate public-key primitive, unsupported 32-byte mnemonic
expansion rejects before the KDF writes, and the observed entropy allocation is
zeroed before deallocation. Positive derivation and constructor compatibility
checks pass on both sides. The 62 audit-helper tests pass; an initial path-alias
fixture failure is preserved. [Scope, commands and limitations](CORE-SOURCE-REPAIRS.md).

These are source repairs, not replacement Apple frameworks or a changed Oath
application. Each dependency finding is now explicitly included in the
machine-readable findings index with integration outstanding. Source coverage
counts are unchanged: testing does not establish review of unread components.
Full dependency compilation, final-target CI, broader secret lifetime and
binary provenance remain unfinished. No simulator/device or App Store use.

## Progress 16 — full native suites, fifth dependency patch and honest scanner gate

Complete native Core/Trezor/Rust/protobuf implementations were built from the
pinned source with the four earlier repairs. The real upstream suites pass
2,363 C++ tests (613 suites) and 113 C cryptography checks. This optimized host
build is separate from the previous isolated sanitizer harnesses and from the
distributed Apple frameworks. Build logs, tool versions, input hashes and failed
setup/test attempts are preserved in [native evidence](../evidence/core-native).

DEP-CORE-005 repairs a public/private extended-key type confusion in an unused
C++ API. The unchanged 94-case regression reports 21 failures before and zero
after; the full 2,363-case upstream suite also passes with that production
translation unit repaired. The key incorrectly returned before repair is not
the private key corresponding to the supplied xpub. No Oath application call or
fund-loss exploit was established. [Detailed scope and recipe](CORE-NATIVE-AND-EXTENDED-KEY.md).

The completed historical GitHub run 41257431422 has 41 successful jobs and one
scanner failure on `f7441b8`. Its raw 40 advisory occurrences are retained.
An exact-source gate now separates that raw output from selected-source
classification; the historical replay has zero unresolved classifications.
Wrong source/locks, malformed reports, execution errors and affected compiled
packages remain failures. Ten added tests bring the helper suite to 72 passes.
This replay does not turn the historical workflow green or prove a current-target
CI pass. [Gate repair and evidence](ADVISORY-GATE.md).

One additional upstream file has a manual hash-bound disposition. Compilation
does not expand manual coverage. Three previously documented unused Go API
defects are now also explicitly open in the findings index. The completion
ledger has **7,679 outstanding items**; the increase includes these recorded
findings and the required advisory gate, rather than hidden or waived work.
The final-target matrix is still active at publication. Native CI preparation,
Apple framework integration, dependency provenance and full source review remain
unfinished. No simulator, physical device or App Store operation occurred.


## Progress 17: integrated aezeed repairs

Application PR 10 integrates DEP-AEZEED-001 through DEP-AEZEED-003 in public source.
The identical paired regression corpus reports four failing top-level tests on
original dependencies and all five passing after repair (25 nested cases; 30
pass events total). The 512 MiB GCM tests exercise each truncated length field
against standard Go GCM. Ten independent positive tests pass, including 24,576
S-box lane comparisons, 1,536 AES differential samples, 514 GHASH lengths and
220 independent BLAKE2b vectors.

On the exact current target, seven aezeed host tests pass; diagnostics has 118
passes and two explicit skips. Public-source and secret checks, diagnostics
coverage, the prepared Go race/vet/vector script, and unsigned generic iOS
Release compilation pass. Six new integrity-helper tests bring the helper
suite to 78 passes. Original failures, preflight pin rejections, and actual
before/after logs remain under `evidence/aezeed-repairs` with original and
published hashes.

Two isolated builds at `0d41065b` match all ten framework files. The final
metadata-only commit has identical sixteen bridge inputs and ten framework
hashes; that comparison is separate evidence, not a relabeled rebuild run.
The previous 02a6e8a validation does not count as a complete matrix for this
new target. Whole-wallet review and Core Apple integration remain incomplete.


The fresh raw OSV scan retains 40 advisory occurrences. Their affected import
paths are absent from all three selected target graphs, so the exact-source
gate passes with zero unresolved dispositions. `govulncheck` separately exits
zero on the prepared patched source. This is source-reachability evidence, not
module-wide or historical-binary clearance. The complete raw responses remain
under `evidence/aezeed-repairs/advisories`.

The earlier corrected gate also passed in GitHub run
[41264140940](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41264140940)
on target 02a6e8a. That prior-target result is preserved separately. The current
completion gate reports 7,679 outstanding items; new required exact-target
checks remain pending even where an earlier target passed them.


## Progress 22: cancellation repair and offline diagnostic coverage

[OW-2026-008](../findings/OW-2026-008.md) closes a queued refresh admission race.
The identical regression failed in ten of ten baseline runs and passed in ten
of ten fixed runs, with network denied and public synthetic responses. The
original CI failure, exploratory non-reproduction and compiler-cache path-alias
failure remain published. The final production fix is merged in app PR 12.
A separate TRON test wait-predicate correction preserves both assertions and
the original time budget; ten additional isolated repetitions pass.

On exact final target `2eef5a4912ce1680cd174c7596471620ffcf129e`, OathAnkr has
1,210 passes/194 skips, OathDatabase 704 passes/71 skips, and OathDiagnostics
118 passes/two skips. Unsigned generic iOS Release compilation, source/Gitleaks
validation and diagnostic coverage pass. The final checks explicitly reuse
isolated build directories. The preceding fresh build at `66e60330` and proof
that only a test predicate changed are retained separately. Nine failures in
the first networking run and one in the second are not erased or relabeled.

Eight enabled offline diagnostic modes and eight control skips pass under a
network-denial profile; all eight also ran on the final target. Ninety audit
helper tests pass. [Diagnostic source dispositions](DIAGNOSTIC-MODES.md) mark
privacy filtering and runtime integration partial, not universally verified.
The completion checker still reports 7656 outstanding items. Full source/dependency
review, remaining final-target checks, historical binary provenance and fresh
GitHub execution remain gaps. Run 41270221065 on `92423215` finished 42 jobs
successfully and failed two; the report distinguishes its cancellation failure
from its protected-startup prerequisite DNS error. Local passes are not a
claim of a successful current-target GitHub matrix.

No simulator, physical device or App Store operation occurred. See the
[durable raw evidence](../evidence/refresh-cancellation) and acceptance checklist.

## Progress 23: EVM send trace and response boundary repair

The new informational finding [OW-2026-009](../findings/OW-2026-009.md) shows
that the standalone pre-broadcast chain check omitted the EVM client's 8 MiB
response bound. The default transport already limits streaming to 64 MiB;
this is not an unbounded download or a demonstrated fund-loss vulnerability.
The same regression fails in three baseline processes and passes in three
fixed processes. Two controls pass in each process before and after. Raw logs,
fixture/binary hashes and original source revisions are preserved.

On the exact current target, OathAnkr passes 1,213 cases with 194 explicit skips;
OathDiagnostics passes 118 with two skips. All 22 EVM authorization host checks,
public-source/Gitleaks validation, diagnostic coverage and generic unsigned
iOS Release compilation pass. The build reuses an isolated directory. Ninety-two
audit-helper tests pass. The [EVM trace](EVM-SEND-TRACE.md) records what was
read and keeps nonce-helper API, chain-protocol, Safe bytecode and broader
integration questions partial. No new property-fuzzing or live-chain proof is
claimed by this increment.

The completion checker reports **7,655 outstanding items**. Current-target
GitHub execution remains pending behind earlier queued work; previous-target
successes do not establish a fresh full matrix. All historical failures remain
in the evidence. No simulator, physical-device or App Store operation occurred.

## Progress 24 — delegation nonce boundary and Safe cross-check

Application target `2e51f0bcd3e710c35a1d78ee93746f6a8f202fdc` is published in
[PR 14](https://github.com/devdasx/oath-wallet/pull/14). Merge
`76072b2a33bfa3a56ec295c60ed5e39c5bb6a955` has the same tree,
`f96f482c8cf0355ed5b8bc89741b12560a854747`.

[OW-2026-010](../findings/OW-2026-010.md) confirms an unchecked increment in the
public delegation-sizing helper. Three baseline processes trap at the maximum
nonce; LLDB identifies the production arithmetic-overflow line. Three more
baseline runs accept the next invalid boundary, failing the rejection assertion.
All six control executions pass. With the three-line guard, the identical four
cases pass in each of three processes (12 passes). No reachable app exploit is
established: existing quote/signing/verification callers already validate this
bound. The helper remains usable for provisional, unfunded fee estimates.

The [Safe source cross-check](SAFE-CONTRACT-CROSSCHECK.md) compares the app's
policy, client and receipt behavior with selected Safe 1.4.1 contract semantics
at an exact source commit. A suspected event-indexing mismatch was ruled out.
The cross-check is not contract compilation, deployed-code verification, or
local/mainnet EVM execution. Permission-batch follow-up reads and remaining
connected authorization questions are recorded in READ-NOTES.

Current-target local checks:

- OathAnkr: 1,411 selected, 1,217 passed, 194 explicit skips, zero failures;
  334.42 seconds including isolated host-package compilation.
- OathDiagnostics: 118 passed, two explicit skips, zero failures; 7.59 seconds.
- App EVM authorization harness: 22 checks passed, 67.80 seconds; production
  vault/PIN/imported signer with substituted biometrics, no HD derivation.
- Public/Gitleaks and diagnostic coverage checks passed.
- Generic unsigned iOS Release build passed in 116.17 seconds using the
  existing isolated build directory; OathAnkr was recompiled. This is not a
  fresh-from-empty iOS build or a runtime test.
- 95 audit-helper tests passed. Workflow lint passes when filtering only the
  existing unknown `xcode-27` runner-label warning; both lint outputs are saved.

The previous GitHub run
[41272454184](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41272454184)
completed with 44 successful jobs and one failed artifact-upload job. Its Aptos
host test passed, then GitHub's artifact request failed with DNS ENOTFOUND. Raw
job logs and metadata are preserved. It remains a failed run, not a source test
failure or a green matrix. Current-target GitHub results remain pending and
must be assessed separately from these local checks.

Durable logs, fixture/binary/toolchain hashes and before/after results are in
[`evidence/evm-delegation-nonce`](../evidence/evm-delegation-nonce). The application
ledger now has 4,678 files: 192 reviewed, 29 partial, 10 generated-verified and
4,447 outstanding. The completion gate still reports 7,654 outstanding items,
including older-source-only required checks. No whole-wallet completion,
independent certification or App Store binary-equivalence claim is made.


## Progress 25 — permission batch revocation during signing preparation

[OW-2026-011](../findings/OW-2026-011.md) confirms that ending, replacing or
expiring a consumed batch grant did not stop a signer waiting on preparation.
Locking and task cancellation already rejected it. The fix rechecks the grant
immediately before synchronous signing and before returning bytes on EVM, TRON
and Solana. Existing single-use scope/fee checks and durable journal semantics
remain intact. This is a low-severity lifetime defect for an already approved
removal, not a demonstrated arbitrary-transfer bypass or live fund loss.

Regression baseline: `976971f0ca3362cfba8c63bc738bd80d15abf096` includes the
controllable monotonic grant clock and completed host adapters, with production
authorization behavior still unfixed. Fix: `da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b`.
[PR 15](https://github.com/devdasx/oath-wallet/pull/15) is merged as
`00e803665a6b030ed1c035939866e739b2196d57`; both commits have tree
`25b706f9c136e26c850c1204fee974f33b57b5dd`.

- The same 21-scenario, 84-assertion corpus runs three times per phase with
  networking denied. Before: 27 expected failures and 225 passing controls.
  After: all 252 assertions pass. Actual returned signatures are verified by
  the production crypto paths. Fixture hashes match and binary hashes differ.
- Existing host authorization checks pass: batch 11, EVM 22, TRON 9, Solana 27
  (69 total). They use synthetic credentials and production vault/imported-key
  signers with substituted biometrics/HD paths; no broadcast or device is used.
- OathDiagnostics: 118 passed, two explicit skips, zero failures (7.72 seconds).
  Public-source/Gitleaks and diagnostic coverage checks pass.
- Generic unsigned iOS Release compilation passes in 150.54 seconds, reusing
  the isolated build directory and recompiling the changed vault. This is not
  a fresh-from-empty build, simulator test or physical-device check.
- Audit tooling: 97 helper tests pass. Workflow lint reports only the known
  `xcode-27` label warning; filtering that exact warning passes. Both outputs
  are retained. The new paired CI job is pinned, read-only and has no deployment
  credentials; it has not yet supplied a completed GitHub result.

The initial test fixture failed because its host mode selected incomplete
TRON/Solana adapters. A later build failed because Clang's cached module paths
mixed `/var` and `/private/var`; the successful pair used a fresh canonical
scratch directory. Both failed attempts remain in the bundle and are not
counted as reproduced security findings. The wrong-source-pin preflight was
rejected before execution. Earlier GitHub run 41281531851 remained pending with
no jobs at the recorded check; this is not a green full-matrix result.

[Permission source review](PERMISSION-BATCH-REVIEW.md) gives explicit read scope
for nine production files and the new fixture. The large vault actor and host
generator remain partial. The app ledger now contains 4,679 files: 202 reviewed,
29 partial, 10 generated-verified, 4,438 outstanding. The completion gate reports
**7,644 outstanding items**, including required checks not run on this exact
revision and upstream source/provenance gaps. Prior results keep their pins.

The 169-file evidence bundle is under
[`evidence/permission-batch-races`](../evidence/permission-batch-races), with
sanitized logs, original/published hashes, seeds implicit in the synthetic
fixtures, source pins, durations and toolchain/binary hashes. No App Store
upload, submission, simulator or physical device operation occurred. The whole
wallet review remains incomplete and is not independent certification.
