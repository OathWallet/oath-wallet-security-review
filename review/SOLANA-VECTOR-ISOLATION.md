# Solana multisig vector isolation and fixture provenance

Reviewed application: `f9cccef32d4508fca13ddbf52d3eb882b5d8f0f1`.
Previous target: `e46fff5686db48a40103c9dbffe5e830cfc5548a`.
Application [PR 22](https://github.com/devdasx/oath-wallet/pull/22) changes tests
only. It is merged as `1f3464284960bc9a0262ac9182828537696138a7`
with an identical tested source tree. It does not change transaction construction, signing, verification,
provider behavior or stored wallet compatibility.

## Observed failure and repair

[GitHub run 41282913488](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41282913488)
completed 50 jobs successfully and failed `host (OathAnkr)`. The failed source
was `da7a88ad0b3dd7cc56304d2e84e9b8b134c7eb4b`. Its SPL conformance test
started and reached the harness's 120-second process limit at 120.033 seconds.
No assertion failure preceded the timeout. That test combined 19 independently
generated vectors, each doing multiple program-derived-address computations,
message generation, signing and verification. The failure and its exact source
remain in the evidence; this is a test scheduling defect, not a demonstrated
fund-loss vulnerability.

Four grouped tests have become 76 separately discoverable XCTest methods, one
per existing fixture. Each receives the same 120-second process budget. The
shared assertion body and entire fixture file are byte-identical to the previous
target. No fixture, assertion, signing step, verification step or timeout was
removed or relaxed. Existing packet-size, signer-count, SDK signature,
production signature and Codable roundtrip assertions still run for every row.

`scripts/solana-vector-isolation.py` requires all 76 unique methods, checks each
method's kind/index, compares the assertion body and fixture against the prior
source, verifies actual compiled discovery, and accepts only the exact requested
case's start/pass events. Tests run in four concurrent, network-denied processes.
Skipped, duplicated, missing, mismatched, timed-out and nonzero-exit executions
cannot pass. Five new audit-helper tests cover these evidence checks.

Local observations:

- Original grouped methods passed locally on the previous target in 20.982 to
  41.623 seconds. The GitHub timeout was **not reproduced locally**.
- Initial isolated run: 76 passed, 45.905 seconds including its build; slowest
  case 2.460 seconds. Final runner run: 76 passed, 37.876 seconds including its
  build; slowest case 2.403 seconds. These are not hardware-controlled performance
  comparisons with the GitHub runner.
- Complete networking package: 1,296 passed, 194 explicitly skipped, zero
  failures/errors, 226.76 seconds. Total discovered cases rose from 1,418 to
  1,490 solely because four groups became 76 cases; this is not 72 new vectors.
- Diagnostics: 118 passed, two skipped. Public-source/secret checks, diagnostics
  coverage and unsigned generic iOS Release compilation pass on this exact pin.
- Audit helper suite: 109 passed. No simulator, physical device, production
  transaction or App Store operation occurred.

The final-target GitHub workflow must still establish its own result. A local
pass does not erase the old CI failure or prove remote runner success. The
previous progress-28 matrix remains separately source-pinned and was still
running when this report was prepared.

## Independent SDK regeneration

The complete fixture was regenerated in a temporary directory using the unchanged
public generator `Tools/GenerateSolanaMultisigVectors.cjs` and a clean locked
installation of:

- `@sqds/multisig` 2.1.4;
- `@solana/web3.js` 1.98.4;
- `@solana/spl-token` 0.4.14;
- Node 26.5.0.

Generation and its child process ran with network access denied. The result
matches all 326,211 fixture bytes, including policy accounts, unsigned messages,
signed transactions and deterministic public seed inputs. Fixture SHA-256:
`33465bf994ceb215eadf6f7b1d03dff1a2664a7d9fa1eaaf62e12556dc1adbda`.
The lockfile's complete integrity-pinned dependency graph is published under
`fixtures/squads-sdk`. This establishes reproducibility with the recorded SDK
versions; it does not recover an unknown historical npm environment or prove
source-to-deployed-Squads-program equality.

The generator covers threshold/member combinations 1-of-2, 2-of-3, 3-of-5 and
5-of-5, legacy default payer and each explicit member payer, and setup/native/
SPL/Token-2022 instructions. This is a bounded corpus, not every threshold,
Token-2022 extension, fee policy or network behavior. Seeds are deterministic
public fixtures; no real wallet credentials or funded accounts are used.

The raw npm advisory report is preserved, including 11 affected package entries
(seven moderate, four high; counts include transitive parents). Underlying
reports concern `bigint-buffer`, `stream-json` and `uuid`. These are audit-only
JavaScript tools, not dependencies added to the iOS application. They process
fixed public fixture inputs with network denied and install scripts disabled.
That limited invocation is not a repair or complete source review of these npm
packages; their advisories remain explicit and are not declared resolved.

## Additional complete source reads

- `SolanaMultisigTests.swift`: all fixture mapping, 76 wrapper declarations,
  complete shared assertion body and malformed/foreign-key tests read. The
  independent regeneration supplements inspection of the generator; it does
  not make the 326 KB generated JSON a manual source review.
- `GenerateSolanaMultisigVectors.cjs`: deterministic public inputs, sorted
  members, payer/approval membership, SDK instruction construction, signing and
  output serialization traced. It makes no provider call.
- `OathSolanaSendModel.swift`: prepare/cancel generation invalidation,
  unlocked-session guard, quote capture, passcode fallback, submission receipt
  preservation and error presentation traced. Required authorization occurs in
  the previously reviewed vault/service, not in these UI flags. Cancelled or
  superseded work cannot overwrite a newer generation's model state.
- `OathSolanaMultisigSetup.swift`: fixed-wallet screen state, refresh suppression,
  task cancellation, pending journal reads, activation gating and bounded polling
  traced into `OathSolanaSendService`. An already initiated submission intentionally
  outlives dismissal; the service signs under vault authorization and journals
  before broadcasting. The refreshed quote is cleared before another preparation.
  UI access flags alone do not establish authorization.

Production multisig policy/crypto and service/plan files were re-read as context;
those already-reviewed dispositions were not counted again. No new confirmed
production vulnerability resulted from these reads. UI timing, presentation,
provider honesty, deployed contract correspondence and broad upstream review
remain separate boundaries. No runtime UI test was claimed.

## Reproduce

```sh
python3 scripts/checkout.py
npm ci --prefix fixtures/squads-sdk --ignore-scripts --no-fund
sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  node fixtures/squads-sdk/verify.cjs .work/source
python3 scripts/solana-vector-isolation.py .work/source \
  --expected-commit f9cccef32d4508fca13ddbf52d3eb882b5d8f0f1 \
  --scratch .work/solana-vectors-build --output .work/solana-vectors
python3 scripts/run.py .work/source OathAnkr
python3 -m unittest discover -s tests -p 'test_*.py'
```

All logs, outcomes, fixture/lock/binary hashes and original failure evidence are
under `evidence/solana-vector-isolation`, with a manifest of original and
published checksums. The review remains in progress.
