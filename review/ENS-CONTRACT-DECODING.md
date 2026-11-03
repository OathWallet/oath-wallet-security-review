# ENS contract response decoding

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

## Source and execution boundary

The reviewed source is 5.0.1 (103), commit `c7acd23bb139864a40273f405d18b479589d2b20`. The complete WalletConnectSigner module is a compiled dependency of WalletConnectSign. The public factory can construct an ENS resolver, which uses ENSRegistryContract and ENSResolverContract to decode JSON-RPC strings. A search of the application source and vendored modules found no application call into ENSResolverFactory, resolveEns or resolveAddress. This review establishes the dependency decoder's behavior under direct host calls. It does not establish a remotely reachable crash in Oath's current screens.

The name and address interfaces are described in the ENS interface reference. Integer, address and dynamic-byte encodings follow the Solidity ABI. The fixtures exercise the legacy resolver profiles used by this implementation. [ENS interfaces](https://docs.ens.domains/resolvers/interfaces/) · [ABI specification](https://docs.soliditylang.org/en/latest/abi-spec.html).

## Reading and reproduction

ContractDecoder force-unwrapped the conversion of a 256-bit word into the host Int. Its dynamic-byte reader multiplied untrusted offsets and lengths by two before checking the available input. Its address reader stripped high bytes without validating them or the remaining hexadecimal text. Its byte reader used the permissive Data(hex:) initializer and accepted missing or nonzero ABI padding.

The existing host SDK harness now compiles the complete production WalletConnectSigner module alongside its actual networking, HTTP, utility and JSON-RPC dependencies. Sixteen XCTest methods exercise the decoder and the production ENSResolverContract response path. The HTTP test double returns synthetic JSON-RPC results, and the per-case runner denies network access. The production implementation is never copied into the tests.

On the original release, seven isolated processes trap, four methods report assertion failures, and five positive or already-protected cases pass. On the repair, all sixteen pass. The bounded mutation method checks seven invalid byte values at all 64 positions of a word, for 448 deterministic mutations and two decoder assertions per mutation. Tests also cover valid address casing, Int.max, empty bytes, boundary payload sizes up to 1,024 bytes, UTF-8 names and invalid UTF-8. [Exact-revision replay and sanitized logs](../evidence/5.0.1-build103/ens-contract-decoding/result.json).

The replay checks out each pinned revision, verifies it is clean, then overlays only the same regression test and build harness. Each SDK implementation stays at its pinned source. Crashes, assertion failures, positive controls and successes have separate recorded outcomes. Each result records fixture, decoder and harness hashes. [Replay command implementation](../scripts/ens-contract-boundaries.py).

## Repair and compatibility

The repaired reader accepts only byte-aligned ASCII hexadecimal RPC results. Int conversion is checked. Dynamic offsets must be nonnegative, word-aligned and within the input before multiplication. Length and zero-padding checks precede slicing. Address words must have zero high-order padding. The API continues to return the original tuple types and throws its existing error cases on malformed inputs.

Valid legacy ENS response fixtures still decode. Malformed responses now produce errors instead of a process trap or an apparently valid decoded value. The existing SDK suite and diagnostics suite are run separately from the new regressions. The unsigned generic iOS Release build passed. [Validation receipt](../evidence/5.0.1-build103/ens-contract-decoding/validation.json) · [Merged PR 66](https://github.com/devdasx/oath-wallet/pull/66).

## Remaining scope

ENS name normalization, reverse-to-forward name confirmation, RPC trust and response-size limits require further review. The encoder and the EIP-191 and EIP-1271 implementations are outside this finding and remain separate review work. There is no live resolver, simulator, physical-device or Apple-distributed-binary verification in this checkpoint. The source repair follows the immutable submitted source tag. [Finding OW-2026-053](../findings/OW-2026-053.md).
