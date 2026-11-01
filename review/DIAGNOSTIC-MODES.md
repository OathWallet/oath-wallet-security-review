# Offline diagnostic coverage and source trace

Reviewed application: `27fcf5f58f6169e1a40fb6afced883bc736d124d`, the same tree
as public merge `99742291d6124fd2628bbf1653ec0ba5f121456f` (4.1.15, build 100).
This increment changes the audit harness and evidence, not application code.
No new production vulnerability was confirmed.

## Why these cases were skipped

The package runner already isolates XCTest cases, but removes inherited test
flags. Seven OathAnkr cases and one OathDiagnostics case explicitly require a
flag because the production reporter configures its process-global outbox only
once. They are offline tests, not live-provider tests. Process isolation alone
does not satisfy their guards.

`scripts/diagnostic-modes.py` has an explicit selector/flag allowlist. It builds
the exact clean reviewed checkout, discovers the required selectors in the
actual compiled bundle, then runs each case twice in separate host processes:
without its flag (must skip) and with only its reviewed flag (must pass).
Empty selections, wrong selectors, duplicate executions, timeouts and unexpected
skips fail the runner. Package pins, test source hashes, binary hashes,
toolchain versions, durations and both process logs are retained.

Every test process runs under a macOS profile denying all network operations.
There is no unconfined fallback. No live-test flags, provider configuration,
credentials or injected-library settings are inherited. Building may download
public pinned dependencies; that is separate from test execution. The fixtures
return synthetic RPC responses and collect diagnostic events in memory.

## Results and what they establish

Eight enabled cases passed, and all eight corresponding controls skipped:

- Arc: missing optional token names/symbols remain nonfatal; required decimals
  and invalid history sender still report, without account/contract input.
- EVM recovery: a verified pending transaction survives an unavailable receipt
  lookup; the retained diagnostic excludes signed bytes, addresses and hash.
- EVM duplicate submission: exact reconciled duplicates stay silent; an
  unverified duplicate preserves its original failure and correlation.
- Fee funding: typed insufficient-native-balance outcomes still block sending
  without being recorded as app defects; unrelated errors remain reportable.
- Quote expiry: typed stale quotes remain distinct from provider failures and
  untrusted lookalike text.
- XRP failure causes: protocol error codes survive filtering while private
  provider payloads do not.
- XRP preparation: account activation/tag/reserve requirements keep quotes
  blocked; real failures retain diagnostic evidence.
- Trace context: navigation and lifecycle changes after recording do not alter
  the captured action, originating screen, source line or original cause.

The original broad-run totals remain unchanged: OathAnkr 1,208 passed/194
skipped, OathDiagnostics 118 passed/two skipped. These targeted runs exercise
seven and one previously skipped cases, respectively. They are not eight new
production test cases or a rerun of the full package matrices. The other
diagnostics skip needs external account-response fixtures and stays open.

Reproduce on a compatible macOS host, with no private configuration:

```sh
python3 scripts/checkout.py
python3 scripts/diagnostic-modes.py .work/source --package OathAnkr --output .work/diagnostic-ankr --scratch .work/diagnostic-build/ankr
python3 scripts/diagnostic-modes.py .work/source --package OathDiagnostics --output .work/diagnostic-trace --scratch .work/diagnostic-build/trace
```

The GitHub workflow includes both modes with pinned actions, read-only tokens
and GitHub-hosted runners. Local results do not establish successful execution
on GitHub. Earlier full run 41270221065 has now completed with 42 passing jobs
and two failures: the database cancellation race documented in
[OW-2026-008](../findings/OW-2026-008.md), and a protected-startup dependency
download failing DNS resolution before its tests. These are not successful
full-matrix results. The later progress-21 run remains queued at this checkpoint.

## Source review dispositions

The complete diagnostic package Swift files were read. The following local
contracts have reviewed dispositions, linked to their exact source hashes:

- `OathDiagnostics`: bounded admission before detached processing; lock-protected
  configuration; capture of correlation/context before detaching; typed
  cancellation and control-flow exclusions; scheduling versus awaitable flush.
- `DiagnosticEvent`: bounded underlying-error depth, explicit error/domain/code
  handling, omission of arbitrary userInfo and SQL bindings, context filtering,
  timestamp coding and schema identity. The serializer's reliance on the privacy
  filter is an explicit boundary, not a claim of universal secret detection.
- `DiagnosticTrace`: lock-protected presentation state, bounded screen history,
  task-local nesting/restoration, monotonic elapsed time and historical-report
  context separate from the currently visible screen.
- `DiagnosticOutbox`: actor-serialized queue, ID-based acknowledgements during
  concurrent enqueue, retry/backoff, capacity/size/age bounds, corrupt-snapshot
  quarantine, atomic protected writes and preservation after read/write errors.
- `DiagnosticWatchdog`: utility callback isolation, monotonic stall tracking,
  generation checks across restart, weak callback ownership and foreground gating.
- `DiagnosticUploadPolicy`: exact bundled exclusion matching, retained
  fatal/runtime exceptions and fail-open behavior for a missing rule resource.
- `DiagnosticEVMBroadcast` and `ClioHolderAbsence`: bounded request/reply
  comparisons and tightly scoped predicates; neither proves chain confirmation.
- OathAnkr's `SendFeeFundingError` and `DiagnosticAvailability`: typed
  classification only; these adapters do not authorize or broadcast transactions.

The previously reviewed `DiagnosticAvailabilityPolicy` was reread; its existing
disposition is preserved. The application's `OathDiagnosticsRuntime` was read
in full: it supplies no diagnostic transport, schedules local work on lifecycle
resume and limits MetricKit input to four MiB. It remains partial because actual
MetricKit delivery, iOS notifications and device file-protection transitions
were not exercised in this host increment.

`DiagnosticPrivacy` and `DiagnosticHTTP` remain **partial** despite complete
file reads. Regex/wordlist filtering is not a proof that every possible secret
representation is removed. Broad Unicode work bounds, all provider predicates,
and every downstream call site's interpretation still require review. In
particular, read-only absence predicates reused by chain clients need their
caller behavior checked; silence in a diagnostic log is not proof of success.
Framework and standard-library implementations remain separate dependencies.

## Evidence boundaries

See [raw controls, enabled runs and hashes](../evidence/diagnostic-modes).
The initial seven-case run and the final generalized-runner run are both
retained, without double-counting cases. No app fix, before/after vulnerability
claim, generic iOS rebuild, simulator, physical device, production transaction
or App Store upload is claimed here. The existing generic iOS build applies to
the unchanged application commit. This is additional review evidence, not a
completed whole-wallet audit.

The separate cancellation follow-up retargets the application to `66e60330`.
Any diagnostic reruns on that target carry their own source commit and results
under `evidence/refresh-cancellation`; they do not rewrite the original `27fcf5f`
evidence above.
