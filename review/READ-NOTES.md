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

## Biometric credential and diagnostic admission review

- `OathBiometricCredentialStore.swift`: full source read. Protected Keychain item
  uses `WhenPasscodeSetThisDeviceOnly`, `biometryCurrentSet`, nonsynchronizable
  storage, and an installation/context-bound envelope. A successful policy
  evaluation alone does not open the wallet; the actual credential must be read.
  The one-shot request arbitrates cancellation, timeout and late delivery under
  a lock; production constructs a new request for every read. Cancellation is
  checked after delivery and before installation-envelope opening. No new defect
  confirmed. Runtime LocalAuthentication/Keychain behavior is not established by
  this source read; Swift Data clearing does not prove all copies are erased.
- `DiagnosticAvailabilityPolicy.swift`: full source read. Explicit typed/coded
  availability exclusions preserve returned errors, fatal/runtime diagnostics,
  and selected terminal send failures. Arbitrary failure text does not become a
  blanket timeout exclusion. Several older package tests still expect excluded
  timeouts/TLS/transport events; they must be reconciled individually with positive
  controls, not by changing the production policy to satisfy old expectations.

## Evidence identity guard

The inventory and host runner now both reject modified tracked files and
nonignored untracked inputs before claiming a pinned source identity. Five
synthetic Git-repository tests exercise exact revision, wrong revision, tracked
modification, untracked compilable input, and ignored build output. This is a
checkout guard, not a claim of a fully hermetic build: generated configuration,
toolchains, fetched dependencies and environment are separate recorded inputs.

## Application metadata and entitlements

Full reads of `OathApp/OathAtmosphere.entitlements`, `Info.plist` and
`PrivacyInfo.xcprivacy` identify two Keychain groups, the app's associated domain,
CloudDocuments container, one background status task and registered payment/
WalletConnect URL schemes. No arbitrary-load ATS exception appears in this
Info.plist. Custom URL schemes are untrusted input, not proof of sender identity.
The shared handoff Keychain group is an additional same-team entitlement boundary
whose member authorization and protocol require their own review. The public
Documents visibility of the iCloud container makes encryption before writing a
necessary boundary, not an assumption that iCloud files are secret plaintext.

The privacy manifest declares no collected data and no tracking. Reading that
declaration does not validate it: the network/SDK trace remains outstanding.
Selected `project.pbxproj` build settings show the same entitlements/Info.plist in
both configurations and script sandboxing enabled; the full project file remains
partially reviewed. Unsigned compilation does not verify provisioning or effective
App Store entitlements.

## Skipped-test reporting correction

Swift 6.4 `swift test --parallel --xunit-output` emits a successful empty test-case
element for some XCTest skips. A synthetic opt-in Bitcoin test was explicitly
rerun through `xcrun xctest`: it printed `Test skipped` while the earlier parallel
XML contained neither a skip element nor a failure. Consequently those parallel
XML skip totals are not reliable and must not be interpreted as zero skips.
The new host runner retains one log per XCTest process, recognizes the explicit
passed/skipped/failed line, rejects empty selections, writes accurate skip elements,
and runs Swift Testing separately. No opt-in network flags are enabled.

## Adapter and test corrections

`PublicSigningEVM.swift` adds four already-used public endpoint defaults without
changing chain-ID verification or account parsing. Full reads of the authority
suite and Bitcoin reconciliation-diagnostics suite include the new negative
controls: reject a wrong chain before account reads; reject an incorrect transaction
ID and retain its privacy-filtered validation report. TON/XRP test changes preserve
rejection of stale quotes while expecting their intentional availability error.
The XRPL retry test compares the complete decoded JSON object, preserving every
request value while accepting insignificant object-key ordering. These narrow test
edits do not imply full source review of the surrounding price/retry test files.

## Aezeed reachable Go source and independent vectors

