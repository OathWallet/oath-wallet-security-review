# Multisig recovery document and adapter review

Target: `02a6e8ab66c7629dcb9dd36637c683457e821d98`.
This increment reads the complete eleven `*MultisigRecovery.swift` documents,
`MultisigCredential.swift`, the eleven `Oath*Multisig.swift` wallet adapters and
`OathMultisigCreation.swift`. Their individual hashes and dispositions are in
`review/dispositions.json` and `scope/inventory.json`. Source review of these
files does not mark their crypto dependencies, setup UI or chain services reviewed.
The Bitcoin and EVM package backup-test files were also read in full; the other
test files were executed without automatically changing their review status.

## Document boundaries

The format/version/type wrapper rejects unknown formats, versions and material
types. Both decode and encode require structural validity. Signer order is
preserved in the serialized material and presentation projections; display
ordering does not rewrite recovery keys. Non-signer bootstrap, executor and
creation material remains inside the credential rather than public metadata.

Each chain document restricts its version, threshold, signer count and credential
shape. Private-key and phrase forms are mutually exclusive. Phrase/language
lengths are bounded, and passphrases must pass the shared NFKD/byte/NUL checks.
EVM networks are allow-listed; addresses and identity lengths have chain-specific
shape rules. Bitcoin's version binds its Bitcoin/Litecoin/Bitcoin Cash/Dogecoin
policy and derivation path. These are deliberately **shape checks**, not proof
that arbitrary address bytes or key scalars are valid.

Ten non-Bitcoin documents reject duplicate recorded identities. Bitcoin's
document cannot compare a WIF with the first derived child of a mnemonic; its
adapter builds the descriptor through `BitcoinMultisig.wallet`. The inspected
`validatedRoots` boundary validates each WIF/seed, derives the actual first leaf,
rejects duplicate leaves and calls descriptor sanity checks. A shape-valid
Bitcoin duplicate must not be described as a cryptographically valid policy.
`hasSameMaterial` is order-insensitive comparison for validated signer sets,
not an input validator. Malformed unvalidated duplicates do not meet that contract.

## Application adapter boundaries

Each adapter first checks structure, then derives the signer identity from its
key or verified BIP39 phrase and compares it with the recorded address/public key.
The fixed per-chain derivation paths are explicit. Policy construction checks
the aggregate account identity; TRON, XRP and Stellar also bind the bootstrap
key to the original account. Solana/NEAR/EVM retain the seed/salt material needed
to reconstruct their deterministic account addresses. Imported NEAR 64-byte keys
verify the trailing public key, and Sui's Bech32 import requires the supported
scheme byte. Bitcoin validates the full WIF and resulting descriptor.

The app's restoration dispatch invokes these material checks before committing
the restored secret. This is source call-path evidence, not a live network test.
The EVM and TRON factory helpers that accept a supplied passphrase rely on the
setup caller to normalize it; the inspected calls in `OathMultisigSetup.swift`
do normalize it before invocation, and restore/signing paths normalize again.
No supported-flow normalization defect was established by that observation.

Export text preserves signer material and explicitly quotes passphrase whitespace
or uses JSON. These methods do not authorize export themselves: callers must
retain the separately reviewed wallet-scoped authorization boundary. The
adapters' `resetBytes` calls reduce one local copy's lifetime; Swift copy-on-write
semantics do not establish erasure of every alias. No such erasure guarantee is
claimed, nor is a chain's live permission state inferred from local recovery data.

## Tests and their limits

The current-source OathCloudBackup host suite passed **58 XCTest cases and one
Swift Testing case**, with zero skips. Its encrypted round trips, wrong-password,
tampering/version, bounded-file, cancellation and reset cases retain their own
logs. There was no live iCloud or phone validation.

The new `tests/MultisigRecoveryBoundary.swift` executable imports the actual
OathCloudBackup package through a generated local SwiftPM harness. All **197
checks across eleven recovery families** passed: shape round trips, exact signer
order/material preservation, outer/inner versions, unknown format/type, invalid
thresholds/count, ambiguous key/phrase forms, phrase/passphrase size and NUL
boundaries, and duplicate public identities where the format provides them.
These intentionally fake addresses are serialization fixtures, not valid funded
wallets. This corpus does not test identity derivation, signing or broadcasting.

```sh
python3 scripts/multisig-recovery.py /path/to/oath-wallet \
  --commit 02a6e8ab66c7629dcb9dd36637c683457e821d98 \
  --output /tmp/oath-multisig-recovery-evidence
python3 scripts/run.py /path/to/oath-wallet OathCloudBackup \
  --output /tmp/oath-cloud-suite-evidence
```

No confirmed application vulnerability or application code patch resulted from
this source batch. Transitive cryptography, policy implementations, setup UI,
on-chain permissions and wider lifetime handling retain their own outstanding
review status. Passing these checks is not completion of the wallet audit.
