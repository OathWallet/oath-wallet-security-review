# OW-2026-058 reproduction

This is an audit-only fixture. It uses `AUDIT-SNAPSHOT-TEST-NOT-A-PRIVATE-KEY`,
which is deliberately invalid, and never loads a real wallet. Do not install it
on a physical device or include it in a distribution build.

## Host replay

From the review repository, clone the public wallet and run:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-disclosure-source
python3 scripts/private-key-disclosure.py /tmp/oath-disclosure-source /tmp/oath-disclosure-build /tmp/oath-disclosure-results
```

The helper pins the previous public main commit and the repair commit. It overlays
only the same regression fixture and host build harness, verifies the production
model stayed unchanged, and requires each named case and the final summary.
Expected outcomes: before seven pass/four fail; after eleven pass/zero fail.
The host reader is synthetic; this is not an OS biometric or UIKit test.
`private-key-disclosure.yml` provides a read-only GitHub replay without deployment
secrets or physical devices.

## Bounded runtime experiment

The unresolved concern was whether a retained value appears in actual OS-created
app-switcher snapshots when optional privacy is disabled. One isolated iPhone 17
Pro simulator with iOS 27.0 and Xcode 27.0 (27A266a), arm64, was used. This was a
production-component fixture, not a complete wallet creation/export UI test.

Copy `prepare.py` and `Fixture.swift` to a new scratch directory. Archive exact
baseline `c7acd23bb139864a40273f405d18b479589d2b20` into its `source/` child, then
run `python3 prepare.py`. The preparation requires exact replacement matches and
writes `source-injection.json`. It changes only the synthetic initial session,
home content, cloud/rate resume guards and app-only bundle identifier. Production
root lock rules, scene privacy cover, disclosure model and value page remain.
The fixture calls the same lock/background cancellation as the Settings owner.

Run the documented `Tools/PreparePublicBuild.sh` from the source directory when
required by a fresh checkout. Build from the scratch directory:

```sh
xcodebuild build -project source/OathAtmosphere.xcodeproj \
  -scheme OathAtmosphere -configuration Debug \
  -destination 'generic/platform=iOS Simulator' -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO ARCHS=arm64 ONLY_ACTIVE_ARCH=YES
```

Use `xcrun simctl --set <scratch>/devices create` with the installed iPhone 17 Pro
and iOS 27.0 identifiers; boot only that new UUID. Install the fixture, launch
`org.oath.audit.snapshotprobe`, and capture a foreground screenshot after the
fixture text appears. Launch `com.apple.Preferences` to background it. Obtain
its data-container path with `simctl get_app_container ... data`. Copy only
`Documents/snapshot-probe.jsonl` and the files beneath
`Library/SplashBoard/Snapshots`; do not collect unrelated data. The preserved
`runtime-commands.log` identifies the actual commands and the failed setup attempt.

For the after run, replace only `OathPrivateKeyModel.swift` with its exact bytes
from `b5621109b64d606dcf6cd906d2c4f2c2f9e78686`, rebuild, uninstall/reinstall this
fixture to discard prior snapshots, and repeat. The manifest confirms this model
matches the separately compiled production repair. Convert native snapshot KTX
files with `sips -s format png <input.ktx> --out <output.png>`. Preserve original
KTX bytes and hashes, not only screenshots. `OCR.swift` runs Apple Vision on the
recorded before/after filenames. Positive controls must detect the marker in
both foreground screenshots and both before scene snapshots; every after
snapshot must omit it. Visually inspect the before/after scene PNGs too.

The actual evidence also records two failed setup attempts: an unavailable Intel
aezeed slice and an overly broad bundle-ID override. The corrected build uses
arm64 and changes only the app target's ID. A host attempt with buffered stdout
is preserved alongside its flushed rerun. None is silently counted as a pass.

Shut down and delete only the isolated simulator when finished. This check does
not establish every OS/timing sequence, heap zeroization or full export-adapter
runtime coverage. The committed JSON manifests identify source and fixture hashes,
log checksums, outcomes and the exact scope. No App Store or device result is implied.
