# Dependency evidence and limitations

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
Seed vectors matched. The original binaries remain unchanged, and equivalence
is unresolved; see OW-2026-002.

OSV Scanner 2.7.0 reports advisories against the pinned `golang.org/x/crypto`
and `golang.org/x/sys` modules. Govulncheck 1.9.0, Go 1.26.5, source mode,
reported module/package-level advisories but **no reachable vulnerable symbol**
for the bridge and public fixture commands in the local run. This does not make
the entire modules safe, prove all platform paths, or cover the historical binary.
The raw OSV and Govulncheck records are retained. CI intentionally retains the
nonzero OSV result rather than hiding it through an ignore list. Future database
updates may change the result. Standard-library advisories are also in the raw
Govulncheck record. Full dependency triage remains outstanding.