The bridge's pinned module graph was resolved with Go 1.26.5 for arm64 macOS,
iOS and iOS Simulator compilation targets. This does not launch a simulator.
Each target selects 112 packages, including 29 nonstandard source inputs (one
is the application bridge). File hashes and module versions are retained in
`evidence/bridge/selected-sources.json`. Standard-library implementation review
and historical archive equivalence remain outstanding.

Full source reads: LND `aezeed/cipherseed.go` and `errors.go`, x/crypto's
`scrypt/scrypt.go` and `pbkdf2/pbkdf2.go`, and `kkdai/bstream/bstream.go`.
The reachable decode path checks external version and CRC before scrypt,
authenticates version/salt as AEZ associated data, and rejects authentication
failure. The bridge accepts only 33 input bytes, 4096 passphrase bytes and 19
output bytes, serializes KDF work, and permits internal versions 0 or 1.
The fixed production KDF parameters (32768, 8, 1, 32) avoid the generic helpers'
unchecked zero/negative-parameter cases; callers cannot choose these parameters.
The bitstream path always consumes/emits exactly 24 words of 11 bits. Unknown
word errors upstream contain input; the bridge returns numeric statuses only.
No new reachable defect was established in these files. This is a code review,
not a proof of cryptographic security or complete memory erasure: upstream KDF
buffers and copied seed values are not all explicitly cleared. AEZ's primitive
implementation and its architecture-specific backends remain outstanding.

The source constants select four bytes of AEZ authentication expansion. Legacy
format compatibility, password strength, and the probabilistic authentication
bound must not be confused with an unconditional guarantee of correct-password
recognition. No cryptographic format or shipped archive was changed.

LND's wordlist initialization and reverse-map construction were read; all 2048
unique words and their order match both the app resource and pinned Wallet Core
BIP39 list. The wordlist body has a generated-data verification disposition,
not a claim of manually assessing each word. `GoDependencyVectors.go` calls the
actual pinned scrypt, PBKDF2 and BStream implementations: five independently
specified RFC 7914 vectors and 1000 deterministic 264-bit cases pass. The 1 GiB
RFC vector is explicitly excluded. These checks do not prove AEZ or binary
provenance, and are separate from the LND-derived end-to-end seed fixtures.

Forty raw OSV advisory records remain preserved. Their explicit Go import-path
metadata (or explicit Go advisory aliases from the same scan) identifies SSH,
OpenPGP, and Windows packages absent from all three selected source targets.
The eight triage regression tests reject missing metadata, missing targets,
version disagreement, unrelated-module aliases and any selected affected path.
`source-advisory-triage.json` therefore records a source-level non-reachability
disposition, not clearance of the historical archives or all dependency code.

The arm64 AEZ dispatcher and `aez_ref.go` select the 64-bit bitsliced backend.
`round_bitsliced64.go` was read fully (key layout, fixed AES4/AES10 round order,
state cleanup and multi-block helpers). The dependency's `ct64` boolean-circuit
implementation remains outstanding. In `aez.go`, the extraction, associated-data
hash, 23-byte tiny-message path, decryption/tag comparison and dispatcher were
traced; the longer-message core and complete PRF were not, so the file remains
partially reviewed. Tag comparison accumulates differences before branching;
this source observation is not a measured timing guarantee. Existing upstream
AEZ, BStream, scrypt, PBKDF2 and Blake2b tests passed with Go's race detector.
Those test passes do not change unread files' dispositions.


## Additional WalletConnect and KMS review

At `f23413c848d202c2b3c7061bdb349e07144ab0a2`, read complete app files
`OathWalletConnectConsent`, `Policy`, `Connections`, `Service`, `Transport`,
`Message`, `RequestViews` and `TypedReview`. The service was traced through
all chain preparation/signing/recovery extensions, not just its EVM switch.

