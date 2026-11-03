import XCTest
import CryptoKit
@testable import OathAnkr

final class SuiAuditSigningBoundaryTests: XCTestCase {
    let key = Data(repeating: 7, count: 32) // Public synthetic fixture only.
    let now = Date(timeIntervalSince1970: 1_700_000_000)
    struct Vector: Decodable { let input: String; let length: Int; let hash: String; let base58: String? }
    func plan(policy: SuiMultisigPolicy? = nil) throws -> SuiSendPlan {
        let funds = SuiSendFunds(coins: [], addressBalance: 1_000_000_000)
        return try .make(network: .mainnet, sender: policy?.address ?? SuiSendCrypto.address(privateKey: key),
            recipient: "0xabc", reference: "native", amount: 1_000_000, native: funds, asset: funds,
            gasPrice: 1000, gasBudget: 5_000_000, estimatedFee: 1_000_000, epoch: 1252, nonce: 42, now: now, multisig: policy)
    }
    func testIndependentBlake2bAndBase58Vectors() throws {
        let path = try XCTUnwrap(ProcessInfo.processInfo.environment["OATH_SUI_AUDIT_VECTORS"])
        let vectors = try JSONDecoder().decode([Vector].self, from: Data(contentsOf: URL(fileURLWithPath: path)))
        XCTAssertEqual(vectors.count, 336)
        for (i, vector) in vectors.enumerated() {
            let input = try XCTUnwrap(Data(base64Encoded: vector.input))
            XCTAssertEqual(SuiSendCrypto.hash(input, length: vector.length).map { String(format: "%02x", $0) }.joined(), vector.hash, "vector \(i)")
            if let expected = vector.base58 {
                XCTAssertEqual(SuiSendCrypto.base58(input), expected, "base58 \(i)")
                XCTAssertEqual(try SuiSendCrypto.unbase58(expected), input)
            }
            let sliced = (Data([0xaa, 0xbb]) + input).dropFirst(2)
            XCTAssertEqual(SuiSendCrypto.hash(sliced, length: vector.length), SuiSendCrypto.hash(input, length: vector.length))
        }
    }
    func testSingleSignatureByteMutationsAndIntentSeparation() throws {
        let p = try plan(), signed = try SuiSendCrypto.sign(p, privateKey: key, now: now)
        XCTAssertNoThrow(try SuiSendCrypto.verify(signed, sender: p.sender))
        for i in signed.signature.indices {
            var signature = signed.signature; signature[i] ^= 1
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: signature, digest: signed.digest), sender: p.sender))
        }
        for i in signed.bytes.indices {
            var bytes = signed.bytes; bytes[i] ^= 1
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: bytes, signature: signed.signature, digest: SuiSendCrypto.digest(bytes)), sender: p.sender))
        }
        let signer = try Curve25519.Signing.PrivateKey(rawRepresentation: key)
        for message in [signed.bytes, SuiSendCrypto.hash(signed.bytes), SuiSendCrypto.hash(Data([3,0,0]) + signed.bytes)] {
            let signature = try Data([0]) + signer.signature(for: message) + signer.publicKey.rawRepresentation
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: signature, digest: signed.digest), sender: p.sender))
        }
    }
    func testSignatureTruncationsTrailingBytesAndSlices() throws {
        let p = try plan(), signed = try SuiSendCrypto.sign(p, privateKey: key, now: now)
        for n in 0..<signed.signature.count {
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: Data(signed.signature.prefix(n)), digest: signed.digest), sender: p.sender))
        }
        XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: signed.signature + Data([0]), digest: signed.digest), sender: p.sender))
        let bytes = (Data([0,1]) + signed.bytes).dropFirst(2)
        let signature = (Data([0,1]) + signed.signature).dropFirst(2)
        XCTAssertNoThrow(try SuiSendCrypto.verify(.init(bytes: bytes, signature: signature, digest: signed.digest), sender: p.sender))
    }
    func testMultisigEnvelopeMutationsAndSignerMembership() throws {
        let keys = [7,8,9].map { Data(repeating: UInt8($0), count: 32) }
        let policy = try SuiMultisigPolicy(required: 2, publicKeys: keys.map { try SuiSendCrypto.publicKey(privateKey: $0) })
        let p = try plan(policy: policy), signed = try SuiSendCrypto.sign(p, privateKeys: Array(keys.prefix(2)), now: now)
        XCTAssertNoThrow(try SuiSendCrypto.verify(signed, sender: p.sender))
        for i in signed.signature.indices {
            var signature = signed.signature; signature[i] ^= 1
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: signature, digest: signed.digest), sender: p.sender), "byte \(i)")
        }
        for n in 0..<signed.signature.count {
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: Data(signed.signature.prefix(n)), digest: signed.digest), sender: p.sender))
        }
        XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: signed.signature + Data([0]), digest: signed.digest), sender: p.sender))
        for invalid in [[keys[0]], [keys[0],keys[0]], [keys[0],Data(repeating: 10,count: 32)], keys] {
            XCTAssertThrowsError(try SuiSendCrypto.sign(p, privateKeys: invalid, now: now))
        }
    }
    func testDecodedInvalidPlansFailBeforeSerializationAndSigning() throws {
        let p = try plan()
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(p)) as? [String: Any])
        let edits: [(String, Any)] = [("amount",0), ("amount",2_000_000), ("requestedAmount",0),
            ("assetBalance",0), ("nativeBalance",0), ("gasBudget",0), ("gasBudget",50_000_001),
            ("estimatedFee",5_000_001), ("gasPrice",0), ("epoch",NSNumber(value:UInt64.max)),
            ("withdrawal",0), ("sender","0x1"), ("recipient","invalid"), ("reference","0x2::sui::SUI")]
        for (field, value) in edits {
            var changed = json; changed[field] = value
            let decoded = try JSONDecoder().decode(SuiSendPlan.self, from: JSONSerialization.data(withJSONObject: changed))
            XCTAssertThrowsError(try decoded.validate(now: now), field)
            XCTAssertThrowsError(try decoded.transactionBytes(), field)
            XCTAssertThrowsError(try SuiSendCrypto.sign(decoded, privateKey: key, now: now), field)
        }
    }
    func testAgeAndMaximumEpochBoundaries() throws {
        let p = try plan()
        for delta in [-5.0, 0, 120] { XCTAssertNoThrow(try p.validate(now: now.addingTimeInterval(delta))) }
        for delta in [-5.001,120.001] { XCTAssertThrowsError(try SuiSendCrypto.sign(p, privateKey: key, now: now.addingTimeInterval(delta))) }
        var json = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(p)) as? [String: Any])
        json["epoch"] = NSNumber(value: UInt64.max - 1)
        let boundary = try JSONDecoder().decode(SuiSendPlan.self, from: JSONSerialization.data(withJSONObject: json))
        XCTAssertNoThrow(try boundary.transactionBytes())
        XCTAssertNoThrow(try SuiSendCrypto.sign(boundary, privateKey: key, now: now))
    }
}
