# XRP Connect simulation-response validation

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Finding: [OW-2026-061](../findings/OW-2026-061.md).

The test-only before commit is
`f8a6d29803594f1f3a74063e92f90b8155122556`; its production parent is
`6783750661c43d3511d8973a2de77106fdf2001d`. The after commit is
`8a31eb265c34ef7f37ba21741201842366d43b7b`. Tests have identical bytes on both
sides. The affected client at the before commit has identical bytes to the
historical review baseline. Only one production guard changes after it.

## Reproduce from public source

Use the toolchain declared in the pinned audit workflow. Dependency downloads
require network access; test RPC responses are synthetic and optional live-test
flags are stripped. No deployment credentials, signing certificate, simulator,
physical device or funded wallet is needed.

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach f8a6d29803594f1f3a74063e92f90b8155122556
python3 scripts/xrpl-connect-simulation.py wallet scratch evidence/local/simulation/before --before
git -C wallet checkout --detach 8a31eb265c34ef7f37ba21741201842366d43b7b
python3 scripts/xrpl-connect-simulation.py wallet scratch evidence/local/simulation/after
```

Run those Python commands from this review repository. The before command
succeeds only when exactly the expected two methods fail and the other four
pass. Empty runs, skips, extra failures, missing tests and unexpected runner
exits fail verification. Its receipt preserves the underlying failure exit.
The after command requires all six methods to pass. Per-method logs and their
hashes are preserved.

The broader local XRP test selection additionally exercises existing signing,
multisig, account-closure and send-boundary regressions: 43 pass, four live tests
skip. Diagnostics has 119 passes and two explicit skips. Public-source checks,
diagnostics coverage, secret scanning and unsigned generic iOS Release
compilation pass at the after commit. Host execution, compilation and live/UI
behavior are distinct; no live or UI outcome is claimed.

[Evidence manifest](../evidence/5.0.1-build103/xrpl-connect-simulation/manifest.json)
contains hashes, source identity, initial experiments, clean-checkout paired
replay and validation receipts. Historical failures are retained.
