# EVM Safe contract cross-check — partial review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Application candidate: `2e51f0bcd3e710c35a1d78ee93746f6a8f202fdc`.
External contract reference: Safe 1.4.1, commit
`bf943f80fec5ac647159d26161446ac5d716a294` in
[safe-global/safe-smart-account](https://github.com/safe-global/safe-smart-account/tree/bf943f80fec5ac647159d26161446ac5d716a294).
This is a source comparison, not proof of deployed bytecode provenance.

## App paths inspected

`EVMMultisigClient.swift` was read completely, alongside
`EVMMultisigPolicy.swift`, `EVMMultisigTests.swift` and
`EVMMultisigInclusionTests.swift`. Policy construction bounds/distinctly sorts
owners and excludes the separate executor. The client compares factory and
singleton code hashes, proxy runtime, master-copy storage, owners, threshold,
modules, guard and fallback before trusting a configured policy. Provider
answers remain a trust boundary: separate `latest` reads are not a single
block-anchored state snapshot. No exploitation of that observation was shown.

Signing validates the plan, binds the chain and Safe address in the domain,
binds recipient/value/calldata/nonce in the transaction digest, sorts owner
signatures and requires membership. Verification reconstructs the exact outer
executor transaction. Only EOA signatures with recovery parity 27 or 28 are
accepted; contract signatures and pre-approved-hash forms are not admitted by
the app verifier. The outer transaction has zero value; the Safe's own balance
pays the inner transfer, and the executor pays the outer network fee.

The receipt path requires outer inclusion and separate inner execution evidence,
checks the canonical block hash again, bounds logs, and checks token transfer
logs independently. The existing inclusion test explicitly rejects an outer
receipt without a matching inner success event. That is an in-memory provider
fixture, not execution of a deployed Safe contract.

## Primary-source comparisons and rejected lead

A suspected mismatch in the indexing of `ExecutionSuccess` was rejected after
reading the exact contract source. `Safe.sol` declares the transaction hash as
indexed; `SafeL2.sol` inherits that event and adds a separate informational event.
The app's two-topic check is consistent with that ABI. No event-decoder change
was made.

The Safe transaction type/domain and field order match the app's digest layout.
The app encodes six zero words for operation, Safe gas limit, base gas, gas price,
gas token and refund receiver. In the contract, zero Safe gas and gas price
require successful inner execution; zero gas price also leaves the emitted
payment at zero. The app's receipt check for zero payment matches that path.
The contract requires increasing, registered owners, consistent with the app's
sorted signature handling. This comparison does not independently verify
secp256k1 or every contract-signature branch.

`SafeProxyFactory.sol` derives its CREATE2 salt from the initializer hash and
salt nonce and appends the singleton as a 32-byte constructor argument. Those
operations match the app's predicted-address calculation. Initialization is
performed in the creation transaction; a failing initializer reverts creation.
The app supplies the initializer rather than intentionally deploying an
uninitialized proxy. The separate chain-specific and callback factory methods
are not used by the app's deployment encoder.

## Evidence and gaps

The source hashes and exact URLs are recorded in
[`evidence/safe-contract-crosscheck.json`](../evidence/safe-contract-crosscheck.json).
SafeL2 and SafeProxyFactory were read in full; Safe.sol's setup, execution,
signature checks, domain and transaction encoding were inspected. This is not a
full review of Safe and its imported modules. No Solidity compilation, deployed
code comparison, local-EVM execution or mainnet transaction was performed in
this increment. The optional local-EVM test remains explicitly skipped in the
normal host suite. The app file dispositions remain partial where those
protocol, dependency or execution boundaries are unresolved.
