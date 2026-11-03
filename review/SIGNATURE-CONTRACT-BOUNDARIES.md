# Signature and contract verification review

The reviewed release is 5.0.1 (103), `c7acd23bb139864a40273f405d18b479589d2b20`. The repaired candidate is `9193c64c6435f60b3ec856e318cdc7d8df5935d8`. The complete WalletConnectSigner source module is compiled into the dependency build. Search of application and vendored source found no call into EIP191Verifier or EIP1271Verifier beyond their definitions. EthereumSignature is a public SDK type referenced by Oath's crypto adapter. This finding records direct type and internal verifier behavior. Exploitation through a current Oath screen has not been established.

The EIP-1271 interface takes a bytes32 hash and a variable-size signature. ABI bytes require a length word and padding determined by the actual byte count. The interface's return marker has a fixed meaning. [EIP-1271 specification](https://eips.ethereum.org/EIPS/eip-1271) · [ABI specification](https://docs.soliditylang.org/en/latest/abi-spec.html).

## Signature shape and recovery byte

EthereumSignature indexed its serialized input without checking the length. Empty and short inputs trapped. Longer inputs silently discarded middle bytes, and a 64-byte input reused its last scalar byte as the recovery byte. The raw-component constructor accepted arbitrary component lengths and recovery bytes. Serializing a recovery byte of 255 trapped during addition.

The repair checks both 32-byte components and the normalized recovery identifier at construction. The serialized constructor requires 65 bytes before indexing. It preserves the earlier wire normalization for 0–3, 27–30, 31–34 and 35–38. Other wire values throw. The EIP191 verifier propagates that error before invoking recovery. Tests enumerate all 256 raw and serialized recovery values, malformed component sizes, nonzero-origin Data slices and the production verifier's admission boundary.

Both public constructors now throw. Source callers must use `try`. This is an explicit source API change for consumers of the vendored type. The repository's production constructor call was updated, and app compilation validates the in-repository use. Serialized valid signatures keep their existing representation. The parsing tests establish structural admission, while cryptographic validity remains the responsibility of the injected recovery implementation.

## Contract request encoding and reply parsing

ValidSignatureMethod declared every signature as 65 bytes. Its padding helper also used the wrong units and padding direction. Nine of ten independently generated ABI vectors differed from the original encoder. The repaired method writes the actual length and pads the payload to the next word boundary. Its message hash must have exactly 32 bytes. The shared fixed-hash encoder now rejects a wrong length, including oversized values that previously caused a negative padding count. ENS method errors propagate through their existing throwing request paths.

The reply check previously accepted arbitrary content starting with the success marker and rejected uppercase hexadecimal forms of the same value. It now accepts the exact four-byte legacy representation or the correctly padded ABI word, with case-insensitive hexadecimal spelling. Garbage suffixes, dirty padding and extra words fail. This protects parsing correctness. Contract validation continues to depend on the RPC provider's truthful answer.

The vectors were generated with ethers 6.15.0 under Node 26.5.0 using Interface.encodeFunctionData. The generator and dependency integrity lock are public, and GitHub regenerates and compares the emitted Swift fixture. Synthetic hashes and sequential bytes carry no wallet credentials. [Vector generator and pinned dependencies](../fixtures/contract-signatures).

## Evidence

The same twenty methods were run against the original release and repair, each in an isolated process with network access denied. Original results contain five traps, twelve failing methods and three passing controls. All twenty pass after repair. The verifier fixture uses the real RPC serialization and verifier code with a synthetic HTTP response. The cryptographic fixture checks structural admission and call behavior. Real ECDSA recovery requires separate evidence.

[Exact-source replay and case logs](../evidence/5.0.1-build103/signature-contracts/result.json) · [Reproduction script](../scripts/signature-contract-boundaries.py) · [Signature finding](../findings/OW-2026-054.md) · [Contract finding](../findings/OW-2026-055.md).

ENS normalization, RPC response limits, the remaining message-signing interfaces and broader cryptographic provenance remain review work. Simulator and physical-device checks were outside this checkpoint.

Checkpoint 7 regenerated the same vectors with ethers 6.17.0 after updating an audit-only WebSocket dependency. The original fixture header and all vector bytes remain unchanged. [Tooling update receipt](../evidence/5.0.1-build103/address-checksums/oracle-update.json).
