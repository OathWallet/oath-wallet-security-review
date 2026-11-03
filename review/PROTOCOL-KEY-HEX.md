# Protocol key parsing and representation review

The immutable baseline is 5.0.1 (103), `c7acd23bb139864a40273f405d18b479589d2b20`. The final candidate is `235a730de504e47fb961c34f68f9426ffdbdfe6d`.

## Parsing, key size and repair

WalletConnect uses X25519 and HKDF for message-encryption key agreement and ChaCha20-Poly1305 for encryption. These protocol keys are separate from transaction-signing wallet keys. [Protocol specification](https://specs.walletconnect.com/2.0/specs/clients/core/crypto/crypto-keys).

The shared Data(hex:) helper coerced malformed pairs and odd-length strings into bytes. Key constructors then relied on CryptoKit's byte-count checks, which cannot detect that the input text was changed. SymmetricKey did not enforce the protocol's 32-byte key size. The new throwing decoder requires complete ASCII hex pairs and accepts only one optional leading prefix. Key constructors use that API. The older nonthrowing helper keeps its signature and returns empty data for invalid input. ContractDecoder and RPCHistory already validate their hex inputs; their valid decoding is unchanged.

The raw symmetric-key constructor and the CryptoKit wrapper now enforce size. The CryptoKit-wrapper initializer becomes throwing, as does internal shared-secret derivation. All in-repository callers propagate errors. Existing stored 32-byte keys and 64-byte agreement records retain their serialization; malformed legacy values now fail. No Keychain identity or database migration changed.

## Caller trace and limitations

OathWalletConnectService.commitProposal invokes Sign.instance.approve. ApproveEngine passes the proposal participant's publicKey string into performKeyAgreement, which reaches generateAgreementKey. Participant is a Codable String field; the inspected proposal handler validates namespaces, not key encoding. The repaired constructors reject malformed keys before derivation. Authentication and error-response paths also call those constructors.

This is a source-level route plus a runtime proof at the production KMS boundary. It is not a completed UI or network exploit demonstration. Approval, identity checks and wallet authorization remain separate boundaries. The valid-key fixture restores an agreement record from serialized bytes; it does not access the user's Keychain.

## Reproduction

[The replay script](../scripts/key-hex-boundaries.py) checks out the exact original and repaired revisions, overlays only the test fixture and host harness, and compiles the real utility and KMS modules. It hashes every source file in those modules. Each case runs in its own process with networking denied. Fifteen methods include all invalid ASCII low nibbles, odd lengths, Unicode, four key-constructor families, wrong symmetric sizes, malformed-peer agreement and valid serialization controls.

The synthetic private input is 32 bytes of 0x42 and the public input is the RFC 7748 base point. CryptoKit performs production agreement; a separate Node 26.5.0/OpenSSL generator supplies the expected HKDF result. [Reference generator](../fixtures/key-hex/reference.cjs) · [RFC 7748](https://www.rfc-editor.org/rfc/rfc7748.html). This is one fixed agreement vector, not exhaustive cryptographic verification.

## Correction to the earlier review

Several KMS files already had reviewed dispositions under the earlier source read. This malformed-hex behavior was missed there. Those notes remain preserved, and this finding adds a tested correction. A reviewed label records performed work, not freedom from defects. Data+utils remains partial because its randomness and base64url callers need additional review. ApproveEngine is partial for the traced proposal/approval route; its remaining lifecycle paths are not promoted by these tests.

The initial publication validator correctly rejected two changed source-file hashes. The unchanged matched lines were independently compared with the prior source; only the two exact hashes were renewed. The first failed check and renewal receipt remain in the evidence.
