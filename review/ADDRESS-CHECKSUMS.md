# Address checksum boundary review

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

The baseline is the immutable 5.0.1 (103) source, `c7acd23bb139864a40273f405d18b479589d2b20`. The repaired candidate is `b128544044a5d3043fca99c7d4c94af1af3b511c`.

## Behavior and repair

ERC-55 specifies a checksum for a 20-byte address. Hash input is the lowercase hexadecimal address in ASCII. The original EIP55 helper accepts arbitrary byte lengths, strips internal prefixes from text and uses a lossy/permissive hex decoder. Those behaviors can change the address being checksummed. The output loop also uses zip, which can truncate if the crypto provider returns a short hash. [ERC-55 specification](https://eips.ethereum.org/EIPS/eip-55).

The repair validates exact size and ASCII hex before decoding. It accepts one optional leading prefix in either case. The Data overload requires twenty bytes and the injected hash must have thirty-two bytes. Both overloads now throw; the sole production caller in ENSResolver uses `try`. Their output prefix conventions remain unchanged. This is a source API change for external callers, with no stored-wallet or backup format change.

## Evidence and limits

The fixture runs the unchanged production module and injects 24 independently calculated hashes/checksums. Eight inputs are the published ERC-55 examples; sixteen are deterministic synthetic byte sequences. The vectors were initially generated with ethers 6.15.0. The current generator pins ethers 6.17.0 and reproduces the same fixture bytes, including the historical provenance header. It checks the exact bytes passed to hashing and tests String, Data, prefixed, uppercase and sliced forms. Invalid input must fail before the hash call. A malformed provider hash must fail rather than truncate the result. The original failure totals include the newly explicit uppercase-prefix and malformed-provider contracts as well as malformed address cases. These tests establish checksum encoding and parsing behavior. They do not validate the cryptographic implementation behind OathWCCrypto.

[Finding](../findings/OW-2026-056.md) · [Generator and pinned dependencies](../fixtures/address-checksums) · [Exact-source replay](../evidence/5.0.1-build103/address-checksums/result.json).

Source search found no application call into EIP55 or ENSResolver. The direct helper finding is not evidence of a current remote exploit through the app. ENS normalization and forward/reverse ownership validation remain review work. The MessageSigner surface also remains partial: its enum accepts signature kinds beyond its Ethereum signer, and its callers and semantics need further assessment before any finding or repair. The shared Data(hex:) helper needs a separate call-site review before changes because multiple APIs use it. No source disposition is promoted for those unresolved behaviors.

The BIP44Provider declaration was reviewed as an interface only; it contains no derivation implementation. MessageSignerFactory wires the Ethereum signer and payload formatter without acquiring keys. ENSResolverFactory configures the fixed registry and RPC host; it does not establish name ownership or provider truthfulness. SignerImports only exports a module. Their narrow dispositions do not certify the components they reference.

## Reference-tool dependency update

The initial npm check reported two advisories in the generator's unused WebSocket dependency. Both current generator locks were moved to ethers 6.17.0. The address and contract-signature fixtures reproduced byte for byte, and the new npm registry check reports zero known advisories. Historical fixtures and reports retain their initial provenance. This is an audit-tool dependency update, not an iOS application dependency update. [Before/after registry reports and lock hashes](../evidence/5.0.1-build103/address-checksums/oracle-update.json).
