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
