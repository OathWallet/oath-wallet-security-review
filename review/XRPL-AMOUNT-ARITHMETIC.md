# XRPL amount arithmetic — bounded host review

Baseline: build 103, `c7acd23bb139864a40273f405d18b479589d2b20`.
Pre-fix reproduction: `a904515793b087289140e4411924f030b3fe61ff`.
Tested repair: `6783750661c43d3511d8973a2de77106fdf2001d`, merged through
[PR #74](https://github.com/devdasx/oath-wallet/pull/74).

## Confirmed defect

[OW-2026-060](../findings/OW-2026-060.md) is a low-severity payment-availability
failure: large valid issued amounts can fail transfer-rate calculation because
an intermediate quotient has leading-zero padding. No wrong signed payment,
authorization bypass or fund loss was demonstrated. The repair strips that
padding before checking size, and also bounds the rounded result.

## Reproduce from public source

Use Python 3.14.7 and Xcode 27.1 on macOS; the workflow checks the toolchain.
No signing identity, provider account or wallet credential is needed.

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach a904515793b087289140e4411924f030b3fe61ff
python3 scripts/xrpl-amount-properties.py wallet evidence/local/xrpl/before --expected-commit a904515793b087289140e4411924f030b3fe61ff
git -C wallet checkout --detach 6783750661c43d3511d8973a2de77106fdf2001d
python3 scripts/xrpl-amount-properties.py wallet evidence/local/xrpl/after
```

Run these commands from this review repository. Both source revisions must be
clean. The script copies selected production function bodies unchanged, supplies
only the enclosing declarations and a JSON test driver, and compiles them with
Swift 6. It denies network access to the executable. An independent Python
integer/decimal oracle checks 4,900 deterministic cases, seed 20261103. This
covers canonical strings, 16-digit rounding, issued amount parse/format,
subtraction and transfer-rate floor/ceiling. It is bounded property testing,
not an exhaustive mathematical proof or a full XRPL implementation test.

The pre-fix run has **4,843 passes / 57 failures**; the fixed run has **4,900
passes / zero failures**. The script accepts the exact known failure indices
only on the pre-fix revision, preserving them as failures in its report. Four
explicit failures use protocol-valid `1e90` at 1:1 and 2:1 rates in both rounding
directions. Random helper-domain cases are not all valid on-ledger token amounts.
The initial 4,895-case experiment and intermediate reruns are retained separately.

## Wider validation

The actual OathAnkr package selected 32 XRP methods: 29 passed, three skipped.
One skipped diagnostics test was rerun in a fresh process with only
`OATH_XRPL_PREPARATION_DIAGNOSTICS_TEST=1` and passed. The two remaining skips are
opt-in live testnet methods; they were not enabled. The original skip remains in
the evidence. OathDiagnostics passed 119 methods with two explicit skips.
Public-release validation, diagnostics coverage, a redacted source secret scan
and generic unsigned iOS Release compilation passed on the tested repair.
No simulator, physical device, live ledger or App Store operation was performed.

[Manifest and raw/compressed receipts](../evidence/5.0.1-build103/xrpl-amounts/manifest.json).
The merge differs from the tested commit only in 91 concurrent Website files;
all other tracked source, dependencies and build settings match. No website test
or deployment result is claimed by this comparison.

## Source coverage and remaining limits

The complete baseline amount helper, XRP model/parser, send-plan validation and
preparation wrapper were read. Their hashes and read ranges are in the
[source receipt](../evidence/5.0.1-build103/xrpl-amounts/source.json). Coverage stays
partial: property tests do not exercise JSON transaction matching, full binary
serialization, signing, upstream cryptographic internals, finality, or UI
approval. The quote call path at `XrplSendClient.swift:228` and `:236` was traced;
the full transport/client is not marked reviewed. The Sui and Aptos addition
helpers are production dependencies of these checks; their entire modules are
not marked reviewed. Passing tests do not close any of those gaps.

[GitHub reproduced the pair](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41570338830). The downloaded artifact and its internal source/fixture/result hashes were verified; the original ZIP is retained with checkpoint 15. [Receipt](../evidence/5.0.1-build103/ci-retests/xrpl-amount-github.json).
