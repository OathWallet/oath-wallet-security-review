# Native Core validation and extended-key type repair

> Integration update: the eight repairs are now selected by public app commit
> `27fcf5f58f6169e1a40fb6afced883bc736d124d`, merged in PR 11.
> [Final app checks and remaining gaps](CORE-APP-INTEGRATION.md). Earlier
> integration-outstanding statements below describe their original checkpoints.

Application scope: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
Upstream: Wallet Core 4.8.4, `d40d24a63d92619167903369308bf0e2f7eb3a59`.
This is a maintainer-commissioned Codex review increment, not an independent
certification, App Store result or whole-wallet completion verdict.

## DEP-CORE-005: public extended key accepted as a private derivation source

At baseline `src/HDWallet.cpp:314–327`, `getPrivateKeyFromExtended` invokes the
same deserializer as the public-key API. At `HDWallet.cpp:373–388` that helper
accepts either public or private version bytes. A public encoding fills the
public-key field while the private-key field remains zero. Non-hardened child
derivation then produces an unrelated private key instead of rejecting the
wrong input type. The returned key is **not** the private key corresponding to
the supplied xpub. This is not recovery of an xpub owner's private key.

Classification: dependency API correctness defect, application exploit not
established. A caller that assumes this API validates private extended inputs
could use an incorrect derived account. No call to this C++ private-extended-key
API was found in Oath's reviewed application/package source. The public C ABI
wrapper exposes the public-key version, not this private-key API. No fund-loss
scenario or transaction was executed.

The [patch](../patches/walletcore-4.8.4-extended-key-kind.patch) adds an explicit
private-input requirement to that caller and rejects public version bytes before
derivation. Public extended-key behavior and valid private inputs are preserved.
Apply it after the four [earlier repairs](CORE-SOURCE-REPAIRS.md). Neither patch
is incorporated into Oath's distributed Apple frameworks yet. Status remains
**source-repair-tested-integration-outstanding**.

## Identical before/after reproduction

[The fixture](../tests/UpstreamExtendedKeyKind.cpp) uses a public BIP39 test phrase,
ten extended-key version pairs, three address indices, malformed strings and an
existing zero-scalar rejection case. Seven mainnet version pairs are supported;
three testnet enum pairs remain rejected by the upstream version classifier.
Valid public/private results are compared with direct derivation from the same
fixture wallet. This is a type/compatibility test, not an independent BIP32 oracle.

- Before: 94 checks, 21 failures; only nine unsupported public inputs rejected.
- After: the same 94 checks, zero failures; all 30 public inputs rejected.
- The complete upstream C++ suite passes with the repaired translation unit:
  2,363 tests across 613 suites, zero failures, errors or disabled tests.

The runner compiles complete production `HDWallet.cpp` translation units with
identical flags and links actual locally built Core, Trezor, Rust and protobuf
libraries. It does not replace derivation or cryptography with stubs. Source,
patch, fixture and library hashes are recorded and rechecked. The full-suite
mode links the repaired object before the original archive so the linker uses
the complete repaired translation unit.

## Full native source build

The four-repair native build separately passes 2,363 C++ tests and 113 C
cryptography checks. The full production constructor test also passes its 22
positive cases and the four rejection/lifetime cases. Earlier isolated
ASan/UBSan results remain separate: **this full native build is optimized, not
sanitizer-instrumented**.

Toolchain: Apple Clang 21 / Xcode 27.0 on arm64 macOS 27, CMake 4.3.4, Boost
1.90.0 headers, Ruby 4.0.5, Rust nightly-2025-12-11, cbindgen 0.29.2.
Pinned downloaded inputs: googletest 1.16.0, Check 0.15.2, protobuf 3.20.3,
nlohmann/json 3.11.3. Archive hashes, dependency lock hashes and command logs
are retained in [native evidence](../evidence/core-native).

The build emits older macOS deployment-target warnings; passing on this host
does not establish older macOS compatibility. No iOS framework, application
runtime or source-to-historical-binary equivalence is established by this build.

## Failed attempts retained

1. Initial full native compilation lacked the Check headers. Building the pinned
   Check dependency resolved the prerequisite failure; subsequent compilation
   completed. The interrupted parent command's missing final record is not used
   as exit-status evidence: a later recorded build verification exits zero.
2. Running the C++ binary from `build/native-core/tests` selected the wrong fixture
   root and ultimately crashed loading a missing test key file. Upstream's test
   main derives `TESTS_ROOT` from three parent directories of the executable.
   A byte-identical copy at `build/tests/tests` selects the actual source fixtures
   and passes. `ctest -N` listing zero tests was not counted as test success.
3. The first extended-key fixture incorrectly treated all declared enum values
   as supported. It was corrected against the actual public/private classifiers;
   unsupported testnet values still reject. The initial 39/18 failure counts
   are retained; the final identical corpus has 21/0 failures.
4. One exploratory compile failed for a missing Boost include; a shell then ran
   an old probe binary. That output is explicitly **not expanded-fixture evidence**.
   Later runs use checked command status and never execute after compile failure.
5. The first reusable full-suite runner inserted its object before a `ccache`
   compiler argument. That link failed. The corrected runner inserts before
   the output option, after compiler launchers and before libraries.

No failed attempt has been relabeled as a passing application test.

## Reproduce

Prepare the native checkout using [the build recipe](CORE-NATIVE-REPRODUCTION.md).
The original upstream checkout must stay clean; the prepared checkout contains
only `walletcore-4.8.4-api-repairs.patch` plus ignored generated build inputs.

```sh
python3 scripts/walletcore-native-tests.py /path/to/prepared-core \
  --app-source /path/to/oath-wallet \
  --app-commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --output /tmp/native-tests
python3 scripts/walletcore-extended.py /path/to/clean-core /path/to/prepared-core \
  --app-source /path/to/oath-wallet \
  --app-commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --boost /path/to/boost-1.90.0/include --full-suite \
  --output /tmp/extended-key-tests
```

Native preparation currently requires the documented local tools. A fresh
dedicated GitHub native-build job is still outstanding. The local results must
not be presented as results of that unexecuted job.

## Manual source disposition and remaining work

`src/interface/TWHDVersion.cpp` was read in full: both predicates whitelist seven
mainnet encodings and return false for all other values, including `None` and
testnet enum values. There is no parsing, allocation or secret material in these
predicates. Its hash-bound ledger entry is now reviewed. Re-reading the complete
C wrapper confirmed its existing disposition and the lack of a private-extended
key entry point. `HDWallet.cpp` stays partially reviewed: ignored child-derivation
return values, copying, transient secret lifetime and other callers still need
work. Compiling thousands of files does not mark them reviewed.

Apple framework integration, app compatibility validation, remaining dependency
and application review, three previously documented unused Go API hazards and
historical binary provenance remain open. No App Store operation or physical
device use occurred in this increment.
