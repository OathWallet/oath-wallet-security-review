# Source review notes — bounded coverage

These notes describe the inspected paths, not a whole-wallet conclusion.
The file ledger is authoritative for remaining coverage.

## JSON and WalletConnect signing

`WalletConnectJSON.swift` implements a bounded byte parser, preserves numeric
lexemes, rejects duplicate decoded keys, and validates strings/number grammar.
The missing object entry limit is OW-2026-001. The production parser now rejects
the same over-limit object that the baseline accepted. The 6,016-case harness
also checks nested limits, duplicate escaped keys, malformed input, depth/bytes,
large numeric lexemes and 2,000 seeded reference cases with mutations.

`OathEVMSigning.swift` and `OathWalletConnectSigning.swift` bind requests to wallet,
account, network and derived sender, and check typed-data chain/session
information. Selected `OathWalletVault` callers were separately inspected for
authentication-generation checks around awaits; that larger file remains only
partially reviewed. This is a file-level
inspection. The UI consent, relay, provider, all downstream encoders and other
chain paths still require a complete trace. No end-to-end signing claim follows.

## Local storage and clipboard

`OathInstallationSecurity.swift` serializes installation-key access, wraps stored
material with authenticated encryption and context, rejects symlink paths,
sets file permissions, and excludes the installation store from backup.
`OathInstallationKeychain.swift` constrains the affected service names.
These checks do not establish the behavior of all callers, OS access-control
transitions, concurrent reset/recovery paths or a compromised operating system.

`OathSensitiveClipboard.swift` keeps secret copying local to the device and sets
a 60-second expiration; ordinary public-address copying uses a separate path.
Clipboard expiry does not revoke a copy already read by another process.

## Aezeed

The Swift wrapper bounds phrase/password bytes, decodes 24 words, checks CRC,
rejects unsupported outer versions, preserves password UTF-8, maps bridge errors
without credential text, and clears mutable input/output buffers. Runtime copies
can remain; this is not guaranteed memory erasure.

The restored Go bridge bounds ABI sizes, serializes KDF calls, rejects unsupported
internal versions, clears mutable temporary buffers, and converts errors/panics
to numeric status. New Go tests call that production decoder, including correct
vectors, wrong passwords, every envelope-byte mutation and size rejection.
They do not test every unsafe ABI pointer permutation. Source tests and public
fixture generation pass. Historical archive reconstruction differs: OW-2026-002.

## Trust Wallet Core sampling

Tag 4.8.4 resolves to `d40d24a63d92619167903369308bf0e2f7eb3a59`.
Sampled `src/HDWallet.cpp` and `src/PrivateKey.cpp`; these files are not fully
reviewed. Read `trezor-crypto/crypto/rand.c`: its default random functions open
`/dev/urandom` and abort on open/short-read failure. The functions are weak symbols;
linkage and replacement behavior of the shipped Apple binary are not proven by
reading this source. The package's published archive checksums are integrity
pins, not proof of source-to-binary equivalence. Reachable upstream signing,
derivation and cryptographic implementations remain a substantial review gap.

## Envelope and portable backup validation

Read the complete `OathVaultEnvelope.swift`, `BackupDocument.swift`, and
`OathInstallationVaultStorage.swift`. The vault validates format, fixed KDF cost,
salt, protection variants, membership uniqueness, lifecycle and version-specific
material. Ciphertext binds the root and member index; the installation wrapper
authenticates the complete stored envelope and account context. The portable
backup bounds total input before decoding/deriving, authenticates its serialized
header with AES-GCM, fixes the KDF parameters, and validates supported material
combinations and network/account structure. PBKDF2 uses 600,000 rounds; mutable
plaintext/password buffers are cleared after use. This does not prove complete
memory erasure. Legacy migration callers and every restore-chain derivation
remain outstanding even though these individual files were read. No additional
exploitable issue was confirmed in these file inspections.

## Additional source read: import, restoration, export and request interpretation

