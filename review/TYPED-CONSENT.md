# Typed-data signing and consent — checkpoint 32

This maintainer-commissioned, Codex-led review covers Oath Wallet 5.0.3 (105),
public source `32701474fefbed3840878e35f6111e8d494e1f02`. No new production
vulnerability was confirmed by this matrix. No application repair is claimed.
The whole-wallet review remains incomplete.

## Threat and source trace

A malicious dApp could attempt to obtain a signature whose meaning differs from
the review: round a large integer, substitute an owner/chain/contract, hide a
duplicate JSON field, mislabel an unlimited approval, or change a nested value.
The review traces the production lossless JSON parser, immutable typed request,
EIP-712 encoder, permission classifier, signer and application adapters.

The parser rejects duplicate object keys before decoding and retains integer
literals as strings. The encoder validates field shapes and numeric widths,
binds supplied chain IDs to the session and produces the signed digest from the
same immutable fields made available to the review. Recognized permissions retain
their exact token, spender, amount and expiry. An omitted chain binding is shown
as a warning, not invented by the wallet. Control and direction characters are
escaped for review without normalizing the bytes to be signed.

The application adapter checks wallet/account ownership, imported-key scope and
the account's chain. The vault captures an authorization generation and rechecks
it across authentication and database awaits. The request service revalidates
session authorization and deadlines before responding. These adapter and UI
paths were source-traced, not exercised by the package host fixture.

## Reproduction

Use a clean checkout of the application commit above, macOS with a compatible
Xcode/Swift toolchain, Python 3.14.7, Node 26.5.0 and npm 11.17.0. From this audit
repository, using fresh directories:

```sh
python3 scripts/typed-consent-review.py ../wallet ../typed-build ../typed-results
python3 -m unittest discover -s tests -p test_typed_consent_review.py
```

The driver installs the integrity-locked `ethers@6.15.0` reference with lifecycle
scripts disabled. It regenerates the complete corpus and requires byte-for-byte
agreement with committed vectors. Reference generation and test execution deny
network access; dependency installation and compilation may download pinned
inputs. Only public synthetic keys are used. No transaction is broadcast.

The Swift fixture compiles with the actual archived `OathAnkr` implementation.
It does not copy the app's encoder into a separate test implementation. Every
selected XCTest method runs in a separate bounded process, with start/terminal
result checks. A skipped case is not a pass.

## Actual results

The local run used Xcode 27.2 (27B52), Swift 6.4.2, Python 3.14.7, Node 26.5.0
and npm 11.17.0. It took **204.808 seconds** including both fresh package builds.

- **20 production methods passed, 0 skipped, 0 failed:** seven new consent
  methods, eight existing typed-data methods, three sign-in methods and two
  JSON collection-bound methods.
- **616 independent reference vectors** matched domain hashes, message hashes,
  final digests and recoverable signatures. These include every supported integer
  width, every fixed-byte width, large unquoted integers, nested structures and
  arrays, Unicode strings, all subsets of the five supported domain fields,
  chain IDs around the floating-point precision boundary, and approval limits.
- **192 invalid numeric/fixed-byte vectors** were rejected. Additional methods
  reject duplicate and escaped-duplicate fields, extra fields, invalid numeric
  forms, wrong owners, wrong signing keys, wrong chains and sign-in field/origin
  substitution. Exact values and escaped control characters remain in the review
  projection.
- A separate disposable build replaces only the domain hash in the signing
  digest with zero bytes. Its selected method fails on exactly four domain-change
  assertions: **0 passed, 0 skipped, 1 expected failed method**. Crashes, build
  errors, skips or unrelated failures do not satisfy this control. This mutation
  is deliberately introduced audit code, not a production finding.

The corpus is deterministic enumeration, not a fuzzing coverage claim. The
independent reference is another implementation, not a mathematical proof of
all protocol behavior. The ordinary package build does not establish a whole
application iOS build.

[Manifest](../evidence/5.0.3-build105/typed-consent/manifest.json) ·
[Logs and exact inputs](../evidence/5.0.3-build105/typed-consent/runs.zip) ·
[Source snapshots](../evidence/5.0.3-build105/typed-consent/validation.zip) ·
[File/range ledger](../evidence/5.0.3-build105/typed-consent/source-binding.json).

## Remaining scope

Nine file/range dispositions are partial and hash-bound. Passing tests do not
promote other files or the frozen inventory to reviewed. The matrix does not
cover all nonstandard contracts, every typed-data grammar combination, full
upstream curve implementation/provenance, server-side sign-in replay handling,
all authentication/cancellation/relay interleavings, rendered and localized
consent, or runtime secret lifetime.

The audit-only hosted workflow pins source/actions/tool selections and has no
deployment jobs. Its configured Xcode 27.1 differs from the local Xcode 27.2;
actual hosted results will be preserved separately when verified. Merely
publishing that workflow is not a successful hosted replay.

No app code was changed, so no new generic iOS build was run or claimed for this
checkpoint. No simulator, physical device or App Store operation was performed.

## Verified hosted replay

[Run 42229826509](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42229826509)
completed successfully at audit commit `4c2e12f32ea4d13a46d074a8e305caf022824a10`.
The Xcode 27.1 replay took **771.309 seconds**, including both fresh builds. All
20 production methods passed without skips; the isolated mutation produced the
one expected failed method. The independently regenerated 616 valid and 192
invalid vectors are byte-identical to the local corpus.

The downloaded artifact's GitHub digest, every indexed file, source manifest,
per-case log and terminal outcome were verified. These receipts supplement the
local run; they do not extend its source or runtime scope.
[Receipt](../evidence/5.0.3-build105/hosted-typed-consent/verification.json) ·
[Durable artifact](../evidence/5.0.3-build105/hosted-typed-consent/artifact.zip).
