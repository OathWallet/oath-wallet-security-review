# Selected aezeed dependencies — progress 10

Follow-up: these three originally reproduced defects now have [tested source
repairs and rebuilt public app archives](AEZEED-DEPENDENCY-REPAIRS.md). The
original review and failing evidence below are retained as historical evidence.


Application target: `f7441b85d5216b702dde490eb027aece1a6cfb5a`.
This maintainer-commissioned Codex source review follows progress 9. It is not
independent certification, a timing proof, or clearance of the historical binaries.
All 28 selected dependency file hashes were rechecked against the module cache;
`evidence/aezeed-dependencies/verified-source-hashes.json` records the identities.

## Source reads and dispositions

The following files were read in full, in addition to the progress-9 reads.
Their exact module versions and SHA-256 identities are in `scope/upstream-aezeed.json`.

- `aez/aez.go`: key extraction, I/J/L derivation, nonce/AD hashing, short-message
  Feistel paths, core two-pass/fragment handling, PRF, append semantics and tag
  checking. Branches depend on public lengths/rounds except the final success
  decision. The generic API assumes nonnegative tag size and nonoverlapping
  input/destination; it does not enforce every precondition. Rejected decryption
  returns nil/false, but temporary/caller backing storage is not guaranteed erased.
  Oath uses a fresh nil destination through LND; failed outputs never cross its C ABI.
- `bsaes/ct32/aes_ct32.go`, `aes_ct32_enc.go`, `aes_ct32_dec.go`: Boolean S-box,
  orthogonalization, AES-128/192/256 expansion, forward/inverse row and column
  transforms, single/two-block loads/stores and Reset guards. Array sizes and
  public round indices were traced. These are compiled package files, but arm64
  AEZ selects its ct64 round adapter. Tests explicitly exercise ct32 nevertheless.
- `bsaes/ghash/ghash.go`: masked carryless multiplication, bit reversal,
  polynomial reduction, initial state and zero-padding of the final block.
  It is compared with a separate bit-serial polynomial implementation at 514
  lengths, including empty, partial, multiple-block and unaligned inputs.
- `bsaes/internal/modes/modes.go`, `cbc.go`, `ctr.go`, `gcm.go`: embedded block
  dispatch, stride and IV allocation, CBC chaining/in-place handling, CTR refill
  and full-width counter carry, GCM nonce derivation/inc32/tag construction,
  constant-time tag comparison before returning plaintext. Three concrete API
  defects are listed below; source review does not classify these files as bug-free.
  CTR's finalizer/reset does not establish complete key/state erasure.
- `x/crypto/blake2b/blake2b.go`, `blake2b_generic.go`, `blake2b_ref.go`: digest/key
  bounds, final-block buffering, counter carry/borrow, twelve compression rounds,
  reset/clone-by-value Sum behavior and arm64 generic implementation selection.
  Serialized state accepts invalid internal sizes/offsets as described below.
- `x/crypto/blake2b/blake2x.go`, `register.go`: fixed/unknown-length XOF limits,
  per-node configuration and counter, partial reads, EOF, Reset/Clone and
  write-after-read rejection; registration of the three fixed hash sizes.
  AEZ does not call XOF, serialization or registry APIs. Upstream BLAKE2b tests
  exercise these implementations separately from Oath's fixed 48-byte hash usage.

## Concrete dependency hazards, not repaired

1. **DEP-AEZEED-001 — CBC silently accepts a partial final block.**
   `internal/modes/cbc.go:51-58` divides by 16 without first rejecting a remainder.
   A 17-byte request decrypts one block and leaves the trailing byte untouched.
   Go's standard CBC implementation rejects the same input. The characterization
   test reproduces the difference; no reachable Oath CBC caller was found.
2. **DEP-AEZEED-002 — malformed BLAKE2b serialized state can panic.**
   `blake2b.go:180-201` validates the header and total length but accepts arbitrary
   digest size and buffered offset. Independently mutating either field to 255
   is accepted by UnmarshalBinary and panics on Sum. Oath's AEZ key extraction
   calls New(48,nil), Write, Sum and Reset, never UnmarshalBinary.