The complete files listed below were read at `ae5a35cec58f51bcfd6de3cd55950b47fa055a51`.
This disposition records a bounded source examination, not proven absence of defects.

- `OathWalletEngine.swift`: creation enters Wallet Core at 128-bit entropy; import
  revalidates BIP39, Electrum or aezeed, with Bitcoin-only alternate seed profiles.
  Reviewed explicit coin/path mapping and restored account derivation. Downstream
  multisig implementations and native binary derivation remain separate gaps.
- `OathPrivateKeyImport.swift` / `OathImportedPrivateKey.swift`: 2 KiB input cap,
  explicit chain selection, WIF compression and extended-key identity, validated
  Ed25519 public halves, Stellar checksum, algorithm-tagged Sui/Aptos parsing,
  curve validation, and no fabricated HD scope for single keys. Swift copies and
  strings mean buffer clearing does not prove complete process-memory erasure.
- `OathPrivateKeyExport.swift`: committed path and address are rechecked, UTXO
  compression/chain codes preserved, and exported formats are chain-specific.
  Fresh authorization belongs to the vault caller, not this internal formatter.
- `OathVaultImportPreparation.swift`: handoff validates declared chain, account
  uniqueness and derived address equality; unsupported descriptor collections
  fail rather than silently losing signing sources.
- `OathWalletRestoration.swift`: bounded accounts, path segments, uniqueness,
  exclusive secret-material representations and derivation-before-commit.
  Migration/recovery coverage remains dependent on the vault lifecycle review.
- `OathWalletRemovalModel.swift` / `OathResetEnvironment.swift`: cancellation
  generations, scoped removal grant, confirmation ownership and sandbox cleanup;
  iCloud is outside local reset. Only missing files are ignored; symlinks are
  unlinked rather than traversed. Actor-side grants still require separate review.
- `WalletConnectTypedData.swift`: exact JSON fields, integer precision, typed
  ranges, bounded recursion/collections, exact domain/session chain match when
  supplied, cycle-bounded type dependencies, visible controls, immutable digest,
  signature recovery check, owner-bound recognized permits and time revalidation.
  Missing domain chain is intentionally represented as generic review; whether
  the UI communicates that clearly remains an outstanding presentation check.
- `UTXOBroadcastProvider.swift`: verifies journal bytes/txid before sending,
  reconciliation requires identical raw bytes (including witness), and hedges
  only the same transaction. Cancellation checks prevent reporting a cancelled
  response as acceptance. A task group still waits for cancellation-resistant
  child tasks; no universal wall-clock bound is established by this read.
- `PublicSigningAuthority.swift` / `PublicSigningEVM.swift`: mainnet identity
  verification, fixed-block reads, Safe proxy and implementation fingerprints,
  bounded ABI owners/threshold decoding. The existing exhaustive adapter test
  identifies missing Filecoin, Sei, 0G and IoTeX entries. No direct app caller of
  this account-policy API was found; the public endpoint map is also reused by
  stablecoin checks. No fund-loss exploit has been demonstrated.

## Upstream entropy source trace

Pinned Trust Wallet Core `d40d24a63d92619167903369308bf0e2f7eb3a59`:
`HDWallet.cpp` creation -> `mnemonic_generate` in `trezor-crypto/crypto/bip39.c`
-> `random_buffer` in `trezor-crypto/crypto/rand.c` -> `/dev/urandom`.
Creation rejects unsupported strengths; the random reader aborts on open/read/
short-read failures. `scripts/upstream-entropy.sh` compiles that production C
file with only the system-call boundary replaced by deterministic fault fixtures.
Eight success/failure scenarios pass locally. This is not a statistical entropy
assessment, review of all BIP39/HD derivation code, or proof of shipped-binary identity.
`rand.c` and `TWHDWallet.cpp` were read in full; `HDWallet.cpp` and `bip39.c`
were traced only through creation and remain partially reviewed.
