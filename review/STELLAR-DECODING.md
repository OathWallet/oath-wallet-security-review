# Stellar decoding — build 104 checkpoint 21

The whole-wallet audit remains incomplete. This checkpoint examines the public
5.0.2 (104) prerelease at `c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`.
No new confirmed defect or application implementation change is claimed.

## Source review

`StellarModels.swift` and `StellarDecoding.swift` were read in full. The bounded
review traces public account/contract address decoding, CRC and version checks,
network-bound Stellar Asset Contract identities, decimal/atomic conversion,
i128 event amounts, CAP-67 memo maps, event ownership, failed transactions,
fee refunds, and classic/indexed holdings. These two previously outstanding
files receive **partial** dispositions, not a complete security verdict.

[Exact source hashes and read ranges](../evidence/5.0.2-build104/stellar-decoding/source-binding.json).

A suspected fee-event state mismatch was investigated but not confirmed.
The pinned upstream Stellar RPC implementation sets `InSuccessfulContractCall`
from `tx.Successful()` for transaction-level and operation-level events and
retains failed transactions because they can pay fees. This narrows the
hypothesis; it does not establish the behavior of every deployed provider.
[Upstream lines 130–176](https://github.com/stellar/stellar-rpc/blob/aafa556b47cb9af9ee0d02bd62c4e56e774c4f44/cmd/stellar-rpc/internal/rpcv1/sqlitedb/event.go#L130).
The inspected upstream file's hash and read range are recorded separately;
the RPC repository has not been fully reviewed or run.

## Independent vectors and host tests

Seven new methods call the production Oath parser. All seven passed in a fresh
source checkout and fresh native SwiftPM build. Runtime network access is
denied for each host test; dependency downloads during compilation are allowed.

The deterministic corpus uses seed `oath-stellar-decoding-v1` and Python's
standard-library base32, CRC-HQX, SHA-256, byte packing and arbitrary-precision
integer operations. It does not call the app to generate expected results.

- 64 synthetic public-byte/address cases, account/contract/muxed XDR forms,
  invalid checksums, wrong address types and lowercase rejection.
- 128 asset-contract cases across mainnet and test-network passphrases, with
  different issuers, mixed-case alphanumeric asset codes and invalid codes.
- 128 exact decimal/i128 cases spanning zero, integer boundaries, deterministic
  values and scales 0, 1, 6, 7, 18, 38 and 255. Negative fee amounts are checked
  separately from unsigned token movements.
- 72 CAP-67 amount maps using integer, bytes and string memo representations.
- 1,776 truncated inputs plus trailing data, oversized/malformed base64 and
  256 deterministic invalid-discriminant inputs exercised by three parsers.
- 12 success/failure/fee-refund event cases, wrong owners and fee contracts;
  indexed holding amount/owner/network checks and duplicate native balances.

Address encodings are also compared with the pinned Soneso SDK 3.12.0 source
at `b5dac0a6e8ff312d597c9a3b4269b03131d66e0d`. This is an additional comparison,
not an independent SDK audit. Expected asset-contract and amount results come
from the separate Python generator; agreement is bounded evidence, not a proof
that either implementation covers the entire protocol.

[Fixture](../fixtures/stellar-decoding/StellarDecodingReviewTests.swift) ·
[Generator](../scripts/stellar-decoding-vectors.py) ·
[Results and hashes](../evidence/5.0.2-build104/stellar-decoding/manifest.json).

## Negative control and reproducibility

A disposable test-copy mutation removes only the account checksum predicate.
The same address test then produces 64 expected checksum assertion failures.
The source is restored afterward. The production app is unchanged. The mutated
copy is rebuilt in its own existing checkout; its executable hash and original
and mutated source hashes are retained separately from the passing run.

From a clean review checkout, with Xcode 27.1 and Python available:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-stellar-source
git -C /tmp/oath-stellar-source checkout --detach c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
python3 scripts/stellar-decoding-review.py /tmp/oath-stellar-source /tmp/oath-stellar-replay /tmp/oath-stellar-results
python3 scripts/stellar-decoding-mutation.py /tmp/oath-stellar-replay /tmp/oath-stellar-results /tmp/oath-stellar-mutation
python3 -m unittest discover -s tests -p test_stellar_decoding_review.py
```

Use fresh output paths. The pinned workflow has read-only repository access,
no deployment credentials, and no pull-request execution on the dedicated
runner. Hosted replay status is reported separately from local results.
Two harness-development mistakes are preserved: an initial driver syntax
error prevented execution, and the first negative-control log counter omitted
"an" from XCTest's assertion text. The actual first mutation run already had
64 failures; the corrected counter was rerun and recorded separately. Neither
harness mistake is counted as an application defect or a successful test.

## Evidence verification

All 404 audit helper tests pass, including five checks for this checkpoint.
The changed publication files and expanded new archives passed the redacted
secret scan. The completion gate still reports 16,917 outstanding review and
validation items; these are scope items, not a count of vulnerabilities.
The compiled-input ledger now records 227 reviewed, 172 partially reviewed,
1,479 outstanding, 460 generated/verified and 20 generated inputs needing trace.

## Remaining scope

This is not independent certification. Bounded adversarial vectors do not
establish exhaustive fuzz coverage. Remaining work includes signed-payload
signer-policy combinations, protocol-version/provider differences, all CAP-67
combinations and canonical padding behavior, real adapter integration,
reachable SDK internals, and binary provenance. The source dispositions stay
partial. Existing broader audit gaps remain open.

No new generic iOS build is claimed for this audit-only checkpoint. Checkpoint
19 records the unsigned Release build of the identical application tree.
No simulator, physical device, live RPC, real secret, funded transaction, or
App Store Connect operation was used.
