# Sui and XRP history restart boundaries

Build 104 checkpoint 16 repairs [OW-2026-068](../findings/OW-2026-068.md)
and [OW-2026-069](../findings/OW-2026-069.md). The immutable build-104 tag
and all earlier source pins retain their original meaning.

## Reproduce

On macOS with a compatible Swift 6 compiler and Python 3.11 or newer:

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach 05e7917f0a3c26072b1a6b88d2e9e4a0d0310427
python3 scripts/history-restart-boundaries.py wallet scratch/before evidence/local/before --baseline --expected-commit 05e7917f0a3c26072b1a6b88d2e9e4a0d0310427
git -C wallet checkout --detach b3f1f6af98bedfe850d390cac684a563c598e3ac
python3 scripts/history-restart-boundaries.py wallet scratch/after evidence/local/after --expected-commit b3f1f6af98bedfe850d390cac684a563c598e3ac
python3 scripts/history-restart-adjacent.py scratch/after/source scratch/after/build evidence/local/adjacent --expected-commit b3f1f6af98bedfe850d390cac684a563c598e3ac
```

Use fresh output/scratch directories. Dependencies may download at build time;
each selected test process denies networking. The before driver requires the
specific overflow process to terminate with SIGTRAP, two account-binding
assertions to fail, and one boundary control to pass. After repair all four
methods pass. The rejected Sui checkpoint remains unchanged across database reopen.
The adjacent driver rebuilds the requested source and selects existing offline
Sui/XRP ledger and send-journal tests, excluding two live-provider methods.

## Review boundaries

The Sui test uses the real JSON decoder and real database commit/restart APIs.
The synchronizer's expired-cursor path is inspected in source but is not driven
end to end. The two account mismatches are internal API calls: ordinary app
callers use the same ticket for cursor reads and restarts. No app-level account
crossover, signed transaction, secret disclosure or mainnet effect is demonstrated.
The fix rejects a malformed stored checkpoint; it does not discard existing history.

The source inspection also checked pinned Sui inventory reads, ledger-hash-bound
XRP inventory requests, and Stellar's conservative minimum observation ledger.
These observations do not prove all replica/cache behaviors or concurrent app
refresh schedules. No whole-file disposition is promoted merely from these tests.
Remaining application, dependency, binary provenance and runtime gaps remain open.

## Hosted evidence from previous repairs

- [NEAR freshness run 41622627422](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41622627422): two controls pass/four cases fail before; all six pass after; 24 adjacent methods pass. [Verified receipt](../evidence/5.0.2-build104/hosted-near-balance-freshness/manifest.json).
- [TRON/TON freshness run 41626421156](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41626421156): two controls pass/three cases fail before; all five pass after; 27 adjacent methods pass. [Verified receipt](../evidence/5.0.2-build104/hosted-inventory-flight-time/manifest.json).

Both downloaded archives match GitHub's artifact digests. Source, driver,
fixture and case-log hashes were checked. These runs retain their own source
commits; they are not tests of every later change.

## Validation

The paired clean-checkout replay passes on local Xcode 27.2. An initial generic
iOS build stopped because the updated Xcode installation lacked its Metal
compiler. The original failure log is retained, and the missing Apple component
was installed before retrying. The retry passes generic unsigned iOS Release compilation and identifies version
5.0.2 (104). All 22 adjacent methods pass, two live methods are excluded, and
diagnostics record 119 passes and two skips. Public-source validation (4,861
files), diagnostics coverage (722 catch sites), redacted secret scanning and all
379 audit-helper tests pass. The completion gate still reports 16,917 outstanding
review items, not vulnerabilities. [Manifest and raw logs](../evidence/5.0.2-build104/history-restart-boundaries/manifest.json). Hosted replay of this new repair is
tracked separately. No App Store, simulator or physical-device action is included.

Merged in [PR85](https://github.com/devdasx/oath-wallet/pull/85), commit `5e54956e10647ca1b2588fa77b3cbcb9b7884f03`. The complete merge tree matches the tested repair tree (`bb27c96baee31a7a8dc4b86215061a8a667d4caa`). This is a later public-source repair; the original prerelease tag is unchanged.
