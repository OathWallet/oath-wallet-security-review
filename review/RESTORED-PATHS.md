# Restoration path review increment

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Reviewed application commit: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
The complete `OathWalletRestoration.swift` and `Tools/CheckCloudRestore.swift`
were read. Their hashes are in the disposition ledger. The much larger
`CheckMultiWallet.py` harness has not been marked fully reviewed by this change.

The restoration review covered bounded metadata, known networks, unique account
identities, imported-key and multisig descriptor branches, mutually exclusive
secret forms, phrase validation, passphrase compatibility, Solana receive-path
validation, encrypted restoration metadata and duplicate derived-address rejection.
It does not constitute a complete review of every validator/engine called by this file.
The confirmed path defect and its compatibility repair are [OW-2026-007](../findings/OW-2026-007.md).

## Reproduce the host regression

After `python3 scripts/checkout.py`, run:

```sh
python3 scripts/run.py .work/source cloud-restore --output /tmp/restore-evidence
```

For the failed-before run, make a separate checkout of
`15174cdf8378816cad58310206146deeeede546d`, copy only
`Tools/CheckCloudRestore.swift` and `Tools/CheckMultiWallet.py` from the fix commit
into it, then run `python3 Tools/CheckMultiWallet.py --cloud-restore` there.
Do not replace the production restoration implementation. This deliberately dirty
baseline is not accepted by the pinned current-source runner. Its first new
assertion must fail. Both fixtures have identical hashes in the preserved runs.

The host tests use memory substitutes for iOS Keychain/biometrics and Wallet Core
address derivation. Production encrypted vault, backup document and SQL code are
executed; no live iCloud or provider is involved.

## Why the limited simulator check was necessary

The unresolved question was whether the shipped iOS-only Core framework actually
skips unsupported steps and whether removing them changes recovered keys. Host
stubs cannot answer it. `tests/WalletCoreRestoredPath.c` compares the actual keys in
memory without logging them, across seven chains, eight path pairs and two public
seeds. The exact compiler command, binary hashes, fixture hash and output are in
`evidence/restored-path/core-compatibility/`. The earlier seven-chain parent/child
characterization is retained separately in `evidence/derivation-return/`.

To reproduce on an explicitly authorized isolated simulator, compile that C file
using `xcrun clang -target arm64-apple-ios26.0-simulator`, the simulator SDK, and
`-F`/`-Wl,-rpath,` for the two simulator framework directories resolved from the
pinned `Packages/WalletCore/Package.swift`. Link `-framework WalletCore` and
`-framework WalletCoreSwiftProtobuf`; run the executable using
`xcrun simctl spawn <isolated-simulator-id> <absolute-executable-path>`.
The build JSON records every argument. No app installation or UI interaction is
required. Do not run it on a physical phone or on another task's simulator.

## Limits

The tests cover sampled key compatibility and metadata repair, not the full
cryptographic implementation, all possible paths, or end-to-end recovery on iOS.
No new full-app runtime claim is made. HDWallet constructor reachability and secret
lifetime investigations remain open. The source-to-binary relationship of Core
remains unproven. A passing build is compilation evidence only.
