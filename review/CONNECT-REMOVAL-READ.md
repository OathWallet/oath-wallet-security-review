# Wallet removal across suspended account reads and permission approval

Build 104 checkpoint 2 fixes [OW-2026-064](../findings/OW-2026-064.md).
The original prerelease tag remains `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d`.
The locally tested repair is `0614556b993f85808b13e3a69984ce36050a8dfe`, merged
in [PR81](https://github.com/devdasx/oath-wallet/pull/81) as
`501915920e99475e63af5fcb9e658f3c834f3cc8`. Both use version 5.0.2 / build 104.
The merge differs from the tested tree only under Website; [exact path evidence](../evidence/5.0.2-build104/connect-removal-read/merge-binding.json)
records this without relabeling the local tests as tests of another commit.

## What failed and what changed

The vault held authenticated contents while awaiting a real database account
lookup. Global lock/reset generations did not change when a particular wallet
was removed. An in-flight message or typed-data request could therefore sign
with those retained contents. Removing and restoring the wallet could likewise
allow an older pending biometric approval to issue a new permission grant.

All 26 signing entry points and permission approval now capture a wallet-specific
removal generation. Successful encrypted removal invalidates that generation
before the next suspension, and clears that wallet's grant. Failed persistence
and unrelated wallet removal preserve existing consent. Lock still changes the
global generation. Existing chain-specific error contracts and persisted formats
are unchanged. A freshly restored wallet can receive fresh authorization.

## Reproducible results

- Actual account-read suspension: **54 pass / 12 fail before; 66 pass after**.
- Pending synthetic biometric consent: **13 pass / 1 fail before; 14 pass after**.
- Broader host regressions: **616 assertions pass across 15 suites** (EVM,
  WalletConnect, permission batch, Solana, TRON, XRP, Stellar, Aptos, Sui, Near,
  TON, THORChain, Arc, wallet lifecycle/reset, and authentication).
- Diagnostics: **119 pass / 2 explicit skips**. Public-source and secret checks,
  diagnostic coverage and unsigned generic iOS Release compilation pass.
- Audit tooling: **330 helper tests pass**; these are distinct from app tests.

[Validation manifest and logs](../evidence/5.0.2-build104/connect-removal-read/validation/manifest.json)
include source pins, durations and hashes. [Earlier attempts](../evidence/5.0.2-build104/connect-removal-read/attempts/manifest.json)
preserve initial fixture setup errors, the smaller exploratory fixture, and two
intermediate fixes that broke existing error contracts. The paused Arc attempt
is retained separately; the resumed completed result is the passing receipt.
The original failed runs have not been erased or counted as passes.

Run from a clean review-repository checkout with a clean app checkout and the
compatible toolchain documented by `scripts/toolchain.sh`:

```sh
git -C /path/to/oath-wallet checkout --detach 0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d
python3 scripts/connect-removal-read.py /path/to/oath-wallet .work/read-build .work/read-before --commit 0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d --expect-vulnerable
git -C /path/to/oath-wallet checkout --detach 1c5a9fab7562dab4583810365ab6b4a2e248d6a1
python3 scripts/pending-consent-removal.py /path/to/oath-wallet .work/read-build .work/consent-before --commit 1c5a9fab7562dab4583810365ab6b4a2e248d6a1 --expect-vulnerable
git -C /path/to/oath-wallet checkout --detach 0614556b993f85808b13e3a69984ce36050a8dfe
python3 scripts/connect-removal-read.py /path/to/oath-wallet .work/read-build .work/read-after --commit 0614556b993f85808b13e3a69984ce36050a8dfe
python3 scripts/pending-consent-removal.py /path/to/oath-wallet .work/read-build .work/consent-after --commit 0614556b993f85808b13e3a69984ce36050a8dfe
```

The scripts require exact named case identities, ordering, expected failures,
summary and exit status. A missed synchronization gate, missing/duplicate case
or unexpected failure is rejected. They clone the pinned source and substitute
only the test entry point and host execution wrapper, then deny networking to
the fixture process. Original/executed harness and fixture hashes are recorded.
The original local pending-consent driver mislabeled its scope as message signing;
its archived copy and receipts are preserved with an explicit correction. That
fixture asserts permission grant issuance, not signatures or relay delivery.

## Source coverage and limits

[Source binding](../evidence/5.0.2-build104/connect-removal-read/source-binding.json)
records all 26 signing-method slices, file hashes, and the baseline/intermediate/
final revisions. This is partial vault review. No whole-file or dependency status
is promoted solely because these tests pass. The focused race fixture exercises
EVM imported-key messages and typed data, not every chain's removal interleaving.
The broader suites check existing signing behavior; they do not expand the race
matrix to all chains. The encrypted envelope and SQLite are real implementations;
credential storage, biometrics, HD derivation and unrelated services use the
host adapters explicitly documented by the harness.

The service has additional membership checks before relay responses. No relay
bypass, blockchain broadcast, unauthorized initial consent or fund loss is
shown. No simulator, device, OS authentication, funded wallet or live provider
was used. Historical binary provenance and unreviewed application/dependency
code remain outstanding. This checkpoint is not a whole-wallet completion verdict.

The pinned read-only [GitHub workflow](../.github/workflows/connect-removal-read.yml)
replays both before/after experiments and separately builds the exact merge.
Hosted results are pending until their terminal receipts are downloaded and
verified. No deployment credentials or App Store job are present.

## Hosted build addendum

The unsigned Release build job in run `41601227473` has now passed at merge `501915920e99475e63af5fcb9e658f3c834f3cc8`. Its downloaded artifact digest, source pin, successful job identity and build-log hash are verified. [Durable evidence](../evidence/5.0.2-build104/hosted-removal-build/manifest.json). The host race-test job was still running at this capture; the build does not establish its result.
