import XCTest
import CryptoKit
@testable import OathAnkr

// Public disposable seed, never a funded or user wallet.
final class MessageDomainReviewTests: XCTestCase {
    let key = Data(repeating: 1, count: 32)
    struct SolanaVectors: Decodable {
        struct Vector: Decodable { let name, account, unsigned, signed: String }
        let vectors: [Vector]
    }
    struct TonVectors: Decodable {
        struct SignedData: Decodable { let payload: TonJSON; let digest, signature: String }
        struct Proof: Decodable { let payload, digest, signature: String }
        struct Transfer: Decodable { let signingHash: String }
        let sender, domain: String
        let timestamp: UInt64
        let dataVectors: [SignedData], proof: Proof, vectors: [Transfer]
    }
    func solanaVectors() throws -> [SolanaVectors.Vector] {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "solana", withExtension: "json", subdirectory: "Fixtures/WalletConnect"))
        return try JSONDecoder().decode(SolanaVectors.self, from: Data(contentsOf: url)).vectors
    }
    func tonVectors() throws -> TonVectors {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "vectors", withExtension: "json", subdirectory: "Fixtures/WalletConnectTon"))
        return try JSONDecoder().decode(TonVectors.self, from: Data(contentsOf: url))
    }
    func solana(_ bytes: Data) throws -> WalletConnectSolanaRequest {
        let account = SolanaSendCrypto.encode(try Curve25519.Signing.PrivateKey(rawRepresentation: key).publicKey.rawRepresentation)
        return try .init(method: "solana_signMessage", chain: SolanaSendNetwork.devnet.walletConnectChain, account: account,
                         params: JSONEncoder().encode(["pubkey": account, "message": SolanaSendCrypto.encode(bytes)]))
    }
    func ton(_ payload: TonJSON, domain: String? = nil, account: String? = nil) throws -> WalletConnectTonRequest {
        let v = try tonVectors()
        return try .init(method: "ton_signData", chain: "ton:-3", account: account ?? v.sender, domain: domain ?? v.domain,
                         params: JSONEncoder().encode(payload))
    }
    func publicKey() throws -> Curve25519.Signing.PublicKey {
        try Curve25519.Signing.PrivateKey(rawRepresentation: key).publicKey
    }
    func testSolanaEveryLeadingByte() throws {
        var accepted = 0, rejected = 0
        for byte in UInt8.min...UInt8.max {
            let bytes = Data([byte]) + Data("Oath challenge".utf8)
            if (32...126).contains(byte) {
                let request = try solana(bytes)
                XCTAssertEqual(request.message, bytes)
                let signature = try SolanaSendCrypto.decode(XCTUnwrap(request.sign(privateKey: key).response["signature"].string))
                XCTAssertTrue(try publicKey().isValidSignature(signature, for: bytes))
                accepted += 1
            } else {
                XCTAssertThrowsError(try solana(bytes), "lead-byte \(byte)")
                rejected += 1
            }
        }
        XCTAssertEqual(accepted, 95); XCTAssertEqual(rejected, 161)
    }
    func testSolanaTransactionMessagesCannotUsePersonalSigning() throws {
        let vectors = try solanaVectors()
        XCTAssertFalse(vectors.isEmpty)
        for v in vectors {
            let tx = try WalletConnectSolanaTransaction(bytes: XCTUnwrap(Data(base64Encoded: v.unsigned)), account: v.account)
            try tx.verifySigned(XCTUnwrap(Data(base64Encoded: v.signed)), requireAll: true)
            XCTAssertThrowsError(try solana(tx.message), v.name)
            XCTAssertThrowsError(try solana(tx.bytes), v.name)
        }
        let text = Data("Sign in to Oath\nمرحبا 🌍".utf8), request = try solana(text)
        let signed = try request.sign(privateKey: key)
        let signature = try SolanaSendCrypto.decode(XCTUnwrap(signed.response["signature"].string))
        XCTAssertTrue(signed.transactions.isEmpty)
        XCTAssertTrue(try publicKey().isValidSignature(signature, for: text))
        XCTAssertFalse(try publicKey().isValidSignature(signature, for: text + Data([0])))
        XCTAssertThrowsError(try request.sign(privateKey: Data(repeating: 2, count: 32)))
    }
    func testSolanaReadableChallengeBoundsAndControls() throws {
        for control in [0, 1, 8, 11, 13, 31, 127, 0x202e, 0x2066, 0x200b, 0xfeff] {
            let scalar = try XCTUnwrap(UnicodeScalar(control))
            XCTAssertThrowsError(try solana(Data(("hello" + String(scalar) + "world").utf8)), "control \(control)")
        }
        for text in ["hello\tworld", "hello\nworld", "مرحبا", "🌍", String(repeating: "x", count: 4096)] {
            XCTAssertEqual(try solana(Data(text.utf8)).message, Data(text.utf8))
        }
        XCTAssertThrowsError(try solana(Data()))
        XCTAssertThrowsError(try solana(Data(repeating: 120, count: 4097)))
    }
    func testTonDataBindsDomainTimeAccountAndPayload() throws {
        let v = try tonVectors(), other = try TonSendCrypto.address(publicKey: TonSendCrypto.publicKey(privateKey: Data(repeating: 2, count: 32)))
        XCTAssertEqual(v.dataVectors.count, 3)
        for vector in v.dataVectors {
            let request = try ton(vector.payload), digest = try WalletConnectTonCrypto.signDataDigest(request, timestamp: v.timestamp)
            let signature = try XCTUnwrap(Data(base64Encoded: WalletConnectTonCrypto.signData(request, privateKey: key, timestamp: v.timestamp)["signature"].string!))
            XCTAssertEqual(TronSendCrypto.hex(digest), vector.digest)
            XCTAssertTrue(try publicKey().isValidSignature(XCTUnwrap(Data(base64Encoded: vector.signature)), for: digest))
            XCTAssertTrue(try publicKey().isValidSignature(signature, for: digest))
            var fields = try XCTUnwrap(vector.payload.fields)
            switch fields["type"]?.string {
            case "text": fields["text"] = .string(try XCTUnwrap(fields["text"]?.string) + "!")
            case "binary": fields["bytes"] = .string((try XCTUnwrap(TonIdentity.base64(XCTUnwrap(fields["bytes"]?.string))) + Data([0])).base64EncodedString())
            case "cell": fields["schema"] = .string(try XCTUnwrap(fields["schema"]?.string) + " changed")
            default: return XCTFail("Unexpected reference type")
            }
            let changed = try [ton(vector.payload, domain: "evil.example"), ton(vector.payload, account: other), ton(.object(fields))]
            for r in changed {
                XCTAssertFalse(try publicKey().isValidSignature(signature, for: WalletConnectTonCrypto.signDataDigest(r, timestamp: v.timestamp)))
            }
            XCTAssertFalse(try publicKey().isValidSignature(signature, for: WalletConnectTonCrypto.signDataDigest(request, timestamp: v.timestamp + 1)))
            XCTAssertThrowsError(try WalletConnectTonCrypto.signData(request, privateKey: Data(repeating: 2, count: 32), timestamp: v.timestamp))
        }
    }
    func testTonProofBindsDomainTimeAccountAndChallenge() throws {
        let v = try tonVectors()
        func proof(_ domain: String, _ account: String, _ payload: String) throws -> WalletConnectTonProofRequest {
            try .init(chain: "ton:-3", account: account, domain: domain, payload: payload)
        }
        let p = try proof(v.domain, v.sender, v.proof.payload), digest = try WalletConnectTonCrypto.proofDigest(p, timestamp: v.timestamp)
        let signature = try WalletConnectTonCrypto.signProof(p, privateKey: key, timestamp: v.timestamp)
        XCTAssertEqual(TronSendCrypto.hex(digest), v.proof.digest)
        XCTAssertTrue(try publicKey().isValidSignature(XCTUnwrap(Data(base64Encoded: v.proof.signature)), for: digest))
        XCTAssertTrue(try publicKey().isValidSignature(signature, for: digest))
        let other = try TonSendCrypto.address(publicKey: TonSendCrypto.publicKey(privateKey: Data(repeating: 2, count: 32)))
        for changed in try [proof("evil.example", v.sender, v.proof.payload), proof(v.domain, other, v.proof.payload), proof(v.domain, v.sender, v.proof.payload + "!")] {
            XCTAssertFalse(try publicKey().isValidSignature(signature, for: WalletConnectTonCrypto.proofDigest(changed, timestamp: v.timestamp)))
        }
        XCTAssertFalse(try publicKey().isValidSignature(signature, for: WalletConnectTonCrypto.proofDigest(p, timestamp: v.timestamp + 1)))
        XCTAssertThrowsError(try WalletConnectTonCrypto.signProof(p, privateKey: Data(repeating: 2, count: 32), timestamp: v.timestamp))
    }
    func testTonTransactionHashesAreNotSignedAsDataOrProofs() throws {
        let v = try tonVectors()
        XCTAssertFalse(v.vectors.isEmpty)
        for vector in v.vectors {
            let raw = try TronIdentity.hex(vector.signingHash)
            for payload in [TonJSON.object(["type": .string("text"), "text": .string(vector.signingHash)]),
                            .object(["type": .string("binary"), "bytes": .string(raw.base64EncodedString())])] {
                let r = try ton(payload), signed = try WalletConnectTonCrypto.signData(r, privateKey: key, timestamp: v.timestamp)
                let signature = try XCTUnwrap(Data(base64Encoded: XCTUnwrap(signed["signature"].string)))
                XCTAssertTrue(try publicKey().isValidSignature(signature, for: WalletConnectTonCrypto.signDataDigest(r, timestamp: v.timestamp)))
                XCTAssertFalse(try publicKey().isValidSignature(signature, for: raw))
            }
            let p = try WalletConnectTonProofRequest(chain: "ton:-3", account: v.sender, domain: v.domain, payload: vector.signingHash)
            XCTAssertFalse(try publicKey().isValidSignature(WalletConnectTonCrypto.signProof(p, privateKey: key, timestamp: v.timestamp), for: raw))
        }
        let payload: TonJSON = .object(["type": .string("text"), "text": .string("same bytes")])
        let binary: TonJSON = .object(["type": .string("binary"), "bytes": .string(Data("same bytes".utf8).base64EncodedString())])
        XCTAssertNotEqual(try WalletConnectTonCrypto.signDataDigest(ton(payload), timestamp: v.timestamp),
                          try WalletConnectTonCrypto.signDataDigest(ton(binary), timestamp: v.timestamp))
    }
    func testTonDomainMutationControl() throws {
        let payload: TonJSON = .object(["type": .string("text"), "text": .string("Sign in")])
        let a = try ton(payload, domain: "alpha.example"), b = try ton(payload, domain: "bravo.example")
        XCTAssertNotEqual(try WalletConnectTonCrypto.signDataDigest(a, timestamp: 2_000_000_000),
                          try WalletConnectTonCrypto.signDataDigest(b, timestamp: 2_000_000_000), "Domain binding removed")
    }
}