Proposal approval reloads wallet ownership and namespaces, blocks invalid/scam
verification and requires acknowledgment for unknown identity. Namespace methods
are restricted per chain family after the SDK's global builder. Signing rechecks
request/session/account ownership, expiry and current pending request across
awaits; signed broadcast recovery uses journal identity/fingerprint rather than
creating a new transaction. Disconnect removes the wallet mapping before relay
I/O. Presentation ownership and cancellation generations prevent a stale review
from acquiring a new request. This does not prove every downstream encoder or
provider preflight, nor every interleaving. Existing host harnesses replace some
vault/SDK/OS boundaries; runtime consent behavior was not exercised.

Typed-data review explicitly warns when the signed domain has no chain binding;
its detailed page renders the immutable signed fields. Ordinary message review
has a bounded preview plus full-message navigation. Display-control handling and
all localized renderings are not established by source inspection alone. The
transport caps messages at 1 MiB and pending writes at 64, completes each write
once under its lock, rejects stale task callbacks, and avoids logging peer close
reasons. Cryptographic primitives are still separate dependency boundaries.

Read complete vendored KMS files: `Envelope`, `Serializer`, `Serializing`,
`ChaChaPolyCodec`, `KeyManagementService`, `AgreementKeys`, `AgreementCryptoKit`,
`SharedSecret`, `SymmetricKey`, `KeychainStorage`, `KeychainService`, and
`GroupKeychainStorage`; also `NetworkingClientFactory`, `ConsoleLogger` and
`LoggingLevel`. CryptoKit supplies X25519, HKDF-SHA256 and authenticated ChaChaPoly.
Type-1 derived-key persistence occurs after authenticated decoding. Apple
Keychain items use AfterFirstUnlockThisDeviceOnly. This concerns relay/session
keys, not the application's wallet-secret vault. Read/migration errors, teardown,
shared-access-group scope and Apple implementation behavior remain separate
integration boundaries. There is no complete memory-erasure or constant-time
proof here.

The configured networking and serializer loggers are off, with no app caller
found enabling their debug logging. The SDK still has decrypted-payload debug
logging branches; reading the default configuration does not prove those branches
safe if another caller enables them. `NetworkingInteractor` was read only through
construction/subscription and receive dispatch, and `LinkEnvelopesDispatcher`
only through its first request path; both remain partially reviewed. Type-2
unencrypted/link-mode separation requires further integration tracing.

The existing SDK host harness compiled production modules and passed 19 cases,
with one deliberate fresh-process diagnostics skip. Running that one case alone
with its documented fixture flag passed. This is 20 distinct case passes across
two processes, not an end-to-end relay test. An apparent empty-envelope bounds
concern was checked against the production malformed-envelope test and a native
Foundation probe: both rejected/handled it without a crash on this host. It is
not recorded as a confirmed vulnerability; that host result does not establish
behavior on every OS runtime.


## WalletConnect relay ingress and session/history review

Read the complete `NetworkingInteractor`, `SessionEngine`, `SessionRequestsProvider`,
`InvalidRequestsSanitiser`, `RPCHistory`, and `RPCHistoryFactory` implementations,
plus the new production-boundary regression fixture. Their ledger hashes identify
exact inputs. OW-2026-004 records the confirmed unauthenticated type-2 dispatch
and its tested fix; the earlier need to trace this path is now resolved as a
finding, not a general clearance of WalletConnect.

The session engine checks existing sessions, chain/method permissions and request
expiry; delete processing relies on transport authentication. History stores
requests by RPC ID and resolves responses by ID. Review identified a further
question about response/topic correlation and same-method concurrent waiters;
the cross-topic response consumption was reproduced with synthetic encrypted frames, but the repair remains open pending authentication-response topic compatibility tests. The same-method waiter concern remains unconfirmed.
The request-provider debounce is wall-clock based and dispatches the oldest
pending request. Runtime scheduling and downstream policy interactions still
need adversarial tests. `reviewed` means the listed source was read; it does not
mean no bugs or all runtime paths proven.


## Response-topic repair and persisted routing

