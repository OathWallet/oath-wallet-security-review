# CAIP model and parser review

Reviewed application commit: `8e5b6b0f565026951d7cef9435258daa0b02b9b2`.
Baseline for the identical regression fixture: `764dd608519e8f30f60e3dea4a553c1def2f8c07`.

## Source read and disposition

Read the complete production `WalletConnectUtils/Blockchain.swift`,
`Account.swift`, and `Extensions/String+CAIPs.swift`: initializer composition,
field counts, character/length restrictions, string preservation, Codable,
derived chain construction, equality/hash synthesis and failure behavior.
These three files now have reviewed dispositions tied to their exact hashes.
This means their implementation was examined; it is not exhaustive proof for
every Unicode value, resource limit, chain-specific address rule or caller.

Read all existing upstream `BlockchainTests` (four) and `AccountTests` (seven),
and added them to the host harness. Reviewed the new seven-case fixture and
the changed harness, including its module-import adaptation. Tests execute the
production parsers; the independent oracle uses ASCII-byte sets and length
checks, not copied production regular expressions.

## Confirmed defect and rejected hypothesis

[OW-2026-019](../findings/OW-2026-019.md) is a separate-field constructor
contract defect. It concatenated an invalid chain and an address before
validation, permitting the address to supply a missing chain reference.
Validating `Blockchain(chainIdentifier)` first fixes that boundary.

The suspected trailing-line-ending regex bypass did **not** reproduce on the
tested Apple Foundation implementation. LF, CR, CRLF, NEL, line separator and
paragraph separator are rejected in every chain/account component, including
JSON decoding. The original small probe and the larger production-model test
are preserved. No regex change was made to repair a non-reproducing hypothesis.

## Contract and compatibility

[CAIP-2](https://standards.chainagnostic.org/CAIPs/caip-2) describes a namespace
and reference with restricted characters and bounded lengths.
[CAIP-10](https://standards.chainagnostic.org/CAIPs/caip-10) adds an account
component and leaves address semantics to the chain. The SDK's existing `_`
and `=` address extension for TON is retained and tested; the report does not
claim this extension is part of the base CAIP-10 grammar.

The fix does not trim, normalize case, alter valid identities, or change storage.
Legacy whole-string account values still decode through the same parser.
The two formerly accepted malformed argument pairs produce valid whole strings;
those whole strings remain supported. Only the invalid separate-field invocation
is rejected. No migration is needed for this change.

Oath's inspected approval construction at
`OathAtmosphere/Scanner/OathWalletConnectService.swift:321–337` uses
`Account(blockchain:address:)` after selecting typed chains. The production
source search found no call to the affected string-chain overload in Oath or
the vendored SDK. Thus no remote app exploit, signing bypass or fund loss is
established. The new case repairs the SDK API's documented input contract.

## Evidence and reproducibility

Same seven cases, separate network-denied host processes before/after:
two assertions fail in one case before; six controls pass. All seven pass after.
The final classifier validates exact case names, assertion count/message, exit
status and terminal outcomes; it rejects skipped/missing cases and arbitrary
crashes or build errors. The 14 recorded executions take 53.706 seconds locally.

The corpus includes all 128 ASCII bytes plus seven non-ASCII strings inserted
at three positions in each of the two/three fields (2,025 comparisons), and
4,096 generated tuples at seed `0xCA1F2026` (12,288 constructor comparisons).
Additional cases test six line endings, Codable, minimum/maximum lengths,
typed and separate-field constructors, invalid delimiters, case sensitivity,
and unchanged TON support. This is bounded testing, not exhaustive fuzzing.

Fixture SHA-256: `7eb2b68e53c89534b859e39c9765c7d532114017b4d5b2d0a5085e9e24a50caf`.
See [durable evidence](../evidence/caip-boundary/manifest.json).

```sh
python3 scripts/checkout.py
python3 scripts/caip-boundary.py .work/source --output .work/caip-boundary --scratch .work/caip-build
python3 scripts/run.py .work/source walletconnect-sdk
```

Broader session lifecycle, caller-specific input/resource limits, chain-specific
address validation, and remaining dependencies stay in the coverage ledger.
No simulator, phone, live relay, transaction or App Store operation was used.
