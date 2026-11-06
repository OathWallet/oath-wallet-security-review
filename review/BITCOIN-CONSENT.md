# Bitcoin signing and consent — checkpoint 33

This maintainer-commissioned, Codex-led review targets public application commit
`32701474fefbed3840878e35f6111e8d494e1f02`, version 5.0.3 (105). No new production
vulnerability was confirmed. The application was not modified. This scoped
review does not establish completion of the whole-wallet audit.

## Attack paths examined

A malicious dApp can supply a PSBT, selected signing inputs and signature-mode
preferences. The investigation asks whether it can obtain a signature allowing
outputs to change, select another account's key, misrepresent input values or
change the recipient, fee or debit after review. A separate persistence-boundary
test changes decoded plan fields; it does not demonstrate remote database writes.

Production code verifies complete parent transactions, compares supplied witness
amounts and scripts, matches selected inputs to known wallet addresses and
restricts signature modes to ALL, plus DEFAULT for Taproot. The signer derives
the selected account and leaf again and checks their address/script identity.
The plan is rebuilt before signing, including its outputs, fee and wallet debit.
Verification checks the unsigned transaction and preserves global, output and
unselected-input maps. Existing peer-signature regression cases are also rerun.

The application adapter, vault, journal and request service were traced for
wallet/account ownership, generation invalidation, request expiry and session
authorization. These source traces are not full application runtime tests.

## Reproduce

Use a clean checkout of the pinned application, macOS with a compatible Xcode
toolchain and Python 3.14.7. From this review repository, with fresh directories:

```sh
python3 scripts/bitcoin-consent-review.py ../wallet ../bitcoin-build ../bitcoin-results
python3 -m unittest discover -s tests -p test_bitcoin_consent_review.py
```

The driver archives production packages, injects the synthetic test fixture and
builds actual production implementations. It does not copy the signer into a
test-only implementation. Dependency versions are locked. Compilation may
download dependencies; each isolated test process has networking denied.
No node, real credentials, funded account or broadcast is used.

## Actual local results

The successful run used Xcode 27.2 (27B52), Swift 6.4.2 and Python 3.14.7 and
took **74.121 seconds**, including two fresh builds.

- **27 production methods passed, zero skipped, zero failed:** six new methods,
  twelve existing Bitcoin Connect methods and nine signature-proof methods.
- Across four address types, **1,040 signature-mode combinations** accept five
  permitted cases and reject 1,035 unsupported cases. Accepted cases are signed
  and verified through production code.
- Eight mixed-input cases sign only the selected owned input while preserving
  foreign inputs and proprietary fields. Selecting the foreign input is rejected.
- A bit change at every byte position in each fixture's unsigned transaction is
  rejected after signing. This is a bounded corpus, not exhaustive fuzz coverage.
- Altered parent values, mismatched parent transactions, unowned change, wrong
  key sources and altered derivation metadata are rejected.
- Six altered consent projections are rejected. In a separate deliberately
  weakened build, removing the rebuilt-plan equality check causes exactly four
  assertions in one method to fail. Independent transfer checks still reject the
  other two altered fields. This mutation is an audit control, not an app finding.

The original attempt passed all 27 production methods and produced those same
four mutation assertions, but the audit driver incorrectly expected six. Its
terminal harness failure and logs remain in `attempt1.zip`. Only the expected
failure signature was corrected; the fixture stayed byte-identical. The second
fresh run passed the corrected evidence checks. Crashes, unrelated failures and
skips are not accepted as successful mutation detection.

[Manifest](../evidence/5.0.3-build105/bitcoin-consent/manifest.json) ·
[Successful run](../evidence/5.0.3-build105/bitcoin-consent/runs.zip) ·
[Original attempt](../evidence/5.0.3-build105/bitcoin-consent/attempt1.zip) ·
[Exact source snapshots](../evidence/5.0.3-build105/bitcoin-consent/validation.zip) ·
[File/range coverage](../evidence/5.0.3-build105/bitcoin-consent/source-binding.json).

## Remaining gaps

Eleven source dispositions are partial and hash-bound. They do not change the
frozen inventory or extend earlier tests to untested files or commits. Upstream
BDK/miniscript/secp256k1 implementation and binary provenance, exhaustive PSBT
semantics, provider truth, full application cancellation/authorization
interleavings, crash recovery, rendered/localized consent and runtime secret
lifetime remain separate work. Bitcoin Core validation from earlier checkpoints
was not rerun here and is not a result of this run.

The hosted workflow is audit-only, read-only and source/action-pinned. A configured
workflow is not a hosted result; its receipt will be appended after verification.
No new generic iOS build was run for these audit-only changes. No simulator,
physical device or App Store operation was performed.

## Verified hosted replay

[GitHub run 42233934547](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42233934547) completed successfully at audit commit `c94ecc75ddc877a3efc5e19c096be02aae71a7e7`. It replayed the same pinned app source with Xcode 27.1 in 314.876 seconds: 27 production methods passed, zero skipped; the deliberate weakened control produced its one expected failed method with four assertions.

The downloaded artifact matches GitHub's SHA-256 digest. Every result, source manifest, dependency lock and case-log hash was independently checked, including the exact mutation failure signature. [Receipt and durable archive](../evidence/5.0.3-build105/hosted-bitcoin-consent/verification.json). These host results do not establish the unresolved runtime or dependency properties above.
