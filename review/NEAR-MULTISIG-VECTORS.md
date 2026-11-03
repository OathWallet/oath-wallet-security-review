# Independent NEAR multisig signing vectors

Application: `5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`, the public repair tree
merged in PR82. No production code changed in this checkpoint.

## Matrix and results

The locked `near-api-js` 7.3.1 SDK independently creates **50 bundles containing
188 transaction parts**. Five quorum configurations (1/2, 2/3, 3/5, 7/10 and
10/10) each cover deployment, bootstrap-key removal, native transfer, token
transfer and token transfer with storage registration, at low and high values.
Member keys are sorted by public bytes; private signing inputs are deliberately
reversed to test signer-to-part matching.

Nonces include 1 and UInt64.max minus one; the proposal creator's confirmation
uses its next nonce, including UInt64.max. Request IDs include 0 and
UInt32.max minus one. Native/token amounts include 1 and UInt128.max minus one.
These are serialization boundaries, **not** claims that those balances or nonce
values are currently admissible on a live chain. The generator hashes the exact
pinned bundled contract before creating deployment actions.

Three host methods pass with runtime networking denied:

1. Complete transaction bytes, transaction hashes and signer identities match
   the independent SDK for every part. Production verification accepts each
   SDK-signed bundle. Node crypto independently verifies all **188 application
   signatures** over those exact expected bytes.
2. Encoding and decoding every plan and signed bundle preserves every field and
   verifies afterward. This checks Codable persistence compatibility, not actual
   journal interruption or filesystem recovery.
3. Every altered signature is rejected, along with removed, appended and
   reordered parts. The independent Node verifier separately rejects five
   missing, reordered, byte-altered and signature-altered output controls.

The original fixture required identical SDK and CryptoKit signature bytes.
It produced 376 failed assertions in one method; the other two methods passed.
Direct independent verification nevertheless accepted all 188 application
signatures over the expected transaction bytes. The fixture was corrected to
check the signature's validity and binding, rather than requiring byte identity
with another implementation's signature. The original fixture, outputs, logs
and successful independent verification are retained. This was an audit-test
assumption, not a confirmed app defect.

A deliberately broken production copy removed the proposal creator's next-nonce
increment. The same final fixture reports **90 failed assertions in one method**,
with the other two passing. This establishes sensitivity to that mutation;
it does not prove sensitivity to every possible signing bug. The mutation was
committed only in an isolated temporary checkout and was never applied to the
public application. Its exact patch and source commit are in the evidence.

[Durable evidence manifest](../evidence/5.0.2-build104/near-multisig-vectors/manifest.json).
The compressed archive includes all attempts, generated vectors, signed outputs,
tool versions, fixture snapshots and internal file checksums. All seeds are
explicit public synthetic values; the accounts must never be funded.

## Reproduce

Use the workflow's pinned macOS/Xcode, Python and Node tools. Dependency
installation needs network access; generation, test execution and verification
run with networking denied.

```sh
git clone https://github.com/devdasx/oath-wallet.git wallet
git -C wallet checkout --detach 5d91d1e4dfd36c56031c7a8fb1ee305446dc54de
python3 scripts/near-multisig-signing.py wallet scratch evidence/multisig
python3 scripts/near_multisig_signing_evidence.py evidence/multisig
sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  python3 scripts/near_multisig_verifier_controls.py evidence/multisig
```

For the sensitivity check, create a separate checkout at that same commit,
apply `evidence/5.0.2-build104/near-multisig-vectors/nonce-mutant.patch`, and commit
it locally. Run the driver with `--commit` set to that synthetic commit. Expect
one failed method with the remaining two passing. Do not apply or publish that
intentional defect to the application.

## Hosted reader repair replay

[Run 41607922685](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41607922685)
completed successfully. Its original reader fixture records four passing methods
and the expected SIGTRAP; the repair records five passes and 82 independently
verified production signatures. All 26 adjacent package methods pass without
skips. The downloaded artifact digest, executed driver and fixture hashes,
method identities and case-log hashes were checked. Independent signature
verification was also rerun against the downloaded outputs.
[Downloaded evidence](../evidence/5.0.2-build104/hosted-near-signing/manifest.json).
This hosted result covers the earlier reader checkpoint, not the new multisig
vector workflow; those runs are tracked separately.

## Remaining work

These vectors extend signing/serialization evidence, not the full contract or
provider state machine. Upstream contract tests and source-to-WASM rebuilding
remain unresolved as described in [the prior provenance review](NEAR-MULTISIG-BOUNDARIES.md).
Staged submission/restart, cancellation interleavings, membership-change
semantics, upstream dependencies and runtime fee acceptance still need review.
No source dispositions were promoted to complete on the strength of these tests.
No new iOS build, simulator, physical-device, live-chain or App Store operation
occurred. The earlier generic iOS build keeps its own exact source pin.
