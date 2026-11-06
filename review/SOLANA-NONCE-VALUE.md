# Solana durable-nonce response presence review

This is a maintainer-commissioned, Codex-led checkpoint, not independent
certification. It follows the earlier response-context review into the
durable-nonce branch and its pending-recovery caller.

## Source and behavior

- Baseline: `193912d31c602cce314f540b2bafb64f8606bfbd`, public 5.0.3 (105).
- Repair: `6a8bfcfcf6aeabdd858c9f3316ff4bdaeaf245a1`.
- Public merge: [PR #105](https://github.com/OathWallet/oath-wallet/pull/105),
  `658245d197592c89c071a946fda0baf8bf93fb41`.
- Finding: [OW-2026-076](../findings/OW-2026-076.md).
- [Scoped source ledger](../evidence/5.0.3-build105/solana-nonce-value/source-binding.json).

The [Solana getAccountInfo schema](https://solana.com/docs/rpc/http/getaccountinfo)
requires a `value` that is an account object or explicit null. The old nonce
validator checked the context but mapped a missing `value` to null. Both the
pending-validity helper and the first review step could therefore mistake an
incomplete response for expiry evidence. Reusing the existing value validator
rejects absence of the member before interpreting its contents.

The recovery caller checks transaction age, retries submission, and rechecks
signature status before settling as expired. These conditions were traced in
source; the test does not recreate that entire service lifecycle. Terminal
database settlement and pending-query exclusion were likewise source-traced.
The fix preserves these conditions and only corrects the provider-data input.

## Reproduce

With Python 3.14 and a compatible macOS/Xcode toolchain, check out the repair in
the public application repository and use fresh output directories:

```sh
python3 scripts/solana-nonce-value-review.py ../wallet ../nonce-build ../nonce-results
python3 -m unittest discover -s tests -p test_solana_nonce_value_review.py
```

The driver builds immutable package archives at both commits, injects the same
six-method fixture, and pins dependency resolution. Individual XCTest processes
deny all networking and use only public synthetic vectors and injected replies.
It checks four baseline controls and two specific failing methods. A build
failure, crash, skipped case, empty selection or unrelated assertion does not
count as reproduction. The repaired selection covers all WalletConnectSolana
host methods, with at most four test processes at once.

## Validation

The fresh paired run took **187.888 seconds** on the macOS host. The baseline
has **4 passing controls and 2 expected failing methods**. After repair, the
same six methods and 52 adjacent methods pass: **58 passed, 0 skipped, 0 failed**.
The expected failures concern missing-value validity and review, not build errors
or crashes. Each method runs in a separate process with networking denied.

The diagnostics suite records **119 passed, 2 skipped, 0 failed**. Its opt-in
trace case additionally passes in a fresh network-denied process; the earlier
skipped invocation is preserved. The other opt-in live case remains skipped.
Diagnostic coverage and application public-source/secret scans pass. These checks supplement
the scoped source review and do not establish complete application coverage.

Unsigned generic iOS **Release builds pass separately at the repair and merge
commits**, using Xcode 27.2 (27B52), Swift 6.4.2. Both identify 5.0.3 (105).
The merge contains intervening Receive UI and website/documentation changes, so
the whole application trees are not claimed identical. The reviewed packages
and recovery-service inputs are identical. The merged build retains 120 warning
occurrences for 24 existing unassigned image-set assets, and no build errors.

The [manifest](../evidence/5.0.3-build105/solana-nonce-value/manifest.json)
binds the paired logs, exploratory attempts, scoped source copies, separate
builds and PR receipt. The six source dispositions remain partial except for
the fully read regression fixture. A pinned, audit-only GitHub replay is
configured; its result is pending and is not included in the passing totals.

The audit repository's raw scan reports 3,953 matches in unchanged historical
evidence. It is not counted as a passing scan. A separate scan of this checkpoint's
changed files and unpacked evidence reports no matches. The classification and
both logs remain in the manifest. All 465 evidence-helper tests pass, while the
whole-review gate correctly fails with 16,916 outstanding inventory items.

## Remaining scope

The frozen inventory remains unchanged. Supplemental dispositions cover only
the nonce response path, JSON member semantics, shared value validator, recovery
caller, terminal journal handling and the regression fixture. Surrounding
implementations remain partially reviewed. Passing these cases does not prove provider honesty,
full pending-journal runtime behavior, UI behavior, dependency
provenance or whole-wallet completion.

No simulator or physical device was used. No production transaction, App Store
upload or release-tag movement is included. Build 105 remains a prerelease;
fixes in public source are not represented as already shipped by Apple.
