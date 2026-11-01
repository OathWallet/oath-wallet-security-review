import Foundation
import XCTest
@testable import OathAnkr

final class TronAuditProductionTests: XCTestCase {
    let key = Data(repeating: 7, count: 32)
    let instant = Date(timeIntervalSince1970: 1_791_940_458)

    func plan(_ reference: String = "native") throws -> TronSendPlan {
        let limit: UInt64 = TronIdentity.isAddress(reference) ? 10_000_000 : 0
        return try .init(network: .nile, sender: TronSendCrypto.address(privateKey: key),
            recipient: TronSendCrypto.address(privateKey: Data(repeating: 8, count: 32)),
            reference: reference, amount: "1234567", requestedAmount: "1234567",
            assetBalance: reference == "native" ? "1000000000" : "10000000", decimals: 6,
            nativeBalance: 1_000_000_000, fee: limit + 1_000_000, estimatedFee: limit,
            feeLimit: limit, energyPrice: 100, bandwidthPrice: 1000,
            blockID: "000000000447a0b3d5803edfbd5d08666d00b12161a4312777b38cb9a217d8d6",
            blockNumber: 71_803_059, timestamp: 1_791_940_458_000,
            expiration: 1_791_940_638_000, createdAt: instant)
    }

    func changed(_ plan: TronSendPlan, _ fields: [String: Any]) throws -> TronSendPlan {
        var object = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(plan)) as? [String: Any])
        for (name, value) in fields { object[name] = value }
        return try JSONDecoder().decode(TronSendPlan.self, from: JSONSerialization.data(withJSONObject: object))
    }

    func testIndependentIntegerVectors() throws {
        struct Vector: Decodable { let decimal: String; let hex: String }
        let url = try XCTUnwrap(Bundle.module.url(forResource: "amounts", withExtension: "json"))
        let vectors = try JSONDecoder().decode([Vector].self, from: Data(contentsOf: url))
        XCTAssertEqual(vectors.count, 1006)
        for vector in vectors {
            XCTAssertEqual(try TronSendCrypto.uint256(vector.decimal), try TronIdentity.hex(vector.hex))
        }
        for invalid in ["", "-1", "+1", " 1", "1 ", "1e3", "1.0", "١", String(repeating: "9", count: 79),
                        "115792089237316195423570985008687907853269984665640564039457584007913129639936"] {
            XCTAssertThrowsError(try TronSendCrypto.uint256(invalid))
        }
    }

    func testTronWebKnownAnswers() throws {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "sdk-vector", withExtension: "json"))
        let vector = try JSONDecoder().decode(TronJSON.self, from: Data(contentsOf: url))
        let rows = try XCTUnwrap(vector["vectors"].array)
        XCTAssertEqual(rows.count, 3)
        for row in rows {
            let p = try plan(XCTUnwrap(row["reference"].string))
            let signed = try TronSendCrypto.sign(p, privateKey: key, now: instant)
            XCTAssertEqual(TronSendCrypto.hex(try TronSendCrypto.raw(p)), row["raw"].string)
            XCTAssertEqual(signed.hash, row["hash"].string)
            XCTAssertEqual(TronSendCrypto.hex(signed.signature), row["signature"].string?.lowercased())
            XCTAssertEqual(TronSendCrypto.hex(signed.bytes), row["bytes"].string)
        }
    }

    func testConsensusFieldMutationsRejectOriginalSignature() throws {
        for reference in ["native", "1005416", "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"] {
            let p = try plan(reference)
            let signed = try TronSendCrypto.sign(p, privateKey: key, now: instant)
            let third = try TronSendCrypto.address(privateKey: Data(repeating: 9, count: 32))
            var changes: [[String: Any]] = [
                ["recipient": third], ["sender": third], ["amount": "1234566"],
                ["timestamp": p.timestamp + 1], ["expiration": p.expiration - 1],
                ["blockID": "000000000447a0b3e5803edfbd5d08666d00b12161a4312777b38cb9a217d8d6"]
            ]
            if p.isContract { changes += [["feeLimit": p.feeLimit + 1], ["reference": third]] }
            if reference == "1005416" { changes += [["reference": "1005417"]] }
            for fields in changes {
                let mutated = try changed(p, fields)
                // Ensure the failure is signature binding, not a malformed-plan guard.
                try mutated.validate(now: instant)
                XCTAssertNotEqual(try TronSendCrypto.raw(mutated), try TronSendCrypto.raw(p))
                XCTAssertThrowsError(try TronSendCrypto.verify(signed, plan: mutated))
            }
        }
    }

    func testEverySignedByteAndSignatureMutationRejected() throws {
        for reference in ["native", "1005416", "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"] {
            let p = try plan(reference), s = try TronSendCrypto.sign(p, privateKey: key, now: instant)
            for index in s.bytes.indices {
                var bytes = s.bytes; bytes[index] ^= 1
                XCTAssertThrowsError(try TronSendCrypto.verify(.init(bytes: bytes, signature: s.signature, hash: s.hash), plan: p))
            }
            for index in s.signature.indices {
                var signature = s.signature; signature[index] ^= 1
                // Re-encode the mutated signature, so equality of envelope bytes
                // cannot reject it before production signer recovery runs.
                let bytes = TronSendCrypto.field(1, try TronSendCrypto.raw(p)) + TronSendCrypto.field(2, signature)
                XCTAssertThrowsError(try TronSendCrypto.verify(.init(bytes: bytes, signature: signature, hash: s.hash), plan: p))
            }
            for length in [0, 1, 64, 66] {
                let signature = Data(repeating: 0, count: length)
                let bytes = TronSendCrypto.field(1, try TronSendCrypto.raw(p)) + TronSendCrypto.field(2, signature)
                XCTAssertThrowsError(try TronSendCrypto.verify(.init(bytes: bytes, signature: signature, hash: s.hash), plan: p))
            }
            XCTAssertThrowsError(try TronSendCrypto.verify(.init(bytes: s.bytes, signature: s.signature, hash: String(repeating: "0", count: 64)), plan: p))
            XCTAssertThrowsError(try TronSendCrypto.verify(.init(bytes: s.bytes, signature: s.signature, hash: s.hash, additionalSignatures: [s.signature]), plan: p))
        }
    }

    func testPlanBoundsAndExpiry() throws {
        let p = try plan()
        for fields: [String: Any] in [
            ["amount": "0"], ["amount": "01234567"], ["amount": "1234568"],
            ["fee": TronSendPlan.maximumFee + 1], ["estimatedFee": p.fee + 1],
            ["feeLimit": 1], ["energyPrice": 0], ["bandwidthPrice": 1_000_001],
            ["blockNumber": p.blockNumber + 1], ["timestamp": 0],
            ["expiration": p.timestamp], ["expiration": p.timestamp + 180_001],
            ["decimals": 255], ["recipient": p.sender], ["sender": "bad"]
        ] {
            let mutated = try changed(p, fields)
            XCTAssertThrowsError(try mutated.validate(now: instant))
            XCTAssertThrowsError(try TronSendCrypto.sign(mutated, privateKey: key, now: instant))
        }
        for offset in [-6.0, 91.0, 180.0] {
            XCTAssertThrowsError(try TronSendCrypto.sign(p, privateKey: key, now: instant.addingTimeInterval(offset)))
        }
        for offset in [-5.0, 0.0, 90.0] { try p.validate(now: instant.addingTimeInterval(offset)) }
    }

    func testReservationMetadataDoesNotChangeSignedExecutionLimit() throws {
        let p = try plan("TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf")
        let covered = try changed(p, ["nativeBalance": 0, "fee": 0, "estimatedFee": 0])
        try covered.validate(now: instant)
        XCTAssertGreaterThan(covered.feeLimit, covered.fee)
        XCTAssertEqual(try TronSendCrypto.raw(covered), try TronSendCrypto.raw(p))
        let signed = try TronSendCrypto.sign(covered, privateKey: key, now: instant)
        try TronSendCrypto.verify(signed, plan: p)
        // Resource availability is provider-supplied metadata, not a signed cap.
        // This control does not assert a future on-chain fee of zero.
    }
}
