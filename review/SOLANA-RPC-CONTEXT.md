# Solana WalletConnect RPC-context review

This maintainer-commissioned, Codex-led checkpoint traces Solana review and
blockhash-expiry response validation. It is not independent certification.

## Source and finding

- Baseline: `02ec5362c188134c42632c555ed5401218d653cb`, public 5.0.3 (105).
- Repair: `e888b220d7c245aaac5b3911ed4f7c72ca5743bd`.
- [Merged PR #100](https://github.com/OathWallet/oath-wallet/pull/100):
  `3338d294f08388655ffd4cfc3e50656f304e1c6c`. Only separate website changes differ
  from the tested repair; application inputs are identical.
- Finding: [OW-2026-075](../findings/OW-2026-075.md).
- [Scoped source ledger](../evidence/5.0.3-build105/solana-context/source-binding.json).

Several reads sent `minContextSlot` but consumed only `value`, leaving the
response context unchecked. Simulation may advance past the original account
snapshot, yet subsequent fee and mint queries used older minimums. The existing
native-send response validator now guards those reads, and dependent queries
and the returned review carry the simulation slot.

Solana documents a response containing `context` and `value` for
[simulation](https://solana.com/docs/rpc/http/simulatetransaction),
[fees](https://solana.com/docs/rpc/http/getfeeformessage) and
[blockhash validity](https://solana.com/docs/rpc/http/isblockhashvalid), together
with the `minContextSlot` request parameter. These are schema checks against the
requested lower bound; they do not prove provider honesty or make multiple reads
an atomic chain snapshot.

## Reproduce

With Python 3.14 and a compatible macOS/Xcode toolchain, clone the application and
this audit repository, check out the repair commit, and use fresh output paths:

```sh
python3 scripts/solana-context-review.py ../wallet ../context-build ../context-results
python3 -m unittest discover -s tests -p test_solana_context_review.py
```

The driver builds separate immutable package snapshots with pinned dependencies
and injects the identical eleven-method fixture. It records source, fixture,
lockfile, executable and individual log hashes. Public dependencies can be
fetched during compilation; each XCTest process denies networking. Injected RPC
responses use existing public SDK transaction vectors and no funded accounts.

The baseline must pass all three controls and fail the other eight methods with
only their specific context/slot assertions. Compilation errors, crashes or
unrelated failures do not qualify. The repaired selection includes every
`WalletConnectSolana` host method, not just the new fixture. Each runs in a fresh
process, with at most four processes at once.

## Validation

The clean-snapshot paired driver completed in 190.547 seconds. It records
three passing controls and eight expected failed methods before repair; all 52
selected methods pass afterward, with no skips. Each test process denies networking.
The fixture is identical across both builds; their executable hashes differ.

The diagnostics suite passed 119 methods, skipped two and failed none. Its
fresh-process trace case was separately run with networking denied and passed.
The optional public-provider fixture case was not enabled. Coverage passed for
722 catch sites; public-release validation, direct secret scanning and diff
checks passed. Original skipped checks and exploratory harness failures are
retained rather than relabeled as passes.

An unsigned generic iOS **Release** build succeeded on Xcode 27.2 (27B52),
Swift 6.4.2. The product reports 5.0.3 (105). The receipt binds its executable
hash to the exact repair commit; it does not claim runtime or App Store verification.

[Manifest](../evidence/5.0.3-build105/solana-context/manifest.json),
[paired logs](../evidence/5.0.3-build105/solana-context/runs.zip),
[additional validation](../evidence/5.0.3-build105/solana-context/validation.zip)
and [build receipt](../evidence/5.0.3-build105/solana-context/build-receipt.json)
identify exact evidence. Hosted replay succeeded and its downloaded artifact is hash-verified.

## Remaining scope

The frozen inventory remains unchanged. The supplemental ledger covers only
specific provider-validation code, the native validator, the pending-recovery
caller trace and the regression fixture. It does not mark every surrounding
implementation reviewed because tests pass. Full pending-journal integration,
provider honesty, all instruction semantics, UI behavior, dependency provenance
and whole-wallet completion remain open. No simulator or physical device was
used. No App Store upload or release-tag movement is included.

## Hosted replay receipt

[GitHub run 42203666265](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42203666265) completed successfully. The downloaded artifact matches GitHub's SHA-256 digest; every recorded file and case log hash matches. It reproduces the three baseline controls, eight expected failures, and 52 repaired passes. The [receipt](../evidence/5.0.3-build105/hosted-solana-context/verification.json) preserves the exact run and source bindings. This supersedes the original pending observation without changing its pinned evidence.
