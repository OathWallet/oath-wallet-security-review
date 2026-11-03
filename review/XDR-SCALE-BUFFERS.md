# XDR and SCALE buffer review — build 104 checkpoint 18

This is a partial source review and bounded parser regression exercise for
5.0.2 (104), not a complete Stellar or Polkadot protocol audit.

Before: `018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0`.
Repair: `2f914715224db31e91f1ce1f0dea4c236c043920`.
The public prerelease remains 5.0.2 (104); no App Store upload or submission.

## Confirmed result

[OW-2026-071](../findings/OW-2026-071.md) records six isolated process crashes
when readers receive Foundation Data slices. The three ordinary-buffer
controls pass before the repair. The same nine methods all pass after it.
Stellar's public plan API accepts the sliced resource data; SCALE is an
internal parser exercised through the test module. Normal provider base64/hex
decoding does not demonstrate the failing input shape. This is a robustness
finding, not a remotely demonstrated signing or funds-loss exploit.

The fixture uses fixed synthetic keys and constructs XDR resources, collection
values and a minimal v14 metadata container. The latter has no pallets/calls and
must continue to reject transfer lookup. Four slice origins, compact-width
boundaries, truncated prefixes, matching transaction bytes and signatures
verified by production code are checked. Round-trip compact tests alone do not
establish independent SCALE conformance. The tests execute the real package,
with network access denied and no live opt-in environment variables inherited.

## Adjacent validation

Forty existing Stellar/Polkadot send, multisignature and WalletConnect methods
pass without runtime networking. Seven opt-in live methods are excluded. The
selection is checked for missing, duplicate, skipped and failed results.
Diagnostics execute 121 methods: 119 pass, two skip. The 388 audit-helper tests
pass. These results do not replace the remaining protocol and application
review.

## Source reviewed

The complete baseline files below were read; their hashes remain tied to the
immutable build-104 inventory and receive **partial** dispositions:

- `StellarSendXDR.swift`: local operation encoding, account/asset/memo encoding,
  bounded signed amounts, Soroban resource fee parsing, recursive XDR values
  and ledger keys, envelope generation, network-bound digest and signature
  checks. The replacement reader initializer was also inspected.
- `StellarSendPlan.swift`: amount/reserve/fee limits, account and asset identity,
  ledger/time bounds, native/classic/contract branch rules, exact source
  authorization comparison and persisted plan fields. The sliced resource
  reproduction uses this public validation path.
- `PolkadotScale.swift`: compact width/canonical checks, text/count limits,
  metadata v14 type/pallet parsing, metadata fingerprint, call lookup, storage
  fallback, bounded recursive value decoding, signed primitives and bitsets.
  The replacement reader initializer was also inspected.
- `WalletConnectStellar.swift`: request field allowlist, canonical base64,
  network/account binding, SDK XDR decode/re-encode comparison, v0/v1/fee-bump
  digest selection, signature preservation, time bounds and exact signed-byte
  verification. This source reading is not a review of every upstream SDK
  implementation it invokes.

Source ranges and before/after hashes are in
[`source-binding.json`](../evidence/5.0.2-build104/xdr-scale-buffers/source-binding.json).
No file becomes fully reviewed merely because its tests pass.

## Reproduction

From a clean audit checkout on the pinned macOS/Xcode toolchain:

```sh
python3 scripts/xdr-scale-buffers.py /path/to/wallet /tmp/xdr-before /tmp/xdr-before-results --baseline --expected-commit 018cd8316d5f2c899f5ccbd3bc8547b3f7a7bea0
# Check out the repair commit in the clean application source.
python3 scripts/xdr-scale-buffers.py /path/to/wallet /tmp/xdr-after /tmp/xdr-after-results --expected-commit 2f914715224db31e91f1ce1f0dea4c236c043920
python3 scripts/xdr-scale-regressions.py /path/to/wallet /tmp/xdr-regression-build /tmp/xdr-regression-results --expected-commit 2f914715224db31e91f1ce1f0dea4c236c043920
```

The dedicated workflow pins source/action/tool versions, runs with read-only
repository permissions and no deployment credentials, and does not execute
outside pull-request code. Local and hosted evidence are reported separately.

The generic unsigned iOS Release build passed and reports 5.0.2 (104).
Public-release validation, diagnostic coverage and the application secret scan
passed. The complete public merge tree matches the tested repair tree.

The upstream `XDRDecoder.swift` and `XDRCodableExtensions.swift` were also
re-read and byte-matched to their existing partial dispositions. They normalize
Data through a byte array, bound allocation counts and track decoding depth.
Oath's full re-encode comparison rejects noncanonical SDK interpretations on
the reviewed WalletConnect path. The earlier [bounded dependency review](STELLAR-XDR-BOUNDARIES.md)
retains its original source/test pins; this re-read does not retest those old
fixtures or close all SDK coverage.

## Remaining work

The complete Stellar SDK XDR implementation, independent fixture provenance,
all operation semantics, runtime metadata trust, unsupported signed extensions,
resource limits under large hostile metadata, app-level authorization and
lifecycle interleavings, and node execution remain outside the demonstrated
result. No UI, simulator, physical-device, public-network transaction or binary
source-equivalence claim is made. The full review remains incomplete.
