# Wallet Core source repairs — not yet incorporated into Oath

Baseline dependency: Wallet Core 4.8.4,
`d40d24a63d92619167903369308bf0e2f7eb3a59`.
Application call-path target: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
The [published patch](../patches/walletcore-4.8.4-api-repairs.patch) addresses
four previously documented defects. **These fixes pass source-level host tests;
the shipped dependency and application binary are not changed by this patch.**
The original [derivation](CHILD-DERIVATION-REVIEW.md) and
[constructor](CONSTRUCTOR-LIFETIME-RESULTS.md) results remain preserved.

## Repairs and identical before/after checks

- **DEP-CORE-001:** unknown curve names reached a null `curve_info` dereference
  in `hdnode_deserialize` (baseline `bip32.c:752`). The same subprocess crashes
  under UBSan before repair and returns a rejection after repair. Both public
  and private deserializers now reject null names too. Additional after-only
  guards verify a missing or unsupported curve cannot populate the key cache.
- **DEP-CORE-002:** the non-Weierstrass public-key dispatcher omitted Nano
  (`bip32.c:484–518`). The baseline asserts on an all-zero cached public key.
  The patched dispatcher generates the BLAKE2b Ed25519 key and sets the cache
  marker only after a recognized branch completes. Sixty-four deterministic
  public fixtures compare the output against the separate primitive used by
  Core's `PrivateKey`; repeated calls preserve it. This tests dispatch and cache
  behavior, not independent mathematical correctness of that primitive.
- **DEP-CORE-003:** `HDWallet<32>` mnemonic expansion wrote a 64-byte KDF result
  into a 32-byte member (`HDWallet.cpp:50–62`). The patch rejects non-64-byte
  mnemonic expansion before calling the KDF. Identical mnemonic and entropy
  calls previously abort with assertions enabled or return corrupted state
  with `NDEBUG`; both now throw `invalid_argument` in both configurations.
  Additional after-only random-strength checks reject the unsupported
  specialization. Raw 32-byte seeds remain supported for the existing caller.
- **DEP-CORE-004:** the destructor did not wipe its entropy vector
  (`HDWallet.cpp:102–106`). The matching allocator/deallocator fixture observes
  the same public 16-byte allocation immediately before free: all fixture bytes
  remain before repair, and all bytes are zero after it, in both configurations.
  This is a specific erasure improvement, not a proof that every copy is wiped.

No reachable Oath exploit was established for the first three API cases. The
entropy result is a local memory-hygiene finding, not evidence of a remote
memory disclosure. Source reachability, severity and exposure must not be
inferred from the isolated harness alone.

## Retests and integrity

Both sides use identical fixture hashes and the same Clang ASan/UBSan flags.
The C harness also passes 52 official SLIP-0010 vectors, 1,920 independently
calculated hardened-derivation cases, 33 public/private child comparisons,
20,000 malformed extended-key calls and two unchanged-on-failure checks.
The constructor harness passes 22 positive compatibility checks in each of
assertion-enabled and `NDEBUG` configurations before and after repair.

The constructor build still uses the exact contiguous production constructor
and destructor bodies, actual class layout and production mnemonic/KDF sources;
it does not compile the entire `HDWallet.cpp` translation unit. The C harness
compiles the 61 production C files into an archive and links the needed objects.
The tests do not prove equivalence with the distributed Apple frameworks.

A disposable checkout applies the exact published patch to the verified clean
pin. The baseline remains untouched. Source changes, newly untracked inputs,
or patch changes during execution fail the harness. Seven new integrity checks
bring the audit-helper suite to **62 passing tests**. Its initial macOS `/var`
versus `/private/var` fixture assertion failure is retained beside the corrected
run; it was a test-path comparison defect, not an application failure.

[All logs, input hashes, toolchain identities, fixture hashes, commands and
manifest](../evidence/core-source-repairs) preserve both stages. A successful
**baseline** harness means that it reproduced the expected known failures;
a successful **repaired** harness means those cases passed against the patch.
They are separate result types and neither is a whole-wallet verdict.

## Reproduction

Use the recorded Clang toolchain and Ruby 4.0.5. Both source repositories must
be clean and pinned as above. From this audit repository:

```sh
python3 scripts/walletcore-bip32.py /path/to/wallet-core \
  --app-source /path/to/oath-wallet \
  --app-commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --output /tmp/core-before
python3 scripts/walletcore-bip32.py /path/to/wallet-core \
  --app-source /path/to/oath-wallet \
  --app-commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --repair --output /tmp/core-after
```

Repeat both commands with `walletcore-constructors.py` and different output
directories. The audit-only GitHub workflow runs both stages without secrets.

## Remaining work

At this snapshot, full native dependency compilation, rebuilt Apple framework
integration, application compatibility and generic iOS build verification
remained outstanding. [Progress 16](CORE-NATIVE-AND-EXTENDED-KEY.md) subsequently
completed native compilation and suites; Apple integration is still outstanding.
The pinned upstream build requires generated protobuf/Rust interfaces and Rust
libraries, not just the patched files. Broader secret lifetime, transient entropy
buffers, default copy/move behavior, other curves and transitive cryptographic
implementations remain review areas. Existing findings stay open until their
integration requirements are met. No application source, simulator, physical
device or App Store operation changed in this increment.
