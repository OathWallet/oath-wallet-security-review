# Stellar provider and contract authorization — build 104 checkpoint 23

The whole-wallet audit remains incomplete. This checkpoint examines public
5.0.2 (104) source at `c2ff488a7c7a647b2e6ab03aa1768f5735928e7e`.
No new confirmed defect or application implementation change is claimed.

## Source scope

`StellarSendClient.swift`, `WalletConnectStellar.swift` and
`OathWalletConnectStellarViews.swift` were read in full. Inspection traces
provider-state validation, reserve/fee arithmetic, classic and contract quote
construction, simulation authorization, signature/request binding, broadcast
acknowledgement versus confirmation, expiry/reconciliation and displayed
transaction details. The three files remain **partially reviewed**: these
bounded host tests do not validate the complete app authorization/UI lifecycle
or all transaction variants. One previously outstanding UI file gains a partial
disposition; the two existing partial dispositions gain this additional evidence.

[Exact source hashes and read ranges](../evidence/5.0.2-build104/stellar-provider/source-binding.json).
The plan/XDR validation helpers and existing test transports were also inspected
for this exercise. Their earlier dispositions are not promoted by these tests.

## Production execution

The fixture imports the production OathAnkr module and supplies synthetic
Horizon/RPC responses through its transport interface. Tests run in individual
host processes with network denied; no real account or provider is contacted.

- A valid native quote signs and verifies before 20 malformed-state cases test
  network/ledger identity, ledger age, reserve/fee bounds, sequence limits,
  sponsorship counters and absent account balance/signing authority.
- Ordinary and maximum contract sends use exact atomic amounts, decoded
  balances/decimals, resource fees and source-account authorization. The pinned
  Soneso SDK constructs authorization from the actual transaction received by
  the test transport and decodes the signed envelope. This is cross-implementation
  agreement, not an independent review of that SDK.
- Twelve malformed transfer simulations must reach the injected response and
  then fail: changed authorization, required restore, untrusted error text,
  old/future ledgers, missing/trailing resource data, understated/excessive fees,
  missing/extra authorization and extra results. They cannot produce a quote
  for signing or send a broadcast request. Error-string assertions check the
  thrown error only; they do not establish exhaustive diagnostic-log redaction.
- A contract multisignature send signs with the two approved keys, rejects the
  bootstrap/foreign keys, and makes no broadcast after on-chain policy changes.
- Eight existing WalletConnect methods cover network/byte binding, V0 total
  fees, malformed envelopes, existing signatures, review/transaction expiry,
  exact-byte retries, receipt/hash/absence handling and uncertain sequence errors.

[Fixture](../fixtures/stellar-provider/StellarProviderReviewTests.swift) ·
[Results and hashes](../evidence/5.0.2-build104/stellar-provider/manifest.json).

The first attempted fixture did not compile because it used an invalid Swift
initializer reference; no app test ran in that attempt. Its build log and exact
fixture are retained separately. The corrected run and final controls are
separate evidence, not a claimed app repair.

All **12 selected methods passed** in the final fresh build (four new and eight
existing). The subsequent disposable mutation produced **one expected assertion
failure** for the altered authorization.

## Negative control

A disposable copy relaxes exact authorization equality to a count-only check.
It is rebuilt before testing; accepting the changed authorization must fail the
regression method. The original tracked source is restored afterward. The
mutation and passing run retain different executable hashes. This deliberately
weakened copy is never published as application code.

## Reproduce

Use Xcode 27.1, Python and fresh directories:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/oath-provider-source
git -C /tmp/oath-provider-source checkout --detach c2ff488a7c7a647b2e6ab03aa1768f5735928e7e
python3 scripts/stellar-provider-review.py /tmp/oath-provider-source /tmp/oath-provider-replay /tmp/oath-provider-results
python3 scripts/stellar-provider-mutation.py /tmp/oath-provider-replay /tmp/oath-provider-results /tmp/oath-provider-mutation
python3 -m unittest discover -s tests -p test_stellar_provider_review.py
```

Dependencies may download during compilation. Test execution denies network.
The workflow pins source, SDK, actions, Python and Xcode, uses read-only repository
permissions, and contains no deployment, secrets or outside-PR execution.
A newly dispatched GitHub replay is distinct from completed local results.

## Earlier GitHub evidence

The [decoding replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41742064900)
reproduces seven passes and the deliberate checksum mutation's 64 assertion
failures. [Downloaded receipt](../evidence/5.0.2-build104/hosted-stellar-decoding/verification.json).

The [multisignature replay](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41743870642)
reproduces ten passes and the deliberate threshold mutation's 627 assertion
failures. [Downloaded receipt](../evidence/5.0.2-build104/hosted-stellar-multisig/verification.json).
Both artifact digests, report/log hashes, pinned fixture/driver hashes and
separate mutation executables were checked. Historical reports stay intact.

All **417 audit helper tests pass**, including seven checks of this checkpoint's
retained execution evidence, source binding, negative control and boundaries.

## Limits and remaining work

These checks do not prove correctness against an entirely dishonest provider,
complete protocol execution, all SDK operation variants, all malicious response
combinations or end-to-end stale-authorization/cancellation races. Runtime secret
lifetimes, additional derivation/recovery paths, dependency internals and binary
provenance remain in the full review backlog. UI source reading is not a visual
or interaction test.

The completion gate still reports 16,917 outstanding review/validation items,
not vulnerabilities. Compiler inputs: 227 reviewed, 176 partially reviewed,
1,475 outstanding, 460 generated/verified and 20 generated needing trace.

No new generic iOS build is claimed for this audit-only checkpoint. Checkpoint
19 records the unsigned Release build of the unchanged application tree.
No simulator, physical device, live RPC, funded transaction, real wallet secret
or App Store Connect operation was used. This is a maintainer-commissioned,
Codex-led review, not independent certification or a zero-vulnerability claim.
