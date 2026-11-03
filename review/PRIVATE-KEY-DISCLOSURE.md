# Private-key export: ownership, lifetime and evidence limits

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

**Checkpoint 12 follow-up:** the previously open retention question is now
confirmed as [OW-2026-058](../findings/OW-2026-058.md), with actual synthetic OS
snapshots, a merged source repair and before/after tests. The checkpoint 11
observations below are retained as historical evidence; their pending statements
are superseded by that finding. The 305-check hosted browser run also completed
[successfully](../evidence/5.0.1-build103/ci-retests/private-key-browser-github.json).

The source baseline is 5.0.1 (103),
`c7acd23bb139864a40273f405d18b479589d2b20`. Complete reads cover the private-key
model, pages and application export adapter. The relevant vault/settings owner
sections were traced without treating the whole large files as reviewed.
[Exact ranges and hashes](../evidence/5.0.1-build103/private-key-disclosure/source.json).
No application change or new confirmed vulnerability is claimed in this pass.

## Authorization and derivation

The model only selects an account present in its account/address list. The vault
revalidates that account against the requested wallet, encrypted-vault reference
and stored public metadata before presenting authentication. Composite UTXO IDs
must resolve to a known branch/index and reconstruct to the same exact ID.
PIN export uses the vault's persisted authentication/throttling path; biometric
export checks authentication generation after the prompt. Export cannot unlock
an already locked session. The account list contains public metadata, not keys.

The application adapter checks imported key structure, network scope and derived
address equality. HD export validates ASCII nonhardened numeric path components
before calling Wallet Core and checks the derived address against the stored
account. UTXO exports additionally check the persisted origin path/address,
network and supported recovery format. The production Bitcoin-family helper
reconstructs the descriptor and exact selected address, derives one leaf, then
checks that leaf's public address before returning WIF. Two-factor Electrum
material refuses ordinary single-key export. Imported extended roots are only
returned by the separate top-level imported-key path; the address browser returns
leaf WIFs. Underlying Wallet Core/BDK source and binary provenance remain separate
review obligations.

PIN and biometric operations publish only after checking the model's generation.
Late unacknowledged completions cannot revive a departed flow. Success initially
holds a pending key behind a warning. Acknowledgement reveals it; leaving the
account clears both pending and visible values. The private-key QR sheet requires
an unlocked session and closes on lock/background. Copy uses the sensitive
clipboard helper and requires an unlocked, non-background session.

## Important retention distinction: still under investigation

Unlike the recovery-phrase model, `cancelAuthentication()` intentionally preserves
an **already revealed** private key. Its existing host test explicitly expects
that behavior. The value page renders the retained string without a local
`isUnlocked` condition; it relies on the application's lock presentation. Native
Back to the warning also retains the same authorized selection for re-reveal.
None of these facts alone proves an authorization bypass.

The root keeps its home hierarchy while locked and defers a new native lock
presentation in the background. The scene's blur cover requires
`settings.appSwitcherPrivacy`, whose initial/default value is false. This
combination needs an actual application-level app-switcher snapshot check with a
synthetic revealed key and privacy disabled. **That check has not been run.**
The preceding settled-blur experiment had the cover explicitly attached, so it
cannot resolve this question. The model and pages remain partially reviewed;
retaining screen state is not evidence that every snapshot hides secret text.

## Existing and newly collected host evidence

`Tools/CheckMultiWallet.swift:352–465` tests a foreign account rejected before
biometric prompting, duplicate selection, PIN rejection/lockout, warning before
reveal, clearing an unacknowledged result, and held late biometric completions
after cancellation or lock. The baseline lifecycle/authentication receipts are
linked in [the completed CI snapshot](../evidence/5.0.1-build103/ci-artifacts-checkpoint9.json).
Those tests use synthetic OS/storage/derivation boundaries and do not prove
UIKit snapshot behavior.

The previously unlisted `Tools/CheckHDPrivateKeys.swift` fixture was run on the
exact baseline through `Tools/CheckMultiWallet.py --private-keys`: **305 checks
pass**. It browses inactive-wallet receive/change branches for Bitcoin, Bitcoin
Cash, Litecoin and Dogecoin; exercises search, imported single/extended keys,
unknown addresses and foreign-wallet rejection; decodes exported WIFs and checks
their derived public addresses. [Report and log](../evidence/5.0.1-build103/private-key-disclosure/private-keys.json).

The test's scope needs care: the host harness substitutes the application's key
engine, including `OathWalletEngine.privateKey(for:account:)`. It uses a fixed
synthetic HD seed and calls the real package-level `privateKeyWIF`. Therefore this
is real vault/database/Bitcoin-family helper coverage, **not execution coverage
of `OathPrivateKeyExport.swift` or its non-UTXO encoders**. Reading the application
adapter is recorded separately. The test uses no real wallet data, user Keychain,
OS biometric prompt, simulator, device or live blockchain request. Dependency
downloads during compilation are separate from test network behavior.

The audit runner now requires a completed fixture summary with at least 305 assertions, not just a
successful compile, and includes this check in its required ledger and hosted
matrix. Five result-parser tests reject absent, duplicate, reduced, zero and wrong-scope
summaries. A dedicated GitHub execution is pending publication. Generic iOS
compilation was not repeated for this audit-only change.
