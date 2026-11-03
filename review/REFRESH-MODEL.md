# Refresh activation, completion and presentation state

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

The main-actor controller asks a value-type cycle to start a refresh. The cycle clamps finite pull progress to the interval from zero to one. Moving through the activation distance without a current eligible drag cannot start work. A second start fails while the cycle is active or returning. Acknowledgement, success and failure are distinct states. The gesture tracks whether the pan began near the resting top. Haptic feedback has four bounded steps and checks finiteness before converting to an integer.

We exercised these production types with 100,000 seeded events including non-finite offsets, duplicate starts, cancellation by reset, and mixed presentation results. There were 4,617 accepted activations and 99 feedback events. The existing completion harness passed 251 assertions on tracking, drag, deceleration and stationary frames. The observation harness performed 20,000 idle resets and checked that they did not repeatedly notify observers. The branded cycle and mark harness passed 6,182 geometry and lifecycle assertions. [Reproduce](../scripts/refresh-model.py) · [Evidence](../evidence/recovery-routing/oath53-evidence/refresh/refresh-model.json).

These tests cover state transitions and drawing geometry on the host. The UIKit attachment, hit testing, frame callbacks and accessibility behavior need separate evidence. The listed tests do not access a wallet, start network work or simulate a device.