Read the complete JSONRPC `RPCRequest` and `RPCID`, the updated history and
network ingress, `SessionAuthRequestService`, `LinkAuthRequester`,
`WalletErrorResponder`, authentication request parameter schema, `CodableStore`
and `KeyValueStorage`, plus both new regression files. The Notify producers'
request/response-topic construction was traced, but their identity signing and
DID/config dependencies are not fully reviewed and their entries remain partial.

OW-2026-005 confirms cross-topic response consumption. A simplistic same-topic
candidate was withheld after source review showed authentication's deliberately
separate reply topic. The repair persists a local-only expectation and retains
legacy authentication routing from the stored public key. Twelve focused tests
cover rejection, valid responses, restart, malformed routing and JSON injection.
The same-method `awaitResponse` waiter concern remains unconfirmed and outside
this fix; it is called by the unused Notify history product in the observed tree.
No complete peer authentication, Notify migration or real network protocol run
is claimed. WalletConnect session/runtime coverage remains incomplete.

## Scanner and pairing URI boundary review

See [INPUT-BOUNDARIES.md](INPUT-BOUNDARIES.md) for the a65601b source reads,
partial traces, new OW-2026-006 finding and explicit host/runtime limitations.
Earlier findings, attempts and evidence remain unchanged.


## Aezeed repaired-source and archive follow-up

Read the complete disposable source preparer, archive build script, test script,
paired regression file, production-vector test, repair manifest, patch, bridge
README and provenance manifest in application commit 92423215. The copied LND
fixture is byte-identical to the canonical package fixture. The three repaired
upstream CBC/GCM/BLAKE2b implementations retain their earlier full-source reads;
the changed validation ordering and length encodings were re-reviewed alongside
the identical before/after regression corpus. New hashes are explicit in the
upstream ledger, with original upstream hashes retained.

All three target source inventories select the repaired hashes. The ten generated
framework files have verified manifest hashes and two-isolated-build evidence;
that generated-artifact disposition is not a source review of compiler output.
The metadata-only final commit preserves all sixteen input and ten output hashes.
No timing proof, whole-toolchain review, historical App Store equivalence or
broader runtime coverage is inferred. See AEZEED-DEPENDENCY-REPAIRS.md.

## Progress 20 — repaired Core application selection

At `27fcf5f58f6169e1a40fb6afced883bc736d124d`, read the complete Core binary-target
manifest, provenance JSON, debug-symbol downloader and symbol input list. Public
artifact/symbol checksums, expected UUIDs, source pins and archive recipe agree.
The final build embeds the selected framework binaries byte-for-byte. Scope and
limitations are recorded in [CORE-APP-INTEGRATION.md](CORE-APP-INTEGRATION.md).
`TronSendPlan.swift` was read completely for local guards but remains partial;
producer/consumer binding, fee relations and delegated validators need further
review. No new finding is asserted for that file.

## Progress 21 — TRON send trace and adversarial corpus

At the unchanged application target 27fcf5f, read the complete TRON plan, crypto,
identity/models, multisig policy and permission-control sources. Trace amount
limits and resource-based fee reservations into signed bytes; inspect signature
membership, exact envelope reconstruction, threshold preservation and integer
overflow guards. Six audit-only property cases call the production package.
Known-answer fixtures are existing TronWeb 6.2.2 outputs, not a freshly executed
JavaScript generator. Read the new Python runner and Swift test fixture in full.

The complete receipt decoder, client, app service, signing adapter and database journal were read,
but retain partial dispositions. Only TRON-specific methods in the shared vault,
reconciliation and permissions files and fee/total access sites in the review
UI were read in this increment. HD derivation, WalletConnect context, provider
trust, service lifecycle and migration/index assumptions remain open. Scope and
finite test coverage are explicit in [TRON-SEND-TRACE.md](TRON-SEND-TRACE.md).
No new production vulnerability was established; no app behavior was changed.
