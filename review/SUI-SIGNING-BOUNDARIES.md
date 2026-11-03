# Sui signing and transaction-buffer boundaries

Build 104 checkpoint 17. This is a scoped continuation of the
maintainer-commissioned, Codex-led review, not completion of the whole audit.

## Pins and source trace

Before: `b3f1f6af98bedfe850d390cac684a563c598e3ac`. Its tree is identical to
the public PR85 merge `5e54956e10647ca1b2588fa77b3cbcb9b7884f03`.
Repair: `018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0`.
The original 5.0.2 (104) prerelease tag is not moved.

Complete files read here include SuiSendPlan, SuiSendCrypto, SuiMultisig,
SuiSendClient, SuiModels, WalletConnectSui, the Sui send model/service and wallet
adapter, and the database Sui send journal. The vault's `signSuiSend` function
was traced as an excerpt only. These reads are scoped partial dispositions;
they do not establish complete protocol or application integration coverage.

- Locally constructed ordinary transfers bind sender, recipient, asset, amount,
  gas and expiration into the serialized bytes. Plan validation precedes signing
  and serialization. Monetary sums use overflow reporting; native transfers
  reserve the gas budget, and token transfers retain token units.
- Ed25519 signatures cover Blake2b-256 of the transaction intent and exact bytes.
  Verification checks the digest and signer-derived address. Multisig parsing
  bounds member/signature counts, requires sorted unique keys, checks the bitmap,
  threshold and member signatures, and rejects trailing envelope bytes.
- The app traces a wallet/account/asset-bound queued plan through authentication,
  repeats generation checks around suspension points, and journals exact bytes
  before broadcast. This is source tracing, not a new end-to-end app test.
- Provider queries verify chain identity; funding validates owner and coin type.
  Writes reconcile by digest and fallback reuses exact signed bytes. Mocked
  transport tests cover selected failures, not every provider/cache interleaving.

## Confirmed repair

[OW-2026-070](../findings/OW-2026-070.md) reproduces a Data-slice crash in the
WalletConnect transaction parser. The before run has one passing ordinary-buffer
control and two SIGTRAP terminations. The repair normalizes buffer indexes before
reading. Ordinary RPC base64 input does not demonstrate the failing slice shape;
the finding remains limited to parser robustness.

## Independent and adversarial checks

Python's `hashlib.blake2b` generates 336 vectors across four digest lengths and
84 deterministic input lengths/patterns, including compression-block boundaries.
An independently structured integer/divmod Base58 encoder checks selected short
inputs, including leading zero bytes. The production hash implementation is also
tested with nonzero-origin slices.

Six new host methods check these vectors; every signature-byte flip and every
transaction-byte flip in a synthetic single-signature transaction; wrong signing
intents; signature truncation/trailing bytes; multisig envelope flips/truncations;
duplicate, missing and foreign signers; 14 decoded invalid plan mutations; quote
age limits and the largest nonoverflowing expiration epoch. This is bounded
deterministic testing, not exhaustive fuzzing or a proof of cryptographic security.

The initial selection passed all 21 methods (six new, 15 existing). Three live
test methods were explicitly excluded. Existing SDK transaction/signature fixtures
are checked, but their upstream generation provenance is not re-established here.
Runtime network access is denied, and inherited opt-in environment variables are
removed. The fixture uses only published synthetic key patterns.

The final repair run passes all 34 selected signing/WalletConnect methods, plus
the three paired parser regression methods. Three real-network methods remain
excluded. The method named `testLiveReviewUsesNetworkSimulationAndNativeUnits`
uses a fully synthetic transport and is included; its name is not a live-network
claim. [Results and original logs](../evidence/5.0.2-build104/sui-signing-boundaries/manifest.json).

## Reproduction

From a clean public source checkout at the specified pin, on compatible macOS
with Xcode and Swift installed:

```sh
python3 scripts/sui-transaction-slices.py /path/to/wallet /tmp/sui-before /tmp/sui-before-results --baseline --expected-commit b3f1f6af98bedfe850d390cac684a563c598e3ac
# Check out the repair commit before these two commands.
python3 scripts/sui-transaction-slices.py /path/to/wallet /tmp/sui-after /tmp/sui-after-results --expected-commit 018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0
python3 scripts/sui-signing-boundaries.py /path/to/wallet /tmp/sui-signing /tmp/sui-signing-results --expected-commit 018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0
```

Use fresh output directories. Dependency acquisition may use the network; test
execution is separately network-denied. `--build-cache` can reuse an isolated
package build directory; the driver always rebuilds before running tests. The
initial 21-method driver is preserved byte-for-byte in its evidence archive. The
final driver adds explicit commit selection and 13 adjacent WalletConnect methods;
this fixture/selection expansion is not a new application failure.

## Validation and retained attempts

The three parser regressions and 34 signing/WalletConnect methods pass on the
repair. Diagnostics execute 121 methods: 119 pass, two explicitly skip. Public
source validation, diagnostic catch coverage and a redacted secret scan pass.
The generic unsigned iOS Release build passes and its Info.plist reports 5.0.2
(104). All 383 audit-helper tests pass after regenerating the compiler coverage join
from the updated canonical dispositions. The initial stale-join assertion failure
is retained; no test assertion was relaxed to obtain the pass.

The first diagnostics command wrapped both compilation and execution in the
network sandbox. SwiftPM could not apply its nested manifest sandbox. Its failure
log is retained; the corrected command builds first, then runs the compiled test
bundle with networking denied. This was a harness setup failure, not an app
diagnostics failure. Local toolchain: Xcode 27.2 (27B52), Swift 6.4.2. Hosted replay
pins Xcode 27.1 and is tracked separately.

The completion gate still reports 16,917 outstanding review/validation items,
not 16,917 confirmed vulnerabilities. Ten source files have hash-bound partial
dispositions; nine compiler inputs move from outstanding to partial. No partial
review is treated as completed coverage.

## Limitations and continuation

The inherited SDK fixtures still need independent regeneration with a pinned
upstream toolchain. Full BCS command semantics, Move execution, node acceptance,
gas ownership under every command, protocol-version compatibility and every
WalletConnect review/simulation interleaving remain open. Quote-display getters
assume a validated plan; the observed app path uses validated quotes, so no
reachable getter-underflow finding is asserted. A full hostile persisted-state
analysis is still outstanding.

No UI, simulator, physical device or live transaction was run. No App Store
upload or submission is part of this checkpoint. The full audit stays incomplete.

## Publication

[PR86](https://github.com/devdasx/oath-wallet/pull/86) merged as `e2b2596bbdd8d1879d0dbbff59bf23d1802bc9aa`.
Its complete tree matches the tested repair tree `e66c1cd623f74c12d99591460ecd2de1ef430378`.
Hosted replay is pending; local results are not presented as a GitHub test pass.
