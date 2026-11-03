# Follow-up: HDWallet seed-size constructor reachability

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

Application: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
Upstream source: Wallet Core 4.8.4,
`d40d24a63d92619167903369308bf0e2f7eb3a59`.

This is a source review follow-up after progress 12, not an additional runtime
or sanitizer result. [Reference inventory](../evidence/constructor-reachability/source-references.json)
retains every matched app call site and the upstream boundary hashes.

## Observations

`HDWallet<seedSize>::updateSeedAndEntropy` supplies `seed.data()` to
`mnemonic_to_seed`, which writes 64 bytes. Instantiating a mnemonic constructor
with `seedSize == 32` is therefore suspicious. The upstream file explicitly
instantiates both 32- and 64-byte classes, so the 32-byte API exists at source level.
That alone does not establish Oath calls it or that an attacker can reach it.

The C wrapper's `TWHDWallet` contains `TW::HDWallet<>`, whose default template
parameter is 64. All four exported creation wrappers construct that type and
catch C++ exceptions. The mnemonic, entropy and strength constructors used by
those wrappers therefore have a 64-byte output buffer. The source inventory
finds 48 HDWallet construction references across OathApp, OathAtmosphere and
Packages. None directly calls an ImmutableX, StarkKey, raw-seed or alternate
TWHDWallet constructor.

The entire upstream `src` search finds two explicit `HDWallet<32>` references:
the template instantiation and `ImmutableX::getPrivateKeyFromSeed`. The latter
calls `bip32DeriveRawSeed`, which constructs the raw-Data overload. That overload
requires exactly `seedSize` bytes and copies exactly that many; it does not call
the mnemonic expansion function. The C wrapper cannot select the 32-byte class
through its strength or mnemonic arguments.

## Disposition and remaining work

No reachable Oath overflow was established. The inspected source call path uses
64-byte mnemonic storage; the only explicit 32-byte upstream caller uses the
size-checked raw-seed overload. This narrows WC-LEAD-002 but does not claim an
exhaustive dynamic call graph or prove distributed framework/source equivalence.
No unsupported application patch was made. Direct misuse of the C++ 32-byte
mnemonic constructor remains an upstream API lead requiring a faithful sanitizer
reproduction before it is promoted to a confirmed finding.

The full HDWallet file was additionally read for ownership: its destructor wipes
seed, mnemonic and passphrase but not entropy; several raw node/Data temporaries
also lack explicit erasure. These observations stay in WC-LEAD-003. Their actual
lifetime, allocator behavior, Swift copies and attacker accessibility remain
unproven. They are not evidence of remote secret exposure. PrivateKey signing
implementations and transitive cryptography are not marked reviewed by this note.
