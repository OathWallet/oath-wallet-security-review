# Oath Wallet 5.0.1 (103) security review

This is a **maintainer-commissioned, Codex-led security review** of the public
Oath Wallet application. It is not independent certification, a guarantee of
zero vulnerabilities, or a comparison with the installed App Store binary.

**Active release:** [Oath Wallet 5.0.1 (103)](https://github.com/devdasx/oath-wallet/releases/tag/v5.0.1-build103), commit `c7acd23bb139864a40273f405d18b479589d2b20`. App Store Connect listed iOS version 5.0.1 as **Waiting for Review** on 2 November 2026. [Build 103 review and checks](review/RELEASE-5.0.1-103.md) · [Source manifest](scope/source.json) · [Previous review series](https://github.com/devdasx/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress57).

**The whole-wallet review is not complete.** Test success does not turn
outstanding source into reviewed source. Consult the [report](review/REPORT.md),
[coverage ledger](scope/inventory.json), [findings](findings), and
[Actions runs](https://github.com/devdasx/oath-wallet-security-review/actions) and
[acceptance checklist](review/ACCEPTANCE.md) together.

**Build 103 checkpoint 7.** The address checksum helper now rejects malformed inputs before changing their bytes. Nine production-code methods pass, including 24 independent vectors. The full SDK suite passes 306 tests with two skips, and unsigned iOS Release compilation succeeds. The source API now throws. [Finding and scope](review/ADDRESS-CHECKSUMS.md) · [Validation](evidence/5.0.1-build103/address-checksums/validation.json) · [Merged fix](https://github.com/devdasx/oath-wallet/pull/68). The helper's application reachability remains unproven.

**Build 103 checkpoint 6.** Signature constructors now reject malformed encodings safely, and contract verification uses actual signature lengths and exact supported replies. Five original traps and twelve failing methods are preserved; all twenty methods pass after repair. The full SDK suite passes 297 tests with two skips, and unsigned iOS Release compilation succeeds. [Findings and compatibility](review/SIGNATURE-CONTRACT-BOUNDARIES.md) · [Merged repair](https://github.com/devdasx/oath-wallet/pull/67) · [Validation](evidence/5.0.1-build103/signature-contracts/validation.json). The dependency verifier's application reachability remains unproven.

**Build 103 checkpoint 5.** The bundled ENS response decoder trapped on malformed input and accepted several invalid encodings. The exact-release replay preserves seven crashing processes, four failing methods and five passing controls. All sixteen pass on the merged repair. Application reachability remains unproven. [Finding](findings/OW-2026-053.md) · [Tests and review scope](review/ENS-CONTRACT-DECODING.md) · [CI evidence](evidence/5.0.1-build103/ci-artifacts-checkpoint5.json).

**Build 103 checkpoint 4.** Public source repairs cover Bitcoin-family address discovery and backup file races. The original failures, fixed cases and build receipts are recorded separately from the submitted build. [Address issuance](findings/OW-2026-049.md) · [Backup reads](findings/OW-2026-051.md) · [Conflicting backup writes](findings/OW-2026-052.md) · [Scalar arithmetic](review/SECP-SCALAR-ARITHMETIC.md).

**Build 103 checkpoint 3.** Synthetic authenticated vault and SQLite records reproduced three integer overflows. Public source repairs passed the focused tests, full database package and unsigned iOS builds. [Vault finding](findings/OW-2026-047.md) · [Database finding](findings/OW-2026-048.md) · [Exact-target CI evidence](evidence/5.0.1-build103/ci-artifacts-checkpoint3.json).

**Build 103 checkpoint 2.** Changing recovery format after an interrupted wallet import could return a different Bitcoin wallet. The error reproduced on the tagged source. [Finding and regression](findings/OW-2026-046.md) · [Application and dependency checks](review/RELEASE-5.0.1-103.md) · [Direct input coverage](evidence/5.0.1-build103/compiler/dispositions.json).

Latest dependency work: [result-wrapper state transitions](review/CORE-RESULT-STATE.md)
and [malformed signing/planning inputs](review/CORE-SIGNING-PARSE.md), with real
before/after tests. All eight source repairs pass the full native C/C++ suites.
[Apple artifact reproduction](review/CORE-APPLE-REPRODUCTION.md) is recorded
separately. [Public app integration and its checks now pass](review/CORE-APP-INTEGRATION.md).
That is not an App Store update or a whole-wallet completion verdict.

**Latest checkpoint.** [Two-factor recovery and fixture repairs](review/ELECTRUM-TWO-FACTOR.md) · [Bitcoin Cash transactions and token-bearing outputs](review/BCH-TOKENS-AND-SIGNING.md) · [Acceptance](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Provider response limits](findings/OW-2026-034.md), [Stellar decoder checks](review/STELLAR-XDR-BOUNDARIES.md) and [remaining scope](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Bitcoin signature integrity](findings/OW-2026-033.md), [Bitcoin Core results and compilation inputs](review/BITCOIN-SIGNER-AND-CORE.md), and [remaining coverage](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Bitcoin WalletConnect packet and parent limits](findings/OW-2026-032.md), [host evidence](evidence/psbt-size/manifest.json), and [remaining review work](review/ACCEPTANCE.md).

**Earlier checkpoint.** [Artwork URL admission and redirects](findings/OW-2026-031.md), [SwiftDraw document model](review/ARTWORK-HOSTS-AND-DOM.md), and [resolved package and BitcoinDevKit provenance](review/RESOLVED-PACKAGES.md).

**Earlier checkpoint.** [Token logo crash and depth bypass](findings/OW-2026-030.md), [bundled asset and SwiftDraw review](review/TOKEN-ARTWORK.md), and [historical CI evidence](evidence/ci-progress38/manifest.json).

**Earlier checkpoint.** [Early relay replies](findings/OW-2026-029.md) and [Wallet Core path API boundaries](review/CORE-PATH-C-API.md). The three relay operations timed out before the repair and completed after it.

Earlier dependency finding: [history identity across sends](findings/OW-2026-028.md).
Six stale-completion cases reproduce 10 assertions before; eight controls pass,
and all 14 pass after. SDK checks pass 254/one skip; diagnostics 118/two skips.
[Generation review](review/HISTORY-SEND-GENERATIONS.md) explains the optional local
field, legacy decoding, synthetic relay ACKs and remaining delivery limits.

Earlier dependency finding: [RPC history atomicity](findings/OW-2026-027.md).
Six races reproduce 10 assertions before; five controls pass, and all 11 pass
after. SDK checks pass 240/one skip and diagnostics 118/two skips.
[History review](review/RPC-HISTORY-ATOMICITY.md) explains shared-store instances,
controlled interleavings and the remaining cross-process/async-generation limits.

Earlier dependency finding: [session response routing](findings/OW-2026-026.md).
Eight invalid cases reproduce 18 assertions before; four controls pass, and all
12 pass after. SDK checks pass 229/one skip and diagnostics 118/two skips.
[Routing review](review/SESSION-RESPONSE-ROUTING.md) distinguishes link encryption
and history effects from relay endpoint recording and Oath app reachability.

Earlier dependency finding: [link metadata and transport state](findings/OW-2026-025.md).
Three nil-unwrap crashes and five rejected-input state assertions reproduce
before repair; eight controls pass and all 16 cases pass after. SDK checks pass
217/one skip and diagnostics 118/two skips. [Metadata review](review/LINK-SESSION-METADATA.md)
discloses restored optional fields, the host opening callback and synchronous
subscriber-test limits.

Earlier dependency finding: [incoming Link Mode boundaries](findings/OW-2026-024.md).
Eight cases reproduce 18 assertions before repair; eight controls pass and all
16 cases pass after. SDK checks pass 201/one skip and diagnostics 118/two skips.
[Link review](review/LINK-ENVELOPE-BOUNDARIES.md) distinguishes protocol dispatch
and history mutation from app reachability and complete peer authorization.

Earlier dependency finding: [authentication request input boundaries](findings/OW-2026-023.md).
Eight crashes and 32 assertions across eight cases reproduce before repair;
four controls pass and all 20 cases pass after. SDK checks pass 185/one skip
and diagnostics pass 118/two skips. [Authentication review](review/AUTH-REQUEST-BOUNDARIES.md)
documents decoder bounds, rejection before side effects, interface-only test
seams and the distinction from Oath's incoming approval path.

Earlier dependency finding: [queued cleanup and store timer lifetime](findings/OW-2026-022.md).
One controlled cleanup crash and one timer assertion reproduce before repair;
six controls pass and all eight cases pass after. SDK checks pass 165/one skip
and diagnostics pass 118/two skips. [Cleanup review](review/CLEANUP-LIFETIME-REVIEW.md)
discloses the queue test seam, preserves an initial fixture error, and reopens
three authentication input-review gaps without changing prior evidence.

Earlier dependency finding: [session watcher and callback lifetimes](findings/OW-2026-021.md).
Four isolated crashes and two duplicate-timer assertions reproduce before;
four controls pass and all ten cases pass after. SDK checks pass 157/one skip,
diagnostics pass 118/two skips and unsigned iOS Release compilation passes.
[Lifetime review](review/WATCHER-LIFETIME-REVIEW.md) records actual timer/storage
behavior and keeps remaining cleanup and concurrency work visible.

Earlier dependency finding: [outgoing request lifetime routing](findings/OW-2026-020.md).
Six assertions across four cases fail before repair; seven controls pass and
all eleven cases pass after. SDK checks pass 147/one skip, diagnostics pass
118/two skips and unsigned iOS Release compilation passes.
[Transport review](review/REQUEST-LIFETIME-REVIEW.md) traces the outgoing SDK
path and keeps link-mode, timer, service-response and cancellation gaps visible.

Earlier dependency finding: [separate-field CAIP account validation](findings/OW-2026-019.md).
Two expected assertions fail in one case before repair; all seven identical
cases pass after. SDK checks pass 136/one skip; diagnostics pass 118/two skips;
unsigned iOS Release compilation passes. [Parser review](review/CAIP-BOUNDARY-REVIEW.md)
records the rejected line-ending hypothesis, independent character oracle,
seeded corpus, preserved TON extension and limited app reachability.

Earlier dependency finding: [chain-scoped namespace validation](findings/OW-2026-018.md).
The same 15 production cases retain two crashes and 15 expected test failures
before repair, with four passing controls; all 15 pass after. SDK checks pass
118/one skip, diagnostics pass 118/two skips and unsigned iOS Release compilation
passes. [Review notes](review/NAMESPACE-BOUNDARY-REVIEW.md) distinguish these
SDK model results from an end-to-end Oath exploit and retain parser/lifecycle gaps.

Earlier dependency finding: [session expiry bounds](findings/OW-2026-017.md).
The same 13 production cases reproduce seven expected assertions and three
conversion crashes before repair, with six passing controls; all 13 pass after.
SDK checks pass 82/one skip, diagnostics pass 118/two skips, and unsigned iOS
Release compilation passes. [Review notes](review/SESSION-EXPIRY-REVIEW.md)
explain the limited Oath reachability and outstanding namespace/lifecycle work.

Earlier application finding: [SDK event opt-out lifecycle](findings/OW-2026-016.md).
All nine identical production tests pass after reproducing 14 expected assertions
before. Initialization, collection, cancellation and stale acknowledgements are
covered. [Review notes](review/EVENTS-LIFECYCLE-REVIEW.md) also preserve the prior
56-job successful GitHub run and distinguish it from the new target.

Earlier application finding: [optional relay transaction metadata](findings/OW-2026-015.md).
The encoder now preserves routing and encrypted peer content while omitting four
optional metadata fields. The same four host cases retain 11 expected assertions
before and pass afterward. [The source review](review/RELAY-METADATA-REVIEW.md)
keeps SDK initialization and other privacy boundaries explicitly outstanding.

Latest test repair: [Solana multisig vector isolation](review/SOLANA-VECTOR-ISOLATION.md).
All 76 unchanged vectors pass as separate network-denied cases, and the pinned
SDK reproduces the entire fixture byte-for-byte. The original CI timeout,
audit-tool dependency advisories and remote-validation gaps remain visible.

Earlier application finding: [router operations omitted from first approval](findings/OW-2026-014.md).
The identical production-model corpus retains 30 expected assertion failures
before and nine passing executions after. Ten ABI fixtures also pass an
independent ethers cross-check. [Approval source review](review/SWAP-APPROVAL-REVIEW.md)
distinguishes host-model tests and compilation from UI or on-chain execution.
The previous [Polygon swap destination repair](findings/OW-2026-013.md) and
[swap review](review/SWAP-REVIEW.md) retain their original evidence.
The prior [duplicate permission readback finding](findings/OW-2026-012.md) and
[discovery review](review/PERMISSION-DISCOVERY-REVIEW.md) retain their evidence.
The previous [permission-grant revocation fix](findings/OW-2026-011.md) and
[batch source review](review/PERMISSION-BATCH-REVIEW.md) remain available.
The previous [delegation nonce serialization finding](findings/OW-2026-010.md) remains,
with retained arithmetic-trap evidence and identical passing post-fix tests.
The [Safe contract cross-check](review/SAFE-CONTRACT-CROSSCHECK.md) records
source comparisons and remaining contract provenance gaps. The previous
[response-size repair](findings/OW-2026-009.md) retains its exact-limit controls. The [EVM source trace](review/EVM-SEND-TRACE.md)
keeps its remaining protocol, dependency and helper-API questions explicit.
The earlier [refresh cancellation repair](findings/OW-2026-008.md) retains its original CI failure.
[Offline diagnostic modes](review/DIAGNOSTIC-MODES.md) also cover eight cases
that previously skipped under the normal package environment. The earlier
[TRON trace](review/TRON-SEND-TRACE.md) remains available separately.

## Reproduce

Use an isolated machine with Xcode 27.1, Swift 6.4 and Python 3.14.7.
Local exploratory runs used Xcode 27.0; each run records its actual toolchain.
The optional aezeed `--rebuild` proof requires Xcode 27.0 (27A266a), matching
the archive provenance. Omitting that flag verifies recorded hashes only.
Package downloads require network access; opt-in live-chain tests are not enabled.
No signing certificate, provider credential, real wallet or App Store access is needed.

```sh
python3 scripts/checkout.py
python3 scripts/request-lifetime.py .work/source --output .work/request-lifetime --scratch .work/request-build
python3 scripts/watcher-lifetime.py .work/source --output .work/watcher-lifetime --scratch .work/watcher-build
python3 scripts/cleanup-lifetime.py .work/source --output .work/cleanup-lifetime --scratch .work/cleanup-build
python3 scripts/auth-boundary.py .work/source --output .work/auth-boundary --scratch .work/auth-build
python3 scripts/link-boundary.py .work/source --output .work/link-boundary --scratch .work/link-build
python3 scripts/link-metadata.py .work/source --output .work/link-metadata --scratch .work/link-metadata-build
python3 scripts/response-routing.py .work/source --output .work/response-routing --scratch .work/response-routing-build
python3 scripts/history-atomicity.py .work/source --output .work/history-atomicity --scratch .work/history-atomicity-build
python3 scripts/history-generation.py .work/source --output .work/history-generation --scratch .work/history-generation-build
python3 scripts/relay-early-replies.py .work/source --output .work/early --scratch .work/early-build
python3 scripts/svg-reference-graph.py .work/source --output .work/svg --scratch .work/svg-build
python3 scripts/artwork-host-policy.py .work/source --output .work/hosts --scratch .work/hosts-build
python3 scripts/bitcoin-psbt-size.py .work/source --output .work/psbt --scratch .work/psbt-build
python3 scripts/bitcoin-parent-budget.py .work/source --output .work/fetch --scratch .work/fetch-build
python3 scripts/bundled-artwork.py .work/source --output .work/resources
python3 scripts/caip-boundary.py .work/source --output .work/caip-boundary --scratch .work/caip-build
python3 scripts/namespace-boundary.py .work/source --output .work/namespace-boundary --scratch .work/namespace-boundary-build
python3 scripts/session-expiry.py .work/source --output .work/session-expiry --scratch .work/session-expiry-build
python3 scripts/swap-approval.py .work/source --output .work/approval-after --scratch .work/approval-after-build
python3 scripts/swap-progress.py .work/source --output .work/swap-after --scratch .work/swap-after-build
python3 scripts/permission-batch-races.py .work/source --output .work/batch-after --scratch .work/batch-after-build
python3 scripts/permission-readback.py .work/source --output .work/readback-after --scratch .work/readback-after-build
python3 scripts/evm-response-boundary.py .work/source --output .work/evm-evidence/after --scratch .work/evm-after-build
python3 scripts/inventory.py .work/source --output scope/inventory.json
python3 -m unittest discover -s tests -p 'test_*.py'
sh scripts/parser-check.sh .work/source .work/parser
python3 scripts/run.py .work/source OathCloudBackup
python3 scripts/run.py .work/source OathDiagnostics
python3 scripts/run.py .work/source OathDatabase
python3 scripts/run.py .work/source OathBitcoin
python3 scripts/run.py .work/source OathAnkr
python3 scripts/run.py .work/source OathAezeed
python3 scripts/run.py .work/source OathWalletHandoff
python3 scripts/relay-envelope-check.py .work/source --output /tmp/relay-evidence
python3 scripts/response-topic-check.py .work/source --output /tmp/topic-evidence
python3 scripts/uri-boundary-check.py .work/source --output /tmp/uri-evidence
python3 scripts/pairing-link-check.py .work/source --output /tmp/uri-evidence
python3 scripts/ton-properties.py .work/source --output /tmp/ton-evidence --scratch .work/ton-properties
python3 scripts/solana-properties.py .work/source --output /tmp/solana-evidence --scratch .work/solana-properties
python3 scripts/tron-properties.py .work/source --output /tmp/tron-evidence --scratch .work/tron-properties
python3 scripts/diagnostic-modes.py .work/source --package OathAnkr --output .work/diagnostic-ankr --scratch .work/diagnostic-build/ankr
python3 scripts/diagnostic-modes.py .work/source --package OathDiagnostics --output .work/diagnostic-trace --scratch .work/diagnostic-build/trace
python3 scripts/refresh-cancellation.py .work/source --output .work/cancellation-after --scratch .work/cancellation-after-build
python3 scripts/aezeed-primitives.py .work/source --expected-commit 2eef5a4912ce1680cd174c7596471620ffcf129e --output /tmp/aezeed-primitives
python3 scripts/aezeed-provenance.py .work/source --expected-commit 2eef5a4912ce1680cd174c7596471620ffcf129e --output /tmp/aezeed-provenance
python3 scripts/ton-authorization.py .work/source --output /tmp/ton-authorization --scratch .work/ton-authorization
python3 scripts/run.py .work/source scanner
python3 scripts/run.py .work/source wallet-links
python3 scripts/run.py .work/source scanner-lifecycle
python3 scripts/run.py .work/source walletconnect-sdk
python3 scripts/run.py .work/source walletconnect-verify
python3 scripts/run.py .work/source security
python3 scripts/run.py .work/source cloud-restore
python3 scripts/run.py .work/source build
```

`scripts/run.py --help` lists the additional authorization harnesses. Those
harnesses replace hardware, networking and some derivation adapters with
fixtures: their outcomes do not establish end-to-end iOS signing behavior.
Read the original harness headers and the report before interpreting a pass.

For the baseline parser reproduction, check out the baseline commit separately
and run `parser-check.sh` against it. The object-limit assertion must fail there;
it must pass on the repaired revision. The parser harness compiles the actual
production files, without rewriting them.

## Evidence and claims

Findings retain the original defect, reproduction and fix; they are not deleted
to create a clean-looking report. Results record exit status and skipped-test
summaries. A passing command may include explicitly skipped live/runtime tests.
Local logs are sanitized for paths before publication. GitHub artifacts are
retained for 90 days; release bundles preserve selected evidence longer.

No workflow deploys the app, uses production secrets or runs on a self-hosted
runner. Public PR checks use disposable GitHub-hosted machines and read-only
tokens. Changes after a reviewed commit require another review.

## Responsible use

All test credentials are public synthetic fixtures. Never fund them or supply
real credentials to these tests. Report newly discovered exploitable issues
through the application's [private reporting channel](https://github.com/devdasx/oath-wallet/security/advisories/new).
Technical details should accompany tested fixes; a public source fix is not
proof that App Store users have received it.

## Progress evidence release

The [historical progress 26 snapshot](https://github.com/devdasx/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress26)
is a prerelease, not a completed audit. It identifies the original baseline and
fixed source target and attaches sanitized logs, result records and SHA-256
checksums. Failed attempts remain included. Workflow runs after the snapshot
are additional evidence; they do not retroactively change its coverage claims.

Package runs isolate each XCTest case in its own host process and retain its
actual skipped/passed/failed output. Swift Testing runs separately. Earlier
Swift parallel xUnit files remain in evidence, but their missing skip markers
must not be read as zero skipped tests; see the reporting correction in
`review/READ-NOTES.md`. No passing command converts an opt-in skip into evidence.


## Aezeed dependency reproduction

The workflow pins Go 1.26.5. From the audit root after checkout:

```sh
reviewed=$(python3 -c "import json; print(json.load(open('scope/source.json'))['reviewed_commit'])")
python3 scripts/go-source-inventory.py .work/source "$reviewed" .work/aezeed-source-inputs.json
python3 scripts/go_advisory_triage.py evidence/bridge/osv-go.json .work/aezeed-source-inputs.json .work/advisory-triage.json
python3 scripts/aezeed-repairs.py .work/source --expected-commit "$reviewed" --output .work/aezeed-paired
python3 scripts/aezeed-primitives.py .work/source --expected-commit "$reviewed" --output .work/aezeed-primitives
bash .work/source/Tools/AezeedBridge/test.sh
```

The committed OSV snapshot makes that classification replayable; CI also obtains
and preserves a fresh snapshot. Any new unresolved affected import fails triage.
For wordlist comparison, clone the pinned Wallet Core revision in
`scope/upstream-wallet-core.json`, then run
`python3 scripts/compare-aezeed-wordlists.py .work/source <WALLET_CORE> .work/wordlists.json`
from the audit root. The module inventory does not establish historical archive
identity or manually-reviewed coverage.

## Child-derivation reproduction

The [upstream child-derivation review](review/CHILD-DERIVATION-REVIEW.md) includes
actual C tests under memory/undefined-behavior sanitizers, an independently written
HMAC/integer oracle, and pinned public SLIP-0010 vectors. It separates passing
derivation cases from two API hazards (source repairs added in progress 15) and gives a clean-checkout
command. Neither source tests nor constructor reachability establish distributed
binary equivalence or a completed wallet audit.

Progress 14 adds [multisig recovery review and mutations](review/MULTISIG-RECOVERY-REVIEW.md)
and [constructor/entropy-lifetime experiments](review/CONSTRUCTOR-LIFETIME-RESULTS.md).
Their original dependency failures remain preserved and distinct from later
source-repair regressions and the passing positive tests.

## Dependency source-repair follow-up

Four confirmed Core API/lifetime defects now have [tested source patches and
identical before/after evidence](review/CORE-SOURCE-REPAIRS.md). They are not yet
incorporated into Oath’s shipped frameworks; integration and the whole-wallet
review remain incomplete. No App Store upload was performed.

Progress 16 adds a [fifth tested Core repair and full native suites](review/CORE-NATIVE-AND-EXTENDED-KEY.md):
the same 94-case extended-key corpus has 21 failures before repair and none after;
2,363 upstream C++ tests and 113 C checks pass. Apple framework integration is
still outstanding. The [advisory gate correction](review/ADVISORY-GATE.md) retains
raw scanner findings and binds classification to the exact selected build graph.
That progress-16 snapshot recorded 7,679 outstanding items.

Progress 17 adds [three repaired aezeed dependency APIs and rebuilt archives](review/AEZEED-DEPENDENCY-REPAIRS.md),
merged in application PR 10. Identical before/after regressions, independent
primitive checks, host tests and generic iOS compilation pass. Current coverage
and missing exact-target checks remain explicit in the completion ledger.
