# How the recovery importer resolves typed and scanned input

> Current audit target: [5.0.2 (104) prerelease](RELEASE-5.0.2-104.md). Earlier results below retain their original tested versions and commits; they are not retroactively tests of build 104.

A BIP39 checksum, an Electrum version prefix and an aezeed envelope identify different properties of the same text. A version prefix alone can match a public payment address or the text of a URL. Conversely, one valid aezeed can also have a valid BIP39 checksum. Running a detector without preserving what the user intended can select a different wallet.

The paired runner builds the production draft, validator and Bitcoin/aezeed packages at three source revisions. Each before/after pair uses a byte-identical Swift probe, starts each case in a separate network-denied host process, and checks the exact exit status and named result. It requires nine specific failures before and eleven successes after. Two controls cover ordinary BIP39, Electrum, aezeed and legacy hexadecimal input. The existing import suite additionally checks ten dictionaries, 260 vectors and all five supported BIP39 word counts. [Reproduction script](../scripts/recovery-routing.py) · [Paired outcomes](../evidence/recovery-routing/oath53-evidence/paired/recovery-routing.json).

## Rejected input and QR recognition

The old editor kept the previous text when it rejected an oversized paste. The plain BIP39 submission code checked rejection and marked-text composition. The two alternate decoder branches could still recognize that previous text. The new candidate set is empty after a rejected edit and during keyboard composition. The import button also checks the rejection state. Replacing the text clears a format choice made for a different phrase.

We generated a synthetic URL using the reserved example.invalid domain, a JSON document and a valid Bitcoin address. Their normalized text happens to match the Electrum standard version prefix. The dedicated recovery scanner previously accepted all three. The new QR-specific rule accepts mnemonic-shaped modern text and preserves the legacy word and raw-hex encodings. After that first correction, we reproduced the same three public inputs through manual paste. The importer now leaves the format unselected for these inputs. A user restoring an unusual historical Electrum wallet may deliberately select Electrum. A valid phrase supplied by another person can still be imported; these checks cannot determine who generated it.

## Two genuine wallets from one fixture

The public test generator asks the pinned LND library to construct a deterministic seed with synthetic entropy and salt. LND encodes it, decodes it back and returns its original entropy. The same 24 dictionary indices also pass BIP39. The fixture independently computes a first Bitcoin receive address from each seed using btcsuite. They differ. The old selection rule suppressed the format picker whenever aezeed recognition succeeded, and the final wallet import boundary always rejected those words on the BIP39 branch.

The picker now lists applicable formats, keeps the existing default, and carries a deliberate BIP39 selection to the engine. That branch still revalidates the mnemonic and language. An untyped aezeed overlap still fails the engine's BIP39 import guard. The integration test exercises both choices with the same words, compares receive addresses independently, and reopens the encrypted wallet envelope to check both stored identities. [LND and btcsuite fixture generator](../fixtures/recovery-routing/dual.go) · [App integration checks](https://github.com/devdasx/oath-wallet/blob/343046575c980b9091a4474f098878e920963492/Tools/CheckAezeedImport.swift).

A second synthetic LND seed, iteration 50,579, also passes BIP39 checksum and Electrum version recognition. The independent generator derives three distinct addresses. The app test checks all three routing options and two native receive derivations. [Three-format regression](../fixtures/recovery-routing/ThreeFormats.swift).

The first encrypted-storage test compared a synthetic host display address to the independent Bitcoin address and failed. The corrected test exercises the production descriptor method and reads the wallet's receive address from its database. The host uses CommonCrypto for BIP39 seed derivation. Generic iOS compilation and host verification have separate results.

## What was verified

The word-list comparison checks each entire file against the Bitcoin BIPs revision named in Oath's manifest. It separately checks the app's Git source and the same file in the unsigned iOS Release bundle. It checks order, uniqueness, entry count and NFKD encoding, and binds the bundle to its executable hash. The word lists are security-relevant data; changing their order can map a phrase to different entropy. This verification does not substitute for review of key derivation or of any user's backup. [Dictionary verifier](../scripts/bip39-dictionaries.py).

Electrum's legacy list has 1,626 entries and uses a different algorithm. We compare its complete order with the literal tuple in Electrum 4.6.2, then verify that the packaged resource is byte-identical to the app source. [Upstream tuple](https://github.com/spesmilo/electrum/blob/a8b86f2c725ffad4e52d7fa5912906be914f1999/electrum/old_mnemonic.py#L34-L1661) · [Reproduction](../scripts/electrum-dictionary.py).

The 709-second full iOS build passed. Xcode omitted the cached manifest identifier from its log. A second unsigned build at the same clean commit emitted the manifest identifier. Only that second log was used for compiler-input attribution. [Original build result](../evidence/recovery-routing/oath53-evidence/history/full-build/build.json).
