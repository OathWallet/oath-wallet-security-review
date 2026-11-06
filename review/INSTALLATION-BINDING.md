# Installation keys, protected records and recovery boundaries

Maintainer-commissioned, Codex-led review checkpoint 34. App source:
`32701474fefbed3840878e35f6111e8d494e1f02`, Oath Wallet **5.0.3 (105)**.
No newly confirmed application vulnerability or application change is claimed.
The whole-wallet review remains incomplete.

## Attack hypotheses and production trace

A local storage substitution could expose secrets if ciphertext from one purpose
were accepted as a different record, or if records survived installation-key
replacement. The production `OathInstallationSecurity` binds the installation ID
and exact context to AES-GCM authenticated data. Its vault, retry-state, passcode
and biometric adapters supply separate contexts. An I/O failure must not be
interpreted as a new installation and erase or replace still-valid credentials.

The fixture compiles the **complete production implementation**, not an extracted
method or a copied implementation. It substitutes only the key-store and cleanup
protocols with a synchronized synthetic store. It tests protected record reuse,
malformed/tampered ciphertext, key replacement and injected read denial. This is a
fault-injection boundary test; it does not establish an attacker can obtain
sandbox writes, defeat iOS Data Protection, or bypass the device passcode.

Manual tracing also covered inner vault envelopes, PIN/biometric credential
handling, creation/derivation dispatch, backup document authentication and restore
identity checks. Files and exact ranges are separately recorded in the
[source disposition ledger](../evidence/5.0.3-build105/installation-binding/source-binding.json).
These reads do not count as runtime verification or complete dependency review.

Two hypotheses did **not** establish a new High/Critical attack: the apparently
unauthenticated inner-envelope metadata is itself protected by the outer
installation envelope; the simple recovery-words accessor had no production
caller found in the reviewed source. The PIN-change/in-flight-operation question
needs further application-level lifecycle investigation; it is not presented as
a confirmed authorization bypass. Reset/lock/removal generations must still be
validated across every signing entry point.

## Reproduction and results

From a clean audit checkout with Xcode and Python:

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach 32701474fefbed3840878e35f6111e8d494e1f02
python3 scripts/installation-binding-review.py wallet .work/installation-binding evidence/replay/installation-binding
python3 -m unittest discover -s tests -p test_installation_binding_review.py
```

Scratch/output directories must not already exist. The driver verifies the exact
clean source before and after running, uses Swift 6 optimized builds and denies
network access to each test executable. Local Xcode **27.2**, Swift **6.4.2**,
Python **3.14.7**; elapsed **5.473 seconds**, including three separate builds.

- **56 existing production host checks pass.**
- **2,647 new assertions pass, zero fail, zero skip.** These include 12
  cross-purpose substitutions, 2,272 individual ciphertext-bit changes, 284
  truncations, 32 wrong-key variants, exact-context checks, reset/reinstallation
  rejection, read-failure preservation and 64 concurrent prepare calls.
- A separate deliberately weakened build removes context from authenticated
  data. All **12 cross-purpose assertions fail**, exactly as required. A crash,
  skip, unrelated failure or missing result does not satisfy this control.
- The original driver incorrectly expected 57 inherited checks; the production
  baseline actually passed 56 and the driver stopped before compiling the new
  fixture. That attempt and its driver are preserved. Only the expected baseline
  count was corrected before the fresh successful run.

[Manifest](../evidence/5.0.3-build105/installation-binding/manifest.json) ·
[Successful run](../evidence/5.0.3-build105/installation-binding/runs.zip) ·
[Original failed harness attempt](../evidence/5.0.3-build105/installation-binding/attempt1.zip) ·
[Reviewed source snapshots](../evidence/5.0.3-build105/installation-binding/validation.zip).

## Limits and next work

The 12 file/range dispositions remain **partial**. Existing frozen inventory
counts are unchanged. Tests do not promote untouched files or later commits.
Actual iOS Keychain/Face ID, entitlement/access-group behavior, protected-file
lock state, runtime secret-copy lifetime, every reset/cancellation interleaving,
complete backup-version compatibility, and reachable upstream cryptographic
implementations/binary provenance remain separate gaps. Public creation/restore
adapter reads have no new end-to-end runtime result in this checkpoint.

The first [hosted run](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42236729393) failed at the inherited baseline after compilation, with an empty runtime log. Its complete downloaded artifact and terminal GitHub metadata are retained in `hosted-attempt1.zip`. This is not a hosted pass or a confirmed app vulnerability. The driver now records process exit codes and runs a separately labeled unoptimized diagnostic on baseline failure; that diagnostic cannot turn a failed optimized result into a pass. The original local driver and successful evidence remain unchanged. The hosted workflow is pinned, audit-only and read-only. No generic iOS build was rerun
for this audit-only change. No simulator, physical device, App Store or other
application project was operated. No independent certification or zero-bug
claim follows from these results.

The diagnostic [second run](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42239315053) returned SIGTRAP (-5). Its unoptimized diagnostic identified the inherited assertion `Installation key is excluded from device backups`. Both optimized and diagnostic failures are retained in `hosted-attempt2.zip`. A separate public-data file metadata probe compares the runner default temporary directory with scratch storage; this is an investigation, not a waived assertion or hosted pass.

The [third hosted run](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42240138092) again fails the inherited backup-exclusion assertion. Both the default temporary directory and scratch directory have the `com.apple.metadata:com_apple_backup_excludeItem` extended attribute, but a fresh URL's `isExcludedFromBackup` reads **false** for the file and directory. Changing TMPDIR does not resolve it. The evidence is preserved in `hosted-attempt3.zip`; the cause remains unresolved, and this does not establish an iOS backup bypass. The driver now continues the independent cryptographic fixtures after a failed baseline, while returning a failed aggregate status and reporting baseline assertion totals as unknown. This prevents the infrastructure failure from concealing separate results without waiving the failing check.


## Independent hosted cryptographic results; storage failure retained

The [fourth hosted run](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42241547803)
at audit commit `8461ef7507c0d80138ddbc0fe302cf6339a9d06d` is **failed**. The inherited
baseline compiles but traps at the same backup-exclusion assertion; the number
of completed baseline assertions is unknown and is not counted as a pass.
Independent production cryptographic checks then complete: **2,647 pass, zero
fail, zero skip**. The context-removal control fails exactly 12 expected assertions.
The aggregate deliberately returns failure. The driver took **36.549 seconds**,
including diagnostic and separate cryptographic builds. The original local
successful run and all earlier failed hosted attempts remain intact.

[Terminal metadata, downloaded artifact and receipt](../evidence/5.0.3-build105/hosted-installation-binding/verification.json)
are validated by `tests/test_hosted_installation_binding.py`. The hosted storage
failure remains unresolved. These results neither confirm an iOS backup bypass
nor establish that backup protection works on every supported platform.
