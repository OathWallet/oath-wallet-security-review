# Offline XRP signing matrix

These fixtures use **public deterministic test wallets only**. The generator
repeats known byte values as entropy. They must never receive funds. No provider
or blockchain request is made, and no real recovery material is used.

From the audit repository, with a clean public application checkout at
`6783750661c43d3511d8973a2de77106fdf2001d`:

```sh
python3 scripts/xrpl-signing-vectors.py /path/to/oath-wallet /tmp/xrpl-scratch /tmp/xrpl-evidence
```

The runner installs the exact public application's npm lock using `npm ci
--ignore-scripts`, creates an isolated source copy, adds only this test file,
and compiles the real OathAnkr package and its dependencies. Source identity is
checked before/after; tracked production files must stay unchanged. The vector
generator and four XCTest processes run with network denied. Dependency download
and package compilation need network on a fresh machine. No credentials are
needed. The initial local run uses Xcode 27.0; npm/Node versions and lock hashes are
recorded with the evidence rather than assumed equivalent across all runtimes.

The pinned XRPL 5.3.0 SDK generates **61 transactions**: native, issued and MPT
payments; AccountDelete; SignerListSet; AccountSet master disabling; TrustSet;
and MPTokenAuthorize. Destination tags include absence, zero and UInt32.max.
Issued amounts include minimum/maximum representable positive values. Thresholds
are 1, 2, 4 and 8 out of eight signers. The tests compare complete signed bytes
and transaction hashes and verify them with the application implementation.
Node's OpenSSL-backed RIPEMD implementation supplies 13 block-boundary vectors.

Four methods also check changed signed fields, appended bytes, changed hashes,
invalid signature bytes, missing signers and duplicate signers. Not every
possible field or malformed request is enumerated. This is not live ledger
acceptance, UI approval, formal cryptographic proof, WalletConnect JavaScript
runtime coverage, side-channel analysis or the complete upstream dependency
review. Independent SDK agreement can still share specification assumptions.
