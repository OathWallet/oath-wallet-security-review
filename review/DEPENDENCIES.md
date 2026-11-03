# Dependency evidence and limitations

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

`scope/dependencies.json` lists Swift lockfile pins; duplicate entries preserve
which manifest declared them. `scope/licenses.json` hashes bundled notices.
`scope/binaries.json` records bundled archive/module hashes. This is an inventory,
not a legal conclusion or a claim that every transitive license was examined.
`scope/entry-points.json` is an automatically located source-review queue.

Trust Wallet Core 4.8.4 release archives have SHA-256 pins in the application
manifest. The upstream source tag resolves to
`d40d24a63d92619167903369308bf0e2f7eb3a59`. We have not reproduced those Apple
archives from source. Reown's bundled sources and additional Swift dependencies
also require reachable-code review. Swift package checksums do not close this gap.

Aezeed uses LND v0.19.3-beta through the now-published bridge. The first rebuild
with Go 1.26.5/Xcode 27.0 had equal archive sizes but different archive hashes.
Seed vectors matched. That historical attempt did not replace the binaries and
did not establish equivalence; see OW-2026-002. The later f7441b8 source repair
replaces aezeed archives with outputs that match two isolated builds using the
recorded toolchain, as documented in `AEZEED-REPRODUCIBLE-BUILD.md`. This does not
retroactively prove the original baseline archives or an App Store binary.

OSV Scanner 2.7.0 reports advisories against the pinned `golang.org/x/crypto`
and `golang.org/x/sys` modules. Govulncheck 1.9.0, Go 1.26.5, source mode,
reported module/package-level advisories but **no reachable vulnerable symbol**
for the bridge and public fixture commands in the local run. This does not make
the entire modules safe, prove all platform paths, or cover the historical binary.
The raw OSV and Govulncheck records are retained. CI intentionally retains the
nonzero OSV result rather than hiding it through an ignore list. Future database
updates may change the result. Standard-library advisories are also in the raw
Govulncheck record. Full dependency triage remains outstanding.

The subsequent selected-source inventory covers all three aezeed targets and
adds `scope/upstream-aezeed.json` to completion accounting. Forty recorded OSV
advisories are classified as **not compiled into those source targets**, based
on exact affected-package metadata and a matching pinned module graph. Raw
scanner failures remain visible. This resolves source reachability for that
snapshot only; future advisories fail triage when metadata is missing or an
affected package becomes selected. Historical archives remain unproven.

Progress 11 adds source review and sanitizer-backed tests of Wallet Core's
mnemonic, path, HMAC and PBKDF2 boundaries. See `MNEMONIC-DERIVATION-REVIEW.md`
for exact scope, the zero-round low-level API characterization, existing Oath
passphrase guards and unresolved derivation/copy-lifetime leads. These source
tests do not verify Wallet Core's distributed Apple binary equivalence.

## Inventory refreshed for the combined recovery repair

At app source `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`, the scan found 32 lock entries, 15 notices, 12 binary or module files and 1,345 candidate network/build source locations. The added exchange-rates package lock references Stellar SDK 3.12.0 at the same revision already recorded for Xcode. The number of candidates includes changed source locations and is not a count of endpoints. The review workflow regenerates and compares all four catalogs to detect further drift. [Pins](../scope/dependencies.json) · [Candidate locations](../scope/entry-points.json).
