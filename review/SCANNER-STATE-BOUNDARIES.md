# Scanner handoff and capture-state review

Reviewed public application: **5.0.2 (104)**, commit
`c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`.
This is a maintainer-commissioned, Codex-led review, not independent certification.
The whole-wallet audit remains incomplete. No new confirmed application defect
or application change is claimed by this checkpoint.

## Source read and limits

Complete current-file reads covered `OathRecoveryScanner.swift`,
`OathRecoveryPhraseDraft.swift`, `OathScannerCamera.swift`, and
`OathScannerCaptureState.swift`. The [source binding](../evidence/5.0.2-build104/scanner-state/source-binding.json)
records hashes and ranges; all four match the frozen build-104 inventory bytes.

The scanner's recognizer task captures a generation, checks cancellation and
active state before publishing a result, and clears pending recognition on
background, wallet changes, lock, reset or disappearance. Multiple QR choices
use generic labels instead of displaying their contents. Camera delivery claims
are locked, one per activation; the UI callback checks generation and active
state again. Camera configuration/start/stop are queued separately from the UI.
Photo decoding has byte and thumbnail bounds; its completion checks cancellation
and generation, and cleanup is conditional on the selected photo still matching.

Handoffs separate camera dismissal from import or connection presentation. The
state machine rejects duplicate approval, prevents delivery after parent
cancellation, clears its pending payload and permits return to scanning only
from a rejected destination. Import and connection destinations also check
session state at presentation. The generic delivery closure depends on caller
and presentation lifecycle guards; full lock/reset/wallet-switch ordering across
SwiftUI dismissal and callers remains unresolved. This read is not evidence of
a new authorization defect or of its absence.

The recovery draft bounds replacement input, prevents rejected/composing input
from selecting a format, rotates request identity when text or explicit format
changes, and preserves deliberate format selection. The existing format-routing
review is historical evidence; this checkpoint does not rerun all derivation or
import-commit tests on current source.

Accordingly the scanner view, camera and draft remain **partially reviewed**.
The previously reviewed small capture-state file gains additional targeted
evidence. Reading all lines does not establish full integration correctness.
AVFoundation, PhotosUI, ImageIO/Vision internals, actual rendering, suspension,
photo permission transitions and end-to-end import authorization remain outside
these host tests. Swift String/Foundation copies are not proven zeroized.

## Current-source tests

The driver compiles the **complete unchanged production capture-state file**
with a new synthetic host fixture. No copied implementation replaces the subject.
The test oracle is an independent transition table over six abstract states and
seven events: start, accept A, accept B, dismiss, cancel, finish and reject.

- All **137,256 transition prefixes through depth six** pass: **274,512 return
  value and phase comparisons**. This is bounded enumeration, not every possible
  execution or all SwiftUI schedules.
- Pending payload lifetime passes for both accepted and canceled handoffs, using
  weak references to synthetic marker objects.
- **6,400 concurrent claim attempts** across 100 activations yield exactly one
  winner each. Stopping invalidates its token and blocks another inactive claim.
  OS scheduling is nondeterministic; no claim of exhaustive concurrency coverage.
- Retry invalidation and repeated-start idempotence pass.
- The unchanged existing `Tools/CheckScannerHandoff.swift` passes **106 checks**
  across its six destination categories.

Five separately compiled, disposable negative controls test harness sensitivity:

- Accept in any phase: exhaustive handoff group fails.
- Ignore cancellation at delivery: handoff and payload lifetime groups fail.
- Retain pending payload after dismissal: handoff and lifetime groups fail.
- Permit duplicate claims: concurrent claims and idempotence groups fail.
- Stop advancing generation: concurrent claims and generation invalidation fail.

Every other group passes in those variants. These are deliberate mutations,
**not discovered production defects or before/after repair evidence**. The driver
requires the exact failing group set, rather than accepting any nonzero exit.
Each executable has its own recorded hash. Networking is denied at runtime.

[Reproducible driver](../scripts/scanner-state-review.py) ·
[Fixture](../fixtures/scanner-state/Checks.swift) ·
[Sanitized logs and results](../evidence/5.0.2-build104/scanner-state/manifest.json).
The first identical test run is retained separately; a second run binds the
final driver after tightening its exact-result gate. Neither run failed.

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
python3 scripts/scanner-state-review.py wallet /tmp/oath-scanner-fresh /tmp/oath-scanner-results-fresh
python3 -m unittest discover -s tests -p test_scanner_state_review.py
```

Use fresh scratch/output directories. The pinned workflow records its compatible
Xcode/Swift toolchain; no signing or deployment credentials are needed.
No simulator, camera, physical device or real credential was used. No new generic
iOS build was performed for this audit-only addition; earlier build results keep
their original source pins. No App Store operation occurred.

## Earlier GitHub replay now verified

[Backup settings run 41754349979](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41754349979)
completed successfully at audit commit `2c1753979e98c1c9708ad126e2402b1799c3c492`.
The downloaded artifact matches GitHub's SHA-256 digest and all reported
source/fixture/log hashes: 52 production-model passes, 40 passing and 12 expected
failing mutation checks, and 15 all-wallet regression passes. Those results retain
their own scope; the new scanner workflow is a separate replay.

## Evidence integrity

All **437 audit-helper tests pass**. The publication scan of changed files and
expanded evidence archives reports no detected secrets. Workflow lint passes
with only the established custom runner-label warning excluded. The completion
gate still reports **16,916 outstanding review/validation items**, not a count
of vulnerabilities. Two outstanding compiler-traced files become partial;
remaining compiler dispositions are 227 reviewed, 182 partial, 1,469 outstanding,
460 generated-verified and 20 generated inputs needing trace.
