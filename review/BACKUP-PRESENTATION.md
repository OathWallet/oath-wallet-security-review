# Backup presentation, secure fields and cancellation

Source scope: 5.0.1 (103),
`c7acd23bb139864a40273f405d18b479589d2b20`. Complete reads covered the all-wallet
backup page/model, backup-password form, SwiftUI secure-input bridge and native
entry field. [Hashes and ranges](../evidence/5.0.1-build103/backup-presentation/source.json).

The confirmed stale failure path is [OW-2026-059](../findings/OW-2026-059.md).
The host replay exercises the real model, with controlled synthetic dependencies;
it does not test the actual iCloud transport or database failure mechanism.
Successful callbacks already recheck ownership after suspension. The repair
extends that same check to errors before changing the current failure/counter.

The password form validates confirmation, disables submission reentry and clears
both input strings before dispatching its accepted value. It also clears on
view disappearance. Settings checks that the session is unlocked and the route
still matches before starting backup. Its lock handling pops ordinary password
editors. The all-wallet model cancels uncommitted preparation on lock/background;
already committed encrypted jobs remain the service's responsibility.

The secure-input bridge uses the native sensitive field with password content
semantics, disables correction and smart substitutions, and clears the field on
dismantle. The native field hides a user-revealed password on edit end, window
removal, disable, application deactivation and scene deactivation. Its visibility
switch preserves editing selection and suppresses programmatic editing feedback.
This is a source observation, not a new UIKit snapshot test. It does not establish
all keyboard, accessibility, autofill, language or system snapshot behavior.

These four files receive partial review dispositions, not completion credit for
all UI/runtime dependencies. The production cloud cryptography, account checks,
transactional database semantics and full export/restore paths retain their own
review and evidence obligations. No simulator or physical device is used in this
backup follow-up.
