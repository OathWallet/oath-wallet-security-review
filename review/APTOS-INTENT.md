# Aptos signed-intent review — checkpoint 31

This maintainer-commissioned, Codex-led review covers public source
`32701474fefbed3840878e35f6111e8d494e1f02`, Oath Wallet 5.0.3 (105).
It is not independent certification or a completed whole-wallet audit.

## Attack paths examined

The review traces whether a changed recipient, amount, gas budget, sequence,
expiry, network, token reference, signer set or signed byte can survive the
production signing verifier. It also checks whether a provider can substitute
those fields in simulation responses or cause invalid signed bytes to reach
the submission transport.

The production implementation reconstructs the transaction from the approved
plan, verifies its exact bytes and signatures, and binds the owner to the key
or MultiKey policy. Simulation responses must match the intended payload.
The application adapter separately binds the account to its wallet and chain;
the vault rechecks authentication and removal generations across awaits.
The service journals signed bytes before submission. These application paths
were source-traced, not executed by the package-only fixture.

No new production vulnerability was confirmed by this matrix. No app repair
or app source change is claimed.

## Reproduction and actual results

With Python 3.14 and a compatible macOS/Xcode toolchain, check out the exact
public source commit above. Use fresh scratch and output directories:

```sh
python3 scripts/aptos-intent-review.py ../wallet ../aptos-build ../aptos-results
python3 -m unittest discover -s tests -p test_aptos_intent_review.py
```

The driver archives the pinned packages and builds their actual production
implementations with the locked dependencies. Runtime test processes deny all
network access. Inputs are public synthetic keys, fixtures and injected replies.

The local run took **191.868 seconds** and recorded **25 passed, 0 skipped,
0 failed**: nine new intent methods, thirteen existing send methods and three
existing multisignature methods. The new tests cover:

- A one-bit change at every signed-byte position for native APT, Coin and
  fungible-asset transfers, plus truncated, appended and empty payloads.
- Approved-field substitutions, wrong keys, signatures, hashes and networks.
- Seven multisignature index/threshold combinations spanning all bitmap bytes,
  plus reordered, duplicate, missing and invalid signer indexes.
- Thirty-two modified simulation replies across the three asset types, with
  valid controls and explicit assertions that no broadcast occurred.
- Four existing official-SDK fixtures. Their generator was not rerun here;
  this is reuse of committed vectors, not fresh independent vector generation.

A separate disposable build deliberately removes only the exact-byte binding
guard. Its selected method fails with the expected wire-substitution assertions
(**0 passed, 0 skipped, 1 failed**). This demonstrates test sensitivity, not an
application vulnerability. Build errors, crashes, unrelated assertions and
skipped cases do not qualify as that control.

The first attempt failed to compile an audit-fixture assertion closure under
Swift isolation checking. Its original fixture, build log, toolchain and input
manifest are retained. Replacing that fixture assertion with ordinary guards
allowed a completely fresh build/run. The app implementation was unchanged.

[Manifest](../evidence/5.0.3-build105/aptos-intent/manifest.json) ·
[Run logs and checksums](../evidence/5.0.3-build105/aptos-intent/runs.zip) ·
[Original failed attempt and source copies](../evidence/5.0.3-build105/aptos-intent/validation.zip) ·
[File/range coverage ledger](../evidence/5.0.3-build105/aptos-intent/source-binding.json).

## Limits and unfinished work

The eight source dispositions are partial and hash-bound. The frozen inventory
remains unchanged; no scanner or test pass promotes an unreviewed file.
Provider honesty, upstream cryptographic implementation/provenance, full
application authentication and cancellation interleavings, persistent journal
recovery, rendered consent and production-network execution remain open.

The workflow is audit-only and pins the source, actions, Python and Xcode
selection. A published workflow is not a completed hosted replay; any hosted
result will receive a separate verified receipt.

No generic iOS build was rerun for these audit-only changes, and no new app
compilation claim is made. No simulator, physical device or App Store operation
was performed. The full review remains in progress.
