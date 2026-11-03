# Delayed authorization and wallet removal

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

This checkpoint follows the pending-journal removal repair. It tests one
specific question: can a delayed biometric result return an EVM message or
EIP-712 signature for a wallet removed while authentication was pending?
It does not close the separate gap between signing, SQL journal insertion and
vault lifecycle persistence.

## Source traced

The selected functions at tested app commit
`0e91ce56f91ef56b3e45629967e01e449be0052f` have identical text at baseline
`c7acd23bb139864a40273f405d18b479589d2b20`. Per-function hashes and line ranges
are recorded in the evidence source trace.

- `OathWalletVault.openWithBiometrics` prompts through its credential store,
  then rereads the persisted encrypted envelope. It checks credential identity,
  biometric policy, authentication generation and task cancellation.
- `signWalletConnectMessage` and `signWalletConnectTypedData` choose an active
  wallet from the authenticated contents, bind the database account to that
  wallet, then sign and recheck the authentication generation. The imported-key
  engine binds key scope/derivation, verifies the address and enforces typed-data
  chain binding. HD derivation is outside the new runtime fixture.
- Removal authorization binds wallet IDs, removal kind and an expiry. Removal
  validates pending work before persisting lifecycle changes. `walletMutation`
  prevents new mutation/signing entry, but it is not a cross-database transaction.
- `OathWalletSession.changeWallet` changes session generation, cancels listed
  refresh work and reloads the home/session after the vault operation. These
  statements are source tracing; the new fixture calls the vault directly.
- The WalletConnect service checks current session wallet membership and the
  peer's chain/method/account grants before returning a response. The service
  and its relay are not executed in this fixture.

## Experiment

The fixture uses keys 1 and 2 solely as public synthetic test material, an
actual encrypted vault and temporary SQLite database, and the production EVM
imported-key message and typed-data signers. It uses the existing host harness's
in-memory credential and biometric stores, synthetic HD profile adapter and
non-network substitutes for unrelated services. It does not test Apple's
Keychain/Face ID, UI navigation or a WalletConnect peer.

For each signature type, the fixture first verifies a valid signature, holds
biometric completion, then performs one of six actions: soft removal, permanent
removal, remove-and-restore, removal of another wallet, rejected vault write,
or locking. It releases the delayed result and checks the expected signature
or rejection. A rejected write is checked before accepting that control.
No timing sleep determines the interleaving: the fixture observes the explicit
biometric continuation before mutation. A bounded readiness failure fails the run.

The negative control changes only the temporary copy's biometric completion
from decoding the latest stored envelope to using the pre-prompt envelope.
It must produce exactly two failures, the message and typed-data soft-removal
checks. A passing negative control alone would mean the tests missed the stale
snapshot; the wrapper requires the failures and retains the nonzero exit.

## Reproduction

On macOS with the pinned source checked out cleanly:

```sh
python3 scripts/connect-removal-auth.py /path/to/oath-wallet .work/auth-build .work/auth-results/replay
python3 scripts/connect-removal-auth.py /path/to/oath-wallet .work/auth-build .work/auth-results/mutant --mutate-stored-envelope
```

The wrapper clones the exact source and replaces only the test entry point;
its alternate run additionally applies the documented deliberate mutation.
It records original/compiled source, fixture, harness and wrapper hashes.
The inherited harness builds first, then the wrapper runs the fixture binary
with network access denied. Dependencies can download during the separate build.

No new defect is established by these delayed-biometric scenarios. This does
not prove every asynchronous account read/signing/journal/removal interleaving,
OS biometric timing, HD derivation or chain signer. The complete audit remains
in progress. No application source change or App Store operation is included.

## Coverage disposition

The 54-line baseline `WalletLifecycle.swift` was read in full: reorder requires
an exact duplicate-free active-wallet set inside one writer; lifecycle replay
rejects non-finite times, requires each wallet and invalidates sync generations
and scan IDs, disables backups and clears the selected ID when removing it.
Its removal preflight defect is OW-2026-062, fixed after the baseline. Its
cross-store interleavings and extreme sync-counter values remain untested; the
file therefore gains only a partial disposition.

The selected vault, session and Connect authorization functions have explicit
partial scopes in the source trace. Session and Connect service behavior is
not claimed as runtime-tested by the vault-only fixture. No scanner or passing
case promotes the remainder of these files to reviewed status.

## Verified local results

The initial experiment and isolated network-denied replay each pass **38 checks**.
The deliberately stale snapshot produces **36 passes and exactly two failures**;
the original nonzero process exit and logs are retained. No new application bug
was confirmed by this matrix. Source traces bind eleven selected function texts
to both the tested revision and baseline.

[Manifest and logs](../evidence/5.0.1-build103/connect-removal-auth/manifest.json) ·
[Read-only pinned workflow](../.github/workflows/connect-removal-auth.yml).
Local toolchain: Xcode 27.0 (27A266a), Swift 6.4, Python 3.14.7. The hosted workflow
pins Xcode 27.1 and reports its result separately. No new iOS build is claimed
for this audit-only change; checkpoint 19 compiled the same app revision.