3. **DEP-AEZEED-003 — GCM truncates authenticated lengths to 32 bits.**
   `internal/modes/gcm.go:72,133-134,170-171` encodes bit lengths with PutUint32.
   At 512 MiB of additional data, the actual implementation produces a different
   tag from standard GCM; the standard implementation rejects that tag. This is
   reproduced with synthetic zero AAD and empty plaintext. The same source pattern
   applies to ciphertext and nonstandard nonce lengths; those large cases were
   not separately executed. Small inputs matching the reference do not refute it.

These defects remain in the pinned upstream source. They are documented limitations
of unused dependency APIs, **not verified exploitable wallet vulnerabilities and
not fixed bugs**. Changing a dependency version or extending the bridge call graph
requires re-evaluation; a passing characterization test means the hazard still exists.

## Reachability basis

The reviewed export `Tools/AezeedBridge/main.go:63` is OathAezeedDecode. It bounds
encoded input to 33 bytes, output to 19 bytes and passphrase to 4096 bytes, clears
output before use, catches panics, and copies decoded material only for status zero.
It calls LND Mnemonic.ToCipherSeed. In pinned LND `aezeed/cipherseed.go:532-539`,
AEZ Decrypt receives a fixed four-byte authentication expansion, nil nonce, a fixed
AD item and a nil destination. Failed authentication returns ErrInvalidPass.
AEZ `aez.go:45-54` uses the ordinary BLAKE2b hash interface. The arm64 round adapter
calls ct64's round/load/store functions, not NewCipher or its embedded modes.
No CBC/CTR/GCM or hash-state decoder is invoked by this traced application path.
Go 1.26.5's standard cipher package also expects a two-argument NewGCM specialization;
the dependency's old one-argument method does not satisfy that interface. Tests
invoke the old method directly so they cannot accidentally test the fallback.

This is an explicit source-call trace, not a general proof that the entire module
has no unsafe API. The selected compilation inventory contains unused functions.
Historical opaque archives and unreviewed Go runtime/standard-library code retain
separate provenance and review gaps. The four-byte AEZ authentication expansion is
an existing aezeed protocol property, not a newly introduced 128-bit tag guarantee.

## Tests and reproduction

The final harness runs the real pinned dependencies under Go 1.26.5's race detector:

```sh
python3 scripts/aezeed-primitives.py /path/to/clean/source \
  --expected-commit f7441b85d5216b702dde490eb027aece1a6cfb5a \
  --output /tmp/aezeed-dependency-evidence
```

It requires about 512 MiB for the large GCM input, plus runtime/race-detector overhead.
Thirteen named cases comprise **ten positive validation cases and three hazard
characterizations**. They cover 24,576 AES S-box/lane comparisons; 1,536 deterministic
AES samples against standard AES; a FIPS-197 known-answer example for each word
width; reset/short buffers; 514 GHASH lengths; 220 independent Python hashlib
BLAKE2b vectors with four chunk sizes and reset/repeat checks; AEZ ciphertext
mutations and wrong key/nonce/AD at lengths 0–129; CBC/CTR/GCM reference comparisons;
and the three defects above. Round trips alone are not treated as independent AEZ
cryptographic validation; existing upstream known-answer tests are run separately.

Results, fixtures, seeds and hashes are in `evidence/aezeed-dependencies`.
The initial 12-case run and separate non-race large-GCM reproduction remain intact.
Pinned upstream AEZ, BLAKE2b and GHASH suites passed with `-race -count=1`.
The ct32/ct64 packages themselves report **no test files**; the audit harness
supplies their tests. The application source was not modified for this increment,
and the unsigned Release compilation evidence remains the exact f7441b8 result
published in progress 9. No simulator, device or App Store operation was performed.

## Remaining coverage

All 28 selected third-party Go files now have a source-review or generated-data
disposition. This is one dependency subset, not the complete application audit.
Go runtime/standard-library internals, Wallet Core's remaining source/provenance,
other dependencies, application files and the final exact-source CI matrix remain
outstanding. There is no whole-wallet completion verdict.
