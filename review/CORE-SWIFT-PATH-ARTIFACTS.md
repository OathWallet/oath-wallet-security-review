# Rebuilding the Swift path repairs for iOS

[Host reproducer, patch, compatibility and limitations](CORE-SWIFT-PATH-VALUES.md).
The artifact release is **walletcore-4.8.4-swift-paths-1**. It is a dependency update for subsequent public app source. The submitted 5.0.1 (103) source tag continues to identify its original inputs.

Start with the [native build recipe](CORE-NATIVE-REPRODUCTION.md) and the `walletcore-4.8.4-combined-eight.patch` repair set. With clean, pinned Core and SwiftProtobuf checkouts, use the existing [Apple build procedure](CORE-APPLE-REPRODUCTION.md) with both options below. The script separately validates the native code and the Swift overlay. It compiles generic iOS and simulator architectures without launching them.

```sh
python3 scripts/walletcore-apple.py --repair-set eight --swift-path-values \
  --source "$CORE_SOURCE" --native "$PREPARED_CORE" --generator "$PROTO_GENERATOR" \
  --runtime "$PROTO_RUNTIME" --rustup-home "$ISOLATED_RUSTUP" --cargo-home "$ISOLATED_CARGO" \
  --output "$NEW_OUTPUT_DIRECTORY"
```

The protobuf distribution ZIP applies the existing resource-metadata repair after compilation. Four Info.plists differ between the raw and distribution ZIPs. Both archives contain the same executable, debug symbols and privacy manifests. [Pinned checksums, build steps, tools and device binary UUIDs](../evidence/5.0.1-build103/core-apple/artifacts.json). The byte hashes identify these outputs. A second independent byte-identical Apple build has not been demonstrated.

## Integration after build 103

[Wallet PR 57](https://github.com/devdasx/oath-wallet/pull/57) updates both package pins and their matching symbols. Both framework executables embedded in the unsigned generic iOS Release archive matched the public package bytes. Both dSYM UUIDs matched the device binaries. The tested commit and the merged commit have the same Git tree. The diagnostics package passed 119 tests and skipped two. [Archive evidence](../evidence/5.0.1-build103/core-apple/integration.json). This evidence applies to public app source after the build 103 tag.
