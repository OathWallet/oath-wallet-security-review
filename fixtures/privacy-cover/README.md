# Synthetic privacy-cover probe

This fixture hosts the **unchanged production** `OathAppSwitcherPrivacy` over
invented labels. It contains no wallet, recovery phrase, private key, network
client or application database. It answers only whether the settled cover leaves
these labels readable on the selected runtime. It does not test the app's scene
callbacks or UIKit's app-switcher snapshot timing.

Recorded run: Xcode 27.0 (27A266a), XcodeGen 2.45.4, iPhone 17 Pro simulator,
iOS 27.0. The source is pinned to
`c7acd23bb139864a40273f405d18b479589d2b20`.

## Reproduce deliberately

Runtime use is opt-in and must be justified by the unresolved visual question.
This is not part of the automatic CI workflow. Use an empty work directory and
a clean checkout of the pinned public application:

```sh
python3 scripts/privacy-cover-probe.py /path/to/oath-wallet /tmp/oath-privacy-probe --run-simulator
```

The runner builds the minimal fixture, creates a private simulator device set,
captures an uncovered control and settled light/dark covers, captures the dark
compositor, and runs Apple's Vision text recognition. It shuts down and deletes
only the simulator it created. A failed command remains a failure; generated
images and logs remain in the work directory. The runner does not change the
source checkout or contact a physical device.

Inspect all images yourself. Zero OCR detections is not proof against image
reconstruction, other content, accessibility modes or operating-system versions.
The committed evidence predates this convenience runner and was collected with
the equivalent commands manually. The runner's full orchestration has not been
rerun merely to repeat the same runtime check.

## Observed result

The uncovered control has ten recognized labels. Neither covered hierarchy
render has recognized text. The dark compositor has only status-bar text. Visual
inspection found no readable fixture content through either cover. No production
change was justified by this experiment. Actual app-switcher timing remains an
open review boundary.

[Images, toolchain and hashes](../../evidence/5.0.1-build103/privacy-cover/result.json)
