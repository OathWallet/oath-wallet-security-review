# XRP request boundaries and codec provenance

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Tested public application commit:
`8a31eb265c34ef7f37ba21741201842366d43b7b`. The files described below have
identical bytes at baseline `c7acd23bb139864a40273f405d18b479589d2b20`.
This is additional review evidence, not a whole-wallet completion verdict.

## Shipped JavaScript reproduction

The 409,981-byte bundled `XrplCodec.js` rebuilds byte-for-byte from the checked-in
entry point and lockfile using Node 26.5.0, npm 11.17.0 and esbuild 0.25.12.
The bundle SHA256 is
`77cb450cf20bbd0ec5b2a0c425244bd0607fc18b6ecf9ecc01ea26aadd52681b`.
The initial cached-package experiment and the fresh locked installation both
match. The formal build denies network access after installation; npm lifecycle
scripts are disabled. This proves the tested source-to-bundle relationship,
not the correctness of all dependency code or App Store binary equivalence.

The bundler reports 171 contributing input files: the application entry point
plus 170 upstream files from 11 packages. Their names, versions, licenses,
registry locations, integrity values, source hashes and contributed byte counts
are recorded in the [provenance receipt](../evidence/5.0.1-build103/xrpl-codec/provenance-final/result.json).
All 170 upstream implementation files are explicitly **outstanding** in the
[new dependency ledger](../scope/upstream-xrpl-codec.json). Their absence from
the previous upstream inventories was a scope gap. A successful rebuild does
not promote them to manually reviewed.

A point-in-time `npm audit --omit=dev` query returned no known advisories for the
locked production dependency tree. Its raw response is retained. It does not
cover unreported vulnerabilities, prove semantic correctness or replace review.

## Read scope and remaining uncertainty

- `WalletConnectXrpl.swift`: all 155 lines read. Traced request field/owner/network
  checks, multisign defaults, approval binding, 120-second signing age, exact
  payload/signature verification and the confined JavaScriptCore call. It remains
  partially reviewed: synthesized Codable restoration and every transaction
  type/upstream implementation still require separate coverage.
- `Tools/WalletConnectXrplCodec/index.js`: all 34 lines read. Input goes through
  transaction validation and encode/decode preservation checks; existing
  multisignatures are verified and duplicates rejected. The returned bytes and
  signing payload are used by Swift. The entry point receives public transaction
  fields, not the private key. Its upstream calls remain open review work.
- `WalletConnectXrplJournal.swift`: all 89 lines read. Traced persisted-plan and
  signature checks, account/wallet ownership, owner reservation, terminal-state
  handling and reset-trigger definitions. This checkpoint did **not** execute its
  database tests or establish complete concurrent/reset recovery behavior.
- `WalletConnectJSON.swift`: all source read again, including duplicate decoded
  keys, depth/node/collection/byte bounds and Foundation string decoding. Its
  earlier reviewed disposition is preserved; these XRP tests add limited
  integration evidence rather than a new parser-completeness claim.

## Six actual-package methods

The initial experiment and the isolated clean-checkout replay both pass:

1. Duplicate keys, escaped duplicate keys, invalid UTF-8 and byte/depth limits.
2. Unsupported method/chain, mismatched account, forbidden authority/signature
   fields and wrong JSON types for flags.
3. Altered approved payment/fee/sequence/tag/expiry fields, invalid ledger
   boundaries, and signing at age 0/120 seconds versus just outside that window.
4. Modified signed bytes, hash, signature and public key, with a valid control.
5. Three sequential multisigners, binary-account ordering and rejection after
   changing a previously signed amount.
6. Invalid destination-tag types/ranges, an unrecognized nested memo field and
   valid zero/UInt32-max tag round trips.

These methods invoke the real Swift request/review/sign/verify functions and
bundled JavaScriptCore codec with deterministic public fixture keys. Each formal
test process has network access denied. No production provider, simulator,
physical device or funded transaction is used. No new application defect was
confirmed by this bounded matrix. It does not cover every transaction family,
malicious ledger behavior, OS authorization or the full UI.

## Reproduce

From this audit repository, with a clean application checkout at the exact
tested commit:

```sh
python3 scripts/xrpl-codec-provenance.py wallet scratch/codec evidence/local/codec
python3 scripts/xrpl-connect-boundaries.py wallet scratch/boundaries evidence/local/boundaries
```

The first command pins Node/npm/esbuild, installs the lock with scripts disabled,
rebuilds and compares the bundle, and inventories contributing files. The second
creates an isolated source copy, adds only the audit test file, compiles the real
package and runs six explicitly named methods in separate processes. Missing or
failing methods do not count as a pass. Original application source must remain
clean at the same commit before and after execution.

[Evidence manifest](../evidence/5.0.1-build103/xrpl-codec/manifest.json).
No application source changed. The unsigned generic iOS Release build from
checkpoint 17 covers this unchanged application commit and was not rerun for
these audit-only additions. Hosted replay status is reported separately.
