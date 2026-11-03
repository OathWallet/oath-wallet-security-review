# App entry, onboarding ownership and scene lifecycle

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Complete source reads cover `OathApp/OathAtmosphereApp.swift` (480 lines), `OathApp/OathSceneDelegate.swift` (348 lines) and `OathAtmosphere/Passcode/OathBiometricPresentation.swift` (48 lines) at the immutable 5.0.1 (103) baseline. All four files in the [source receipt](../evidence/5.0.1-build103/app-entry/source.json) are byte-identical in the later tested application tree `235a730de504e47fb961c34f68f9426ffdbdfe6d`. This is source review, not a new runtime proof or App Store binary comparison.

The SwiftUI and retained UIKit scene delegates share a context. Startup loads local settings and wallet state concurrently; a canceled task or replaced connection UUID cannot publish readiness. State restoration is completed through defer on the startup path. Scene observers are removed on reconnection/disconnection; incoming links enter the same inbox while readiness is pending. Link payload validation remains the separate inbox/parser boundary. Debug visual fixtures are compiled only for Debug simulator configurations.

The root preserves the home hierarchy behind the lock, disables/accessibility-hides locked content and uses the initial inline cover separately from later native lock presentation. A late unlock after entering the background re-applies the background policy. The scene callback updates privacy state synchronously, then invokes wallet background locking. Disconnect cancels startup, invalidates the connection and requests locking only for a real home/locked session; a fresh onboarding state is not converted into a fabricated protected wallet.

Onboarding destinations contain route values and a wallet identifier, not raw recovery/private-key strings. Pending validated secret material lives in view state. Source callbacks check the current route before advancing. Leaving the corresponding passcode route clears the pending material; leaving the source screen clears its draft. Multisignature pending values are cleared together, preventing the inspected back-navigation sequence from selecting another chain's previous material. Completion delegates persistence/authentication to the setup store, clears pending material and proceeds to customization. The customization route hides back navigation after vault commitment. This source tracing does not establish SwiftUI memory zeroization or every visual navigation interleaving.

Biometric presentation tracks independent request UUIDs and posts only on real begin/end transitions. Another instance's requests do not change its state. Privacy policy exempts the owned biometric interruption while inactive; a background transition always requires a cover, and late biometric callbacks cannot remove that background requirement. Presentation bookkeeping does not grant wallet authorization.

Existing exact-baseline GitHub receipts cover 123 biometric fallback checks and 158 security checks, 144 wallet lifecycle and 37 reset checks, plus 28 protected-startup checks. They compile relevant production logic with synthetic storage/OS boundaries. The biometric fixture explicitly covers overlapping requests, duplicate completions, another instance's prompt, and background transitions. These checks do not execute the UIKit/SwiftUI scene delegates themselves. [Hash-linked reports and logs](../evidence/5.0.1-build103/ci-artifacts-checkpoint8.json) · [Host fixture source](https://github.com/devdasx/oath-wallet/blob/c7acd23bb139864a40273f405d18b479589d2b20/Tools/CheckBiometricFallback.swift#L101-L143).

The privacy-cover view was read in full but remains partial: it uses an ultra-thin material blur plus a translucent shade (opaque background with Reduce Transparency). Source review cannot establish that sensitive text is unreadable in every rendered snapshot, or prove UIKit snapshot ordering on all lifecycle paths. A targeted synthetic visual/runtime check is still required for that concern. No simulator or physical device was used in this pass. No application source changed and no vulnerability was confirmed in these files.

## Follow-up: settled cover rendering

The subsequent targeted experiment used one isolated iPhone 17 Pro simulator on
iOS 27.0, with synthetic labels and the unchanged production cover. The uncovered
control was readable. Neither settled light/dark cover left fixture text visually
readable; Vision recognized ten control labels, zero labels in the covered
hierarchy renders, and only status-bar content in the dark compositor screenshot.
The simulator was shut down after capture. No full wallet app, real wallet data or
physical device was used. [Images, toolchain and hashes](../evidence/5.0.1-build103/privacy-cover/result.json)
· [Reproduction fixture and limits](../fixtures/privacy-cover/README.md).

This resolves the narrow legibility question for those captures, not UIKit's
actual app-switcher snapshot ordering. The cover was attached directly and
allowed to settle for one second. Other runtime/accessibility combinations and
image reconstruction are not tested. The file remains partially reviewed; no
production fix was justified by this negative experiment.
