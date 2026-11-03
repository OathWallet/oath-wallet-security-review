# Session and request expiry review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Target: `fd002d9272a767352c114e8b752a21f65f0694cc`.
Finding: [OW-2026-017](../findings/OW-2026-017.md).

The production session model and request TTL implementation were read and traced
through extension request/response subscribers and the local requester. The
13-case host corpus reproduces seven incorrect-state/bounds assertions and three
conversion crashes before repair, with six controls passing. All 13 pass after.
The runner validates each process independently and denies network access.

The two extension subscribers and requester were read in full. The controller
guard precedes mutation for incoming extensions; response processing uses the
stored outgoing request. ApproveEngine's creation functions and Oath's service
were traced as context, not marked completely reviewed. No dapp-to-Oath crash
or signature bypass is claimed. The source fix prevents invalid values from
mutating state or reaching unsafe conversions even when invoked directly.

The request model, fixed Time constants, expanded production-schema harness and
new fixture were read in full. Full SDK tests pass 82 cases with one explicit
skip, diagnostics pass 118 with two skips, and generic unsigned iOS Release
compilation plus source/secret and diagnostics-coverage checks pass. These are
host/compilation results, not end-to-end peer interaction or UI validation.

## Explicit remaining review work

- WCSession remains **partially reviewed**: namespace update force-unwraps an
  optional chains list. Chain-qualified required namespaces and Oath's normalized
  approvals need controlled protocol tests before assigning impact or a repair.
- The general Date milliseconds helper remains **partially reviewed**. This fix
  removes its use from session expiry; it does not validate every remaining caller.
- Outgoing SessionRequester calculates a TTL-bearing protocol method but passes
  a newly constructed default method to networking. This is an unresolved
  propagation lead; a production-path reproduction is still required.
- LinkSessionRequester assumes non-null redirect/universal-link fields. Session
  establishment and restored-session guarantees need further adversarial tests.
- Request/proposal expiry watchers, namespace validators and broader session
  lifecycle paths still have outstanding correctness/protocol work. Prior source
  reads are not counted as completed validation of those concerns.
- The complete CI matrix for this new source target is not yet verified. Prior
  successful runs retain their original source pins and do not become current
  passes automatically. Whole-wallet and upstream coverage remain incomplete.

The [evidence manifest](../evidence/session-expiry/manifest.json) retains fixture
setup failures, isolated baseline traps/assertions, final paired results and
validation logs. See the acceptance checklist for the full remaining scope.
