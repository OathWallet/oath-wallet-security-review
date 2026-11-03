# Bitcoin signing, final proofs and independent consensus checks

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

The [signer finding](../findings/OW-2026-033.md) concerns an authorized signing request whose response could be invalid. The distinction between the transaction the wallet approved and a peer's assertion that it was already signed matters for both sign-only responses and retries from the local submission journal.

## Dependency trace

The previously traced BDK release [build](RESOLVED-PACKAGES.md) used a Cargo lock containing bdk_wallet 3.1.0 and miniscript 12.3.7. Both registry archives matched the SHA-256 in that lock. The [ledger](../scope/upstream-bitcoin-signers.json) lists all files in the two distributions. Five files have partial dispositions; hashing the remaining files did not confer review credit.

- The Rust FFI wallet method locks the PSBT and forwards signing options to the wallet library; the exposed PSBT finalizer clones its input and returns a success flag and the resulting packet. Those methods were traced in the [bridge ledger](../scope/upstream-bdk-ffi.json). The mutex lifetime, other FFI entry points and independent rebuild are still partial.
- The BDK single-key signer checks input indices and permitted hash modes. Its ECDSA branch returns early if the public key is already in partial_sigs. Its Taproot key-path branch signs only when tap_key_sig is absent. The wallet's finalizer can construct a witness from a supplied partial. Oath previously interpreted the presence of this output as proof that the current signing operation had produced it.
- In miniscript, finalize_input skips a previously finalized input. For an unfinalized one it constructs the satisfaction, collects previous outputs, and interprets the script. The interpreter uses separate legacy, SegWit v0 and Taproot signature-hash paths and libsecp256k1 verification. Our new verification packet supplies no final fields for a requested input. For a foreign input it supplies its authenticated previous output and a skip marker. Reconstruction and the final byte comparison cover only the requested single-key scripts. Hash flags outside Oath's supported set are rejected.
- App-side key lookup rederives the selected branch and leaf. Single, seed, aezeed, Electrum and extended-key inputs take different derivation paths. The Electrum branch delegates to its own validation. The ordinary send signer constructs the unsigned transaction, checks expected inputs and output totals, and asks BDK to sign. The returned raw transaction is checked against the plan. The selected normal-send tests below exercise those paths independently of the WalletConnect bug. Full review of the dependencies, other coins' signing modes, delegated derivation and consensus policy remains open.

## Local Bitcoin Core

The audit runner checks the upstream Bitcoin Core 32.1 arm64 macOS archive against two signed builder statements from a pinned revision of bitcoin-core/guix.sigs. It verifies the expected primary fingerprints for fanquake and hebasto and pins both executables by SHA-256. The node starts with a new temporary data directory, no peers and P2P networking disabled. The test may use only the designated local RPC port. The runner checks the chain, block height and network state, collects the XCTest outcome and terminates the node that it started. RPC cookies, node wallets and node data directories are never published. [Upstream release files](https://bitcoincore.org/bin/bitcoin-core-32.1/) · [Pinned builder statements](https://github.com/bitcoin-core/guix.sigs/tree/fdc0f9635ca5bee7dd46c51f3bcf3afca83b2d5d/32.1)

The five existing opt-in suites use the production signing modules. The matrix exercises 32 source/destination and receive/change combinations. A second suite includes a mixed 255-input sweep, fee and dust-change cases, an uncompressed import and a duplicate broadcast. The multisig suite covers fixed and HD signers and thresholds up to 15-of-15. The aezeed suite checks recovery, spendability, change and confirmation. The Electrum suite runs 11 fixture combinations across five seed kinds. The exact block heights in fresh chains are 165, 109, 111, 103 and 123 respectively. These are five existing tests enabled separately from the ordinary suite's opt-in skips.

The dApp fixture is a separate before/after experiment. It sends valid legacy and nested SegWit controls plus two packets contaminated with a different transaction's valid signature. Addresses in the request use WalletConnect's signet encoding. The same scripts are funded and mined only on regtest. An accepted case must receive the matching txid and a positive confirmation count. The signed packets were tested by Bitcoin Core's mempool, independently of the app's verifier. This setup does not test a public relay, signing UI or App Store executable.

## Reproduction

Start with a clean checkout of this audit tag on the documented Apple silicon toolchain. Python's standard library, curl and GnuPG are used for the Core installer. The full app tests and build remain available through scripts/run.py.

```sh
python3 scripts/checkout.py
python3 scripts/bitcoin-core-tools.py --destination .work/core/bin --evidence .work/core-tools.json
python3 scripts/bitcoin-signing-crates.py --cache .work/crates --output .work/signing-crates.json
cmp .work/signing-crates.json scope/upstream-bitcoin-signers.json
python3 scripts/bitcoin-connect-signature.py .work/source --scratch .work/sig-build --output .work/sig-results
python3 scripts/bitcoin_core_regtest.py .work/source --core-bin .work/core/bin --scratch .work/core-build --output .work/core-results
python3 scripts/bitcoin-connect-core-proof.py .work/source --core-bin .work/core/bin --scratch .work/wc-build --output .work/wc-results
```

The five old suites keep their original expectations and source bytes. The separate dApp fixture is added only to private build directories, with identical bytes on both application revisions. Failure to run a selector, a skipped opt-in scenario, an incorrect height, or unexpected external networking state prevents a passing result.

## Journal boundaries

The Bitcoin journal calls the verifier before database insertion and again when decoding a stored plan/signature pair. It compares wallet and account identity and the request fingerprint on idempotent insert. Its transaction checks active reservations before inserting outpoints; confirmed mainnet rows mark matching outputs spent. Existing tests cover conflicting ownership and outpoints, restarts, reset and accepted/confirmed monotonicity. Actual dApp UI, concurrent recovery callbacks and assurance for a third-party explorer's confirmation report remain separate questions. This checkpoint did not demonstrate a production journal entry, a user-visible balance discrepancy or an unauthorized payment.

## What Xcode compiled

The Release build named an exact Xcode build description in its checksum-verified log. The [input ledger](../evidence/core-signatures/oath-core48-evidence/build-inputs/release-inputs.json) reads that description. For each Swift target it cross-checks the compilation command against its written file list. For each C compile it also reads the emitted dependency file. It compares known source file bytes to the pinned repository inventories. This recovers selected source even when an incremental build reuses an object file. It does not claim a fresh compilation of every input or prove which individual symbols survive linking.

The unsigned arm64 build selected 2,268 Swift sources and 14 C translation units. The Clang dependency files add 71 non-toolchain inputs. The 2,353 distinct paths comprise 1,017 in the app repository, 1,316 in resolved package checkouts, and 20 generated by Xcode. Among the resolved source checkouts, 986 inputs came from the Stellar SDK, 167 from GRDB, 101 from SwiftDraw, 61 from swift-secp256k1 and one from the BDK Swift binding. Xcode separately processed four distinct XCFrameworks: aezeed, BDK, Wallet Core and WalletCoreSwiftProtobuf. An absent Swift file is not enough to rule out bundled resources, binary code, build-tool execution or a different build configuration. These counts do not change manual review dispositions.

The two peer fields involved are specified in [BIP 174](https://bips.dev/174/) and [BIP 371](https://bips.dev/371/). The change uses the existing BitcoinDevKit interpreter and does not add a signature-hash implementation to Oath.
