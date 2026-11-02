# Swift derivation-path values and extended-key validation

The Swift overlay shipped in Wallet Core 4.8.4 accepts paths of different lengths. A three-component account path survived parsing, but encoding and decoding it as JSON silently added two components. This changes the derivation path. The public app also uses a same-named type from BitcoinDevKit in some Bitcoin code. Those call sites do not establish that the Oath app encodes the affected Wallet Core type.

## DEP-CORE-009 · A saved path could identify a different derivation

Low severity in the app's reviewed context. A caller has to persist the affected library type and later use the decoded path. No Oath wallet, backup or funds were demonstrated affected. The [Swift implementation at lines 50–81](https://github.com/trustwallet/wallet-core/blob/d40d24a63d92619167903369308bf0e2f7eb3a59/swift/Sources/Extensions/DerivationPath%2BExtension.swift#L50-L81) serialized five BIP44 fields regardless of the actual number or hardening of components. A root, short, long or differently hardened path round-tripped to a different value. A valid numeric path whose first component had no generated Swift enum case crashed when encoding read its purpose.

The repair preserves the old five-field representation whenever it exactly reconstructs the path. For other paths it stores their complete canonical string. It accepts existing five-field records, rejects conflicting representations and validates a string before accepting it. An old decoder rejects the new string-only format. Previously lost information in a five-field record cannot be reconstructed. This patch fixes the encoding path; the generated nonoptional purpose accessor still assumes a declared enum case if called directly. Direct-property compatibility remains an open API review item.

## DEP-CORE-010 · An optional Swift subscript could terminate its caller

Low severity. The [Swift subscript at lines 38–40](https://github.com/trustwallet/wallet-core/blob/d40d24a63d92619167903369308bf0e2f7eb3a59/swift/Sources/Extensions/DerivationPath%2BExtension.swift#L38-L40) converted a signed machine index to UInt32 before reaching the bounds-checked native function. A negative index and an index one above UInt32.max each terminated their own test process. The repair uses an exact optional conversion. Both now return nil. The corpus also checks the last valid index and the first invalid index within the representable range.

[Source repair](../patches/walletcore-4.8.4-swift-path-values.patch) · [Identical Swift fixture](../tests/WalletCoreSwiftPathValues.swift) · [Per-case results and log hashes](../evidence/progress57/swift-path/result.json).

## Reproduction and boundaries

The test compiles the production Swift extension, generated path and enum wrappers and actual C/Rust libraries into a native macOS program. It invokes every case in a separate network-denied process, checks the expected assertion or trap and verifies unchanged source, fixture and library identities. It does not use test-only replacement types. Seven adverse cases reproduced before repair. All eleven cases passed after repair. The wrapper's first run expected a different word in the negative-index diagnostic and rejected that output. Its classification was corrected to match the observed Swift trap before rerunning the entire corpus.

Prepare the pinned Core checkout and a native build with the published eight prior repairs using the [native recipe](CORE-NATIVE-REPRODUCTION.md), selecting `patches/walletcore-4.8.4-combined-eight.patch` for this build. The Swift runner applies the new overlay only to its temporary source file.

```sh
python3 scripts/walletcore-swift-path-values.py /path/to/clean-core /path/to/prepared-core /tmp/path-results
python3 scripts/walletcore-native-tests.py /path/to/prepared-core --repair-set all-eight \
  --app-source /path/to/public-wallet --app-commit 8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707 --output /tmp/native-results
python3 scripts/walletcore-extended.py /path/to/clean-core /path/to/prepared-core --repair-set all-eight \
  --app-source /path/to/public-wallet --app-commit 8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707 \
  --boost /path/to/boost-1.90.0/include --full-suite --output /tmp/extended-results
```

The complete native build passed 2,363 C++ cases across 613 suites and 113 C cryptography checks. The extended-key fixture linked the same production libraries with hash-checked before/after HDWallet translation units. It reproduced its 21 original failures and passed all 94 repaired assertions. Its separately relinked full C++ suite also passed 2,363 cases. The two full executions exercise an overlapping suite.

We also traced the C version header, binding manifest and WebAssembly forwarding declarations and implementation. The C header declares ten public/private encoding pairs and the none value. The generated manifest lists seven mainnet pairs and none. The classifiers reject the three testnet pairs, none and unknown inputs. Both WebAssembly methods only forward to the respective C predicate. A host UBSan build of the production C++ implementation checked all 21 named values and 4,096 unregistered values. WebAssembly was inspected as source. Its runtime was not exercised. [ABI fixture](../tests/UpstreamHDVersions.cpp) · [Native evidence](../evidence/progress57/native/result.json) · [Extended-key evidence](../evidence/progress57/extended/result.json).

```sh
clang++ -std=c++20 -O2 -fsanitize=undefined -fno-sanitize-recover=all -I "$CORE/include" \
  "$CORE/src/interface/TWHDVersion.cpp" tests/UpstreamHDVersions.cpp -o /tmp/core-hd-versions
/tmp/core-hd-versions
```

Distribution of these two Swift repairs requires separate evidence for rebuilt frameworks, their integration into an app commit, and that commit's validation. Host results do not establish any of those steps. The 5.0.1 (103) tag is unchanged.
