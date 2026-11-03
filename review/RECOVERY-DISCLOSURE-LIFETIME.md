# Recovery disclosure and passcode setup ownership

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

This source pass uses the immutable 5.0.1 (103) baseline
`c7acd23bb139864a40273f405d18b479589d2b20`. The [receipt](../evidence/5.0.1-build103/recovery-lifetime/source.json)
identifies exact files, hashes and read ranges. No application source changed and
no new vulnerability was confirmed in this pass.

## Recovery model and its callers

The complete recovery model was read. It binds the reader to an immutable wallet
identifier. Warning acknowledgement allows one authentication operation at a
time. Both biometric and PIN completions check a generation token and task
cancellation before publishing material. Cancellation changes the generation,
cancels work, clears all eleven multisignature representations, words and the
optional passphrase, and returns a revealed/authenticating model to the warning.
Expected biometric failures offer PIN entry; locked/unavailable wallets do not
publish material. This does not establish memory zeroization of Swift strings
or independence of all upstream reader implementations.

The settings sheet cancels recovery on lock and background. Navigation back to a
warning/PIN page clears material; navigating outside this wallet's recovery
routes clears and releases the model. Sheet disappearance also clears it.
Destination construction checks the model's wallet identifier against the route.
These are traced sections of the large settings file, not a full-file review.

The separate backup-offer sheet initially looked different: it has no direct
`isUnlocked` observer. Tracing its owner resolves that suspicion. The home screen
dismisses its backup sheet when locked, changing wallets or changing profiles;
the sheet's disappearance clears recovery. The sheet itself clears on background,
guards rendering/actions against the active wallet/session state, and constructs
its recovery model for the opening wallet. The owner's dismissal path is source
evidence, not a runtime proof of every SwiftUI transition. This suspected gap was
not promoted to a finding.

Recovery pages guard authentication and copy actions against a locked/background
session, clear entered PIN digits on inactivity/disappearance, and use the
sensitive clipboard helper. Passphrase text selection is disabled. Separate
multisignature rendering, the vault reader, clipboard implementation and actual
screen teardown remain their own review boundaries. No real recovery data was
opened or copied.

Existing exact-baseline host fixtures exercise fresh inactive-wallet PIN and
biometric authorization, an unknown wallet rejected before prompting, duplicate
acknowledgement, incorrect PINs and lockout, cancellation clearing words and a
passphrase, and a held late biometric response rejected after cancellation/lock.
See `Tools/CheckMultiWallet.swift:260–345` and the hash-linked
[baseline records](../evidence/5.0.1-build103/ci-artifacts-checkpoint9.json).
The seven biometric failure modes in `Tools/CheckBiometricFallback.swift:150–220`
cover recovery, private-key export and other protected actions. These fixtures
do not execute SwiftUI views or establish clearing of every allocator copy.

## Setup and automatic biometric prompting

Complete reads cover the passcode setup model, setup screen, standalone verifier
store, biometric result definitions, device wrapper and automatic prompt policy.
Setup validates six decimal digits, discards mismatched entries, invalidates
delayed transitions on reset, and waits for a committed save before enrollment.
An in-flight local save is deliberately not reported as canceled after success.
Biometric failure offers retry or continuation with the saved PIN; completion is
claimed once and deferred while backgrounded. The screen disables input while
inactive and wires suspension/resume/disappearance to the model. Native back
gesture interception and complete setup-store transaction behavior remain
separate boundaries; those larger files stay partially reviewed.

The reusable standalone verifier uses a 32-byte random salt, PBKDF2-HMAC-SHA256
with 600,000 iterations and a 32-byte verifier. Insert-only Keychain storage uses
WhenUnlockedThisDeviceOnly, explicitly disables synchronization and seals the
record through installation security. Its comment correctly distinguishes this
standalone store from the app's injected wallet/setup transaction. Read-time
unlock policy is not implemented here. The existing setup fixture includes an
independent PBKDF2 vector, duplicate-insert preservation and Keychain error
mapping; reading that fixture is not a claim that it was rerun in this pass.

The device wrapper delegates enrollment to the previously reviewed credential
store without claiming success itself. The automatic prompt policy consumes an
attempt only when active, idle, biometrics-capable and without PIN input or a
notice. A manual attempt suppresses another automatic prompt until a real
background visit. It grants no authorization. A focused host replay of the
existing production-policy fixture is recorded separately in this directory's
evidence; it does not present Face ID or access Keychain.

## Remaining limits

Source review dispositions are per file and scoped, not an endorsement of the
whole authorization system. UI lifecycle scheduling, native navigation,
multisignature display, reader implementation boundaries and Swift memory
retention are not closed by these reads. The large home/settings files only gain
additional partial evidence. Passcode and recovery UI runtime checks were not run.
