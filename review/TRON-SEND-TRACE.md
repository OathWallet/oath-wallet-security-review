# TRON send, signature and recovery review

Source target: `27fcf5f58f6169e1a40fb6afced883bc736d124d`, whose tree matches
public merge `99742291d6124fd2628bbf1653ec0ba5f121456f`. This increment did not
change application code or establish a new production vulnerability.

## Traced boundaries

1. `TronSendClient.quote/prepare` binds provider accounts to requested addresses,
   checks the endpoint's genesis identifier, validates relevant governance values,
   and bounds prices, energy, timestamp and block number. TRC20 simulation must
   contain the expected transfer event. Only the pinned legacy token gets the
   documented zero-return exception. These are checks on provider responses,
   **not independent verification of blockchain consensus**.
2. The immutable `TronSendPlan` validates canonical integer amounts, available
   balances, expiry, reference height, native-token decimals and exclusive
   permission/multisig modes. `fee` is a resource-based reservation; `feeLimit`
   is the value encoded into a smart-contract transaction. They need not equal:
   available staked resources can legitimately yield a zero reservation. A future
   resource change can change actual fees. The UI fee/total access sites use the
   reservation; this review does not promise an exact on-chain fee.
3. `OathTronSendService` reserves a database draft and plan before signing. The
   vault's `signTronSend` rechecks its authentication generation after awaits and
   compares wallet, account, asset, queued state and the complete persisted plan.
   The signing adapter additionally checks account ownership, network, imported
   key/derivation mode and multisig policy. Production cryptography checks the
   signer addresses against the plan before constructing the signed envelope.
4. `queueTronSend` validates the account, asset, recipient and amount in one SQL
   write and reserves the sender across duplicate imports. `journalTronSignature`
   verifies the signed bytes against the saved plan before saving them. Recovery
   uses that signed payload and plan; it does not derive or sign a replacement.
5. Broadcast acknowledgement remains separate from confirmation. Timeouts do not
   release the reservation. Recovery verifies exact bytes/signatures; expiry
   requires a continuous, provider-reported solid block range. Permission and
   multisig configuration changes are rechecked before retries. Late submission
   acknowledgements cannot replace a terminal journal state.

## Adversarial production-code tests

`scripts/tron-properties.py` builds an isolated host test target against the
actual pinned `OathAnkr` package and pinned remote dependencies. No production
implementation is copied into the test. The deterministic seed is
`0x4f41544854524f4e`. Six test cases passed:

- 1,006 decimal-to-uint256 vectors computed with independent Python integers,
  plus ten malformed/out-of-range inputs.
- Three existing `tronweb@6.2.2` fixtures compare raw encoding, digest, signature
  and full signed bytes for TRX, TRC10 and TRC20. Their generator and fixture were
  read; the upstream JavaScript generator was not rerun in this increment.
- 21 changes to consensus fields first pass production plan validation, then
  fail verification of the original signature. This distinguishes signature
  binding from rejection solely by malformed-plan guards.
- 701 single-bit changes spanning every signed-envelope byte and 195 changes
  spanning every signature byte are rejected. Mutated signatures are re-encoded
  into matching envelope bytes so signer recovery is exercised. Twelve invalid
  signature lengths, altered hashes and duplicate-signature envelopes are also
  rejected.
- Fifteen malformed-plan variants fail validation and signing. Age boundaries
  accept -5, 0 and 90 seconds and reject signing at -6, 91 and 180 seconds.
- A funded-by-resources control preserves the signed execution limit while
  changing only reservation metadata. It does not assert future fees are zero.

The existing TRON authorization host harness passed nine checks: wrong passcode,
missing biometrics, no signature on failed authorization, exact intent, cross-
wallet rejection, biometric intent equivalence, paused authentication, lock
invalidation and locked signing. It uses production vault/PIN/imported-key
signing code with a synthetic biometric store and substituted HD derivation.
It does not execute the complete app service, real Face ID or an iOS UI.

## Broader host regressions and evidence

On this exact application commit, OathAnkr selected 1,402 XCTest cases:
1,208 passed, 194 skipped, zero failed. OathDatabase selected 774:
703 passed, 71 skipped, zero failed. The separate empty Swift Testing runs add
no coverage. Skips include live/fixture opt-ins and separate diagnostics modes
that this runner does not enable. Isolation alone does not enable those modes;
their coverage remains outstanding in this run. Among these, TRON-named/WalletConnect-TRON package cases account
for 44 passes and ten skips; TRON database cases account for 21 passes and two
skips. These subsets are included in the package totals, not additional tests.
The 79.561-second TRON node-recovery/cache test completed successfully within
the existing 120-second isolated-case timeout; no timeout was relaxed.

All 84 audit helper tests passed. The new GitHub job is configured with the
existing pinned actions, read-only permissions, isolated host and no secrets.
Local success is not a GitHub run result. Actionlint reports only its unknown
`xcode-27` runner label; rerunning with that exact warning filtered passes.
The unfiltered warning is retained. GitHub's prior successful TRON job reports
runner group `GitHub Actions` with that label, and the repository lists no
self-hosted runners. This does not establish current runner availability. Raw per-case logs, result manifests,
fixture hashes, dependency pins, seed, durations and compressed logs are in
[the evidence bundle](../evidence/tron-send-trace). Original and normalized
published hashes are recorded separately. No new generic iOS build was needed:
application source remains the already-built 27fcf5f target.

## Read dispositions and limitations

The complete plan, crypto, identity/model, multisig policy and permission-control
files were read for bounds, encoding, signature membership, threshold retention
and integer overflow. Their downstream CryptoKit/secp256k1 implementations and
network protocol provenance remain separate dependency review boundaries.

The complete receipt decoder, client, app service, signing adapter and SQL journal were also read,
but retain partial dispositions: malicious-provider behavior, WalletConnect
request decoding and approval context, receipt/history consumers, HD key derivation, app-service lifecycle
integration and database migration/index assumptions need further evidence.
Only the TRON method of `OathWalletVault` and `SendReconciliation`, the TRON
removal type in `Permissions`, and fee/total access sites in `OathSendReviewPage`
were read here; other methods in those files do not inherit coverage.

No live provider, funded account, broadcast, simulator or physical device was
used. Package downloads are not live-chain tests. Passing these finite corpora
does not establish absence of all malformed inputs, races or chain-specific
defects. The whole-wallet review and final-target GitHub matrix remain open.
