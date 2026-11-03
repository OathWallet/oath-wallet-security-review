# Aptos, Near, Sui and THORChain wallet-adapter source trace

Source read at `0614556b993f85808b13e3a69984ce36050a8dfe`. All four wallet-adapter
files and their multisignature adapters are byte-identical at the build-104
baseline `0b1b4aeabf01d03bc417f00d4eb022a5bb0c049d` and merge
`501915920e99475e63af5fcb9e658f3c834f3cc8`. The accompanying source-binding file
records these comparisons. This read gives the four previously outstanding
wallet wrappers **partial**, not complete, dispositions.

## Reviewed paths

Each of the four `Oath*Wallet.swift` files was read in full. The corresponding
`Oath*Multisig.swift` adapters were reread to follow the called signer/policy
validation; their existing dispositions and historical evidence are preserved.

- Aptos binds account wallet/network and normalized sender, imported-key chain
  and path, or verified BIP39 material before derivation. Public-key lookup
  checks the derived address. Multisignature send requires the stored policy
  and special derivation path, validates signer material and selects the
  canonical threshold keys. The called signer validates the plan and public key.
- Near binds the wallet/network and imported-key chain/path. Implicit addresses
  must match the derived key. Named accounts deliberately use a public key
  rather than derive the account name; their on-chain access-key proof remains
  a separate provider/plan review obligation. Multisignature policy construction
  validates nonempty keys before the wrapper indexes its first key. Transfer
  stages use threshold member keys; deployment/security stages use the stored
  bootstrap seed. Connect requests reject these multisignature accounts and
  require the account name to match the selected account.
- Sui checks wallet/network and normalized sender before ordinary or
  multisignature signing. The ordinary signer validates the plan and derived
  address. Multisignature signing requires the matching stored policy and
  canonical threshold keys. Connect key lookup rejects multisignature wallets
  and proves the key-derived address matches the selected account.
- THORChain ordinary and Connect paths reject multisignature secrets, restrict
  imported key chain/path, and bind the sender to the account. Its multisignature
  path requires mainnet, matching policy/address/wallet/network/path and selects
  signers in the policy's address-based key order. Each selected private key is
  checked against its recorded public key before signing.

All four wrappers arrange cleanup of temporary key Data. This does not prove
complete memory erasure: Swift copy-on-write values, crypto-library copies and
process memory were not instrumented. Mnemonic derivation calls Wallet Core;
the imported-key host harness does not exercise that binary path.

## Supporting evidence and limits

The final removal-fix regression run includes nine ordinary-send authorization
assertions for each of these four chains. Those tests use the production vault,
PIN and imported-key signer with synthetic credential stores. They do not test
all the multisignature/HD/Connect branches described above. See the
[exact receipts](../evidence/5.0.2-build104/connect-removal-read/validation/manifest.json).

Downstream source tracing followed Aptos and Near sign/verify and policy
validation, Sui sign/verify and bounded multisignature decoding, and THORChain
signer-policy selection. Their full parsing, serialization, provider, replay,
fee and upstream crypto implementations are not closed by this wrapper review.
Independent transaction vectors, named-account authorization proofs, full HD
integration and malformed persistence boundaries remain separate obligations.
No new defect is confirmed by these source reads alone. No simulator, device,
network provider or transaction broadcast was used.

[Source binding and coverage](../evidence/5.0.2-build104/chain-wallet-adapters/source-binding.json).
