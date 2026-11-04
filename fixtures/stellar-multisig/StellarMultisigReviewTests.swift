import Foundation
import XCTest
import CryptoKit
import stellarsdk
@testable import OathAnkr

final class StellarMultisigReviewTests: XCTestCase {
    func key(_ n: Int) -> Data { Data(repeating: UInt8(n), count: 32) }
    func address(_ n: Int) throws -> String { try StellarSendCrypto.address(privateKey: key(n)) }
    func policy(_ count: Int, _ required: Int) throws -> StellarMultisigPolicy {
        try .init(account: address(99), required: required, signers: (1...count).reversed().map { try address($0) })
    }
    func plan(_ policy: StellarMultisigPolicy, configure: Bool = false) throws -> StellarSendPlan {
        .init(network: .testnet, kind: configure ? .configureMultisig : .payment,
              sender: policy.account, recipient: configure ? policy.account : try address(98), reference: "native",
              requestedAmount: configure ? "0" : "12500000", amount: configure ? "0" : "12500000",
              assetBalance: "1000000000", nativeBalance: 1000000000, reserve: 110000000,
              fee: UInt32((policy.signers.count + 1) * 100), sequence: 42, firstLedger: 1000, lastLedger: 1025,
              maxTime: 1700000120, createdAt: Date(timeIntervalSince1970: 1700000000), multisig: policy)
    }
    func json(_ value: [String: Any]) throws -> StellarJSON {
        try JSONDecoder().decode(StellarJSON.self, from: JSONSerialization.data(withJSONObject: value))
    }
    func row(_ key: String, _ weight: Int = 1, _ type: String = "ed25519_public_key") -> [String: Any] {
        ["key": key, "weight": weight, "type": type]
    }
    func state(_ p: StellarMultisigPolicy) -> [String: Any] {
        ["account_id": p.account, "thresholds": ["low_threshold": p.required, "med_threshold": p.required, "high_threshold": p.required],
         "signers": p.signers.map { row($0) } + [row(p.account, 0)]]
    }
    func testEverySupportedThresholdAndPolicyDrift() throws {
        var cases = 0
        for count in 2...20 { for required in 1...count {
            let p = try policy(count, required), valid = state(p)
            try p.validate(); XCTAssertEqual(p.signers, p.signers.sorted()); XCTAssertTrue(p.matches(try json(valid)))
            var wrong = valid; wrong["account_id"] = try address(98)
            XCTAssertFalse(p.matches(try json(wrong)))
            for level in ["low_threshold", "med_threshold", "high_threshold"] {
                wrong = valid
                var thresholds = try XCTUnwrap(wrong["thresholds"] as? [String: Int]); thresholds[level] = 0
                wrong["thresholds"] = thresholds
                XCTAssertFalse(p.matches(try json(wrong)), "lower threshold must be rejected")
                thresholds[level] = required + 1; wrong["thresholds"] = thresholds
                XCTAssertFalse(p.matches(try json(wrong)))
            }
            let active = p.signers.map { row($0) }
            for signers in [active, active + [row(p.account)], active + [row(p.account, 0), row(try address(97))],
                            Array(active.dropLast()) + [row(p.account, 0)],
                            [row(p.signers[0], 2)] + Array(active.dropFirst()) + [row(p.account, 0)],
                            [row(p.signers[0], 1, "sha256_hash")] + Array(active.dropFirst()) + [row(p.account, 0)],
                            Array(active.dropLast()) + [active[0], row(p.account, 0)]] {
                wrong = valid; wrong["signers"] = signers; XCTAssertFalse(p.matches(try json(wrong)))
            }
            cases += 1
        } }
        XCTAssertEqual(cases, 209)
    }
    func testBootstrapRequiresUntouchedMasterAndZeroThresholds() throws {
        let p = try policy(3, 2)
        let valid: [String: Any] = ["account_id": p.account, "signers": [row(p.account)],
                                   "thresholds": ["low_threshold": 0, "med_threshold": 0, "high_threshold": 0]]
        XCTAssertTrue(p.bootstrapMatches(try json(valid))); XCTAssertFalse(p.bootstrapMatches(try json(state(p))))
        for signers in [[], [row(p.account, 0)], [row(p.account, 2)], [row(p.account, 1, "sha256_hash")],
                        [row(try address(1))], [row(p.account), row(try address(1), 0)]] as [[[String: Any]]] {
            var wrong = valid; wrong["signers"] = signers; XCTAssertFalse(p.bootstrapMatches(try json(wrong)))
        }
        for level in ["low_threshold", "med_threshold", "high_threshold"] {
            var wrong = valid; var thresholds = try XCTUnwrap(wrong["thresholds"] as? [String: Int]); thresholds[level] = 1
            wrong["thresholds"] = thresholds; XCTAssertFalse(p.bootstrapMatches(try json(wrong)))
        }
        var wrong = valid; wrong["account_id"] = try address(98); XCTAssertFalse(p.bootstrapMatches(try json(wrong)))
    }
    func testDecodedInvalidPoliciesCannotReachSigning() throws {
        let p = try policy(3, 2), original = try plan(p)
        let encoded = try JSONEncoder().encode(original)
        let root = try XCTUnwrap(JSONSerialization.jsonObject(with: encoded) as? [String: Any])
        let validPolicy = try XCTUnwrap(root["multisig"] as? [String: Any])
        var invalid = [[String: Any]]()
        for required in [Int.min, -1, 0, 4, Int.max] { var v = validPolicy; v["required"] = required; invalid.append(v) }
        for signers in [[], [p.signers[0]], [p.signers[0], p.signers[0]], [p.account, p.signers[0]].sorted(),
                        Array(p.signers.reversed()), ["invalid", p.signers[0]].sorted(), (1...21).map({ try! address($0) }).sorted()] {
            var v = validPolicy; v["signers"] = signers; invalid.append(v)
        }
        var wrongAccount = validPolicy; wrongAccount["account"] = try address(98); invalid.append(wrongAccount)
        for value in invalid {
            var altered = root; altered["multisig"] = value
            let decoded = try JSONDecoder().decode(StellarSendPlan.self, from: JSONSerialization.data(withJSONObject: altered))
            XCTAssertThrowsError(try decoded.validate(checkAge: false))
            XCTAssertThrowsError(try StellarSendCrypto.sign(decoded, privateKeys: [key(1), key(2)], now: original.createdAt))
            let signed = try StellarSendCrypto.sign(original, privateKeys: [key(1), key(2)], now: original.createdAt)
            XCTAssertThrowsError(try StellarSendCrypto.verify(signed, plan: decoded))
        }
        XCTAssertEqual(invalid.count, 13)
    }
    func testEveryThresholdSignsOnlyWithRequiredDistinctKeys() throws {
        var cases = 0
        for count in 2...20 { for required in 1...count {
            let p = try plan(policy(count, required)), keys = (1...required).reversed().map { key($0) }
            let signed = try StellarSendCrypto.sign(p, privateKeys: keys, now: p.createdAt)
            try StellarSendCrypto.verify(signed, plan: p)
            let signatures = try XCTUnwrap(signed.signatures)
            XCTAssertEqual(signatures.count, required)
            XCTAssertEqual(signatures.map(\.publicKey), signatures.map(\.publicKey).sorted { $0.lexicographicallyPrecedes($1) })
            XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKeys: Array(keys.dropLast()), now: p.createdAt))
            XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKeys: keys + [key(97)], now: p.createdAt))
            XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKeys: [key(97)] + Array(keys.dropFirst()), now: p.createdAt))
            if required > 1 { XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKeys: Array(repeating: keys[0], count: required), now: p.createdAt)) }
            XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKey: key(99), now: p.createdAt))
            cases += 1
        } }
        XCTAssertEqual(cases, 209)
    }
    func testForgedSignaturesAndEnvelopeBindingsAreRejected() throws {
        let p = try plan(policy(3, 2)), signed = try StellarSendCrypto.sign(p, privateKeys: [key(1), key(2)], now: p.createdAt)
        let s = try XCTUnwrap(signed.signatures), tx = try StellarSendXDR.transaction(p)
        let badSets: [[StellarMultisigSignature]] = [[], [s[0]], [s[0], s[0]], Array(s.reversed()), s + [s[0]],
            [.init(publicKey: Data(), signature: s[0].signature), s[1]],
            [.init(publicKey: s[0].publicKey, signature: Data()), s[1]],
            [.init(publicKey: s[0].publicKey, signature: Data(repeating: 0, count: 64)), s[1]],
            [.init(publicKey: s[0].publicKey, signature: s[1].signature), s[1]]]
        for signatures in badSets {
            let forged = StellarSignedSend(bytes: StellarSendXDR.envelope(tx, signatures: signatures), publicKey: Data(), signature: Data(), hash: signed.hash, signatures: signatures)
            XCTAssertThrowsError(try StellarSendCrypto.verify(forged, plan: p))
        }
        let altered: [StellarSignedSend] = [
            .init(bytes: signed.bytes + Data([0]), publicKey: Data(), signature: Data(), hash: signed.hash, signatures: s),
            .init(bytes: signed.bytes, publicKey: Data(), signature: Data(), hash: String(repeating: "0", count: 64), signatures: s),
            .init(bytes: signed.bytes, publicKey: s[0].publicKey, signature: Data(), hash: signed.hash, signatures: s),
            .init(bytes: signed.bytes, publicKey: Data(), signature: s[0].signature, hash: signed.hash, signatures: s)]
        for forged in altered { XCTAssertThrowsError(try StellarSendCrypto.verify(forged, plan: p)) }
        var root = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(p)) as? [String: Any])
        for (field, value) in [("network", "mainnet" as Any), ("recipient", try address(97) as Any), ("sequence", 43 as Any), ("amount", "12500001" as Any)] {
            let old = root[field]; root[field] = value
            let changed = try JSONDecoder().decode(StellarSendPlan.self, from: JSONSerialization.data(withJSONObject: root))
            XCTAssertThrowsError(try StellarSendCrypto.verify(signed, plan: changed)); root[field] = old
        }
    }
    func testSDKDecodesAtomicSignerSetupAndMasterDisableForEveryPolicy() throws {
        var cases = 0
        for count in 2...20 { for required in 1...count {
            let policy = try policy(count, required), p = try plan(policy, configure: true)
            let signed = try StellarSendCrypto.sign(p, privateKey: key(99), now: p.createdAt)
            try StellarSendCrypto.verify(signed, plan: p)
            XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKeys: (1...required).map { key($0) }, now: p.createdAt))
            XCTAssertThrowsError(try StellarSendCrypto.sign(p, privateKey: key(1), now: p.createdAt))
            let decoded = try XDRDecoder.decode(TransactionEnvelopeXDR.self, data: signed.bytes)
            guard case .v1(let envelope) = decoded else { return XCTFail("Expected v1 envelope") }
            XCTAssertEqual(envelope.signatures.count, 1); XCTAssertEqual(envelope.tx.operations.count, count + 1)
            for (i, operation) in envelope.tx.operations.enumerated() {
                XCTAssertNil(operation.sourceAccount)
                guard case .setOptionsOp(let options) = operation.body else { return XCTFail("Expected SetOptions") }
                XCTAssertNil(options.inflationDestination); XCTAssertNil(options.clearFlags); XCTAssertNil(options.setFlags); XCTAssertNil(options.homeDomain)
                if i < count {
                    XCTAssertNil(options.masterWeight); XCTAssertNil(options.lowThreshold); XCTAssertNil(options.medThreshold); XCTAssertNil(options.highThreshold)
                    let signer = try XCTUnwrap(options.signer); XCTAssertEqual(signer.weight, 1)
                    guard case .ed25519(let publicKey) = signer.key else { return XCTFail("Expected ed25519 signer") }
                    XCTAssertEqual(try PublicKey(Array(publicKey.wrapped)).accountId, policy.signers[i])
                } else {
                    XCTAssertNil(options.signer); XCTAssertEqual(options.masterWeight, 0)
                    XCTAssertEqual(options.lowThreshold, UInt32(required)); XCTAssertEqual(options.medThreshold, UInt32(required)); XCTAssertEqual(options.highThreshold, UInt32(required))
                }
            }
            cases += 1
        } }
        XCTAssertEqual(cases, 209)
    }
}
