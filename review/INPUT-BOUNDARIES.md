# Scanner, external-link and pairing-input review

Source target: `a65601b78f86e33ebae08a754035d69c1f5f5e43`.
This is source review plus bounded host testing, not a whole-wallet verdict.

## Source inspected

- `OathScanAddress.swift`: ASCII/length admission; EVM checksum checks; network
  ambiguity; fallback NEAR names; offline per-chain address adapters; embedded
  Stellar/XRP routing IDs; Base32/Base58/checksum implementations. Called chain
  adapters are not all manually reviewed by this read. These codecs do not sign.
- `OathScanPayload.swift`: 8 KiB input cap; secret/address/URI classification;
  amount normalization without floating-point conversion; duplicate/required
  query-field policy; explicit network restrictions, token identity, memo and
  expiry handling. Payment routing prepares review rather than authorization.
  Dictionary and address-decoder internals remain separately tracked dependencies.
- `OathWalletLink.swift`: allowed native/universal origins; rejection of nested
  payment wrappers/secret imports; pending-link coalescing; expiry recheck after
  unlock; active-consent preservation. Its URI validation led to OW-2026-006 when
  compared with the next SDK parsing stage.
- `OathScanRecognizer.swift`: shared dictionary task, serialized classification,
  cold address path without dictionary load, cancellation after the awaited load;
  private-key context classifies bounded input but does not validate/import a key.
- `OathMnemonicValidator.swift`: resource manifest/digest checks, 2,048-word
  uniqueness, normalization, language/word-count/checksum validation, bounded
  autocomplete and UTF-16 ranges. Strings and Foundation copies are not proven
  zeroized; clearing an entropy buffer is not proof all copies were erased.
- `OathScanImage.swift`: encoded-byte limit, ImageIO thumbnail bounds, QR-only
  Vision request, bounded payload and result count. ImageIO/Vision internals and
  hostile compressed-image decoder behavior are outside this source read.
- `OathScannerCaptureState.swift`: short locked state transitions, generation
  invalidation, once-per-activation delivery and handoff phases. This is distinct
  from the AVFoundation camera runtime.
- `WalletConnectURI.swift`, `RelayProtocolOptions.swift` and the CharacterSet
  extension: input decoding, protocol/query serialization, encoded whole-URI
  compatibility and duplicate handling. See OW-2026-006 for the confirmed repair.
- `Tools/CheckScanner.py`, `CheckWalletLinks.swift`, `CheckScannerPerformance.swift`,
  `CheckWalletConnectSDK.py`, `URIBoundaryTests.swift` and the existing upstream
  `WalletConnectURITests.swift`: reviewed harness execution, fixtures and assertions.
  The scanner harness copies production files, extracts the network registry and
  links production host-compatible packages. The SDK harness now additionally runs
  the 13 unchanged upstream URI compatibility cases. A harness is not the full app.

## Partial reads and remaining concerns

`OathScannerCamera.swift` was read for queue ownership, callback invalidation,
permission changes and shutdown. AVFoundation/UIView lifecycle races are not
resolved by the host state-machine tests, so its disposition remains partial.
`OathVaultImportFlow.swift` was read for inbox/lock gates, consumed references,
detached preparation and restoration. The whole presenter lifetime, lock/import
race and first-time passcode flow still need a complete trace. No new handoff
vulnerability is asserted. `OathVaultImportPreparation.swift` was reread; its
existing review and key/address agreement checks remain recorded in READ-NOTES.
Only relevant sections of OathSceneDelegate and OathHomeScreen were inspected;
these partial traces do not promote those whole files to reviewed.

A scan for force unwraps/preconditions prompted limited reads of TonAmount,
TonSendPlan, TonSendClient and ArtworkImage. No reachable crash was reproduced in
those reads, and they are not marked fully reviewed. The TON request helper only
returns nil for explicit optional not-found responses; a force unwrap alone is
not evidence of a remote crash. Arithmetic and SVG-expansion boundaries need
further systematic review.

The SDK's method-only `awaitResponse` convenience API remains a review candidate;
the observed direct caller is in the unused Notify product. No new finding or
fix is claimed for it. SDK convenience UIKit URI initializers and actual pairing
with another peer were not runtime-tested.

## Recorded validation on this target

- Scanner: 13,635 assertions; 715 generated CoreImage/Vision QR round trips;
  42 chains; 260 public BIP39 vectors across ten languages.
- Wallet links: 145 assertions.
- Recognizer/capture-state lifecycle: 2,021 assertions, including an unfinished
  dictionary load and cancellation. Host timing observations are not iPhone
  performance measurements or end-to-end camera validation.
- Pairing URI before/after: identical eight-case corpus, 3 pass/5 fail before,
  8 pass after. A separate production app-parser harness checks that the encoded
  fixture reaches the SDK unchanged and a raw duplicate is rejected.

Evidence lives under `evidence/uri-boundary`. No camera, simulator, physical phone,
production relay, real secret or transaction was used. Existing scanner tests are
regressions, not a newly completed fuzz campaign or proof that every input is safe.
