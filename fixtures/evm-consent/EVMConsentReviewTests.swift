import XCTest
@testable import OathAnkr

// Disposable deterministic keys; no provider, funded account or network access.
final class EVMConsentReviewTests: XCTestCase {
    let key = Data(repeating: 1, count: 32)
    let receiver = "0x" + String(repeating: "2", count: 40)
    let token = "0x" + String(repeating: "3", count: 40)
    let alternate = "0x" + String(repeating: "4", count: 40)
    let balance = "1000000000000000000000000"

    func plan(_ network: EVMSendNetwork = .ethereum, tokenized: Bool = false, legacy: Bool = false) throws -> EVMSendPlan {
        .init(network: network, sender: try EVMSendCrypto.address(privateKey: key), recipient: receiver,
              reference: tokenized ? token : "native", decimals: tokenized ? 6 : 18,
              requestedAmount: "1000000", amount: "1000000", assetBalance: balance, nativeBalance: balance,
              nonce: 7, gasLimit: tokenized ? 70000 : 21000, maxFeePerGas: 41000000000,
              maxPriorityFeePerGas: legacy ? 0 : 1000000000, blockHeight: 100, legacy: legacy)
    }
    func changed(_ p: EVMSendPlan, _ edit: (inout [String: Any]) throws -> Void) throws -> EVMSendPlan {
        var object = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(p)) as? [String: Any])
        try edit(&object)
        return try JSONDecoder().decode(EVMSendPlan.self, from: JSONSerialization.data(withJSONObject: object))
    }
    func rehashed(_ signed: EVMSignedSend, bytes: Data) -> EVMSignedSend {
        .init(bytes: bytes, signature: signed.signature, hash: "0x" + TronSendCrypto.hex(TronSendCrypto.keccak(bytes)),
              authorizationSignature: signed.authorizationSignature, multisigSignatures: signed.multisigSignatures)
    }

    func testAllChainsAndEnvelopeFormatsRejectCrossChainReplay() throws {
        XCTAssertEqual(EVMSendNetwork.allCases.count, 38)
        XCTAssertEqual(Set(EVMSendNetwork.allCases.map(\.chainID)).count, 38)
        var accepted = 0, rejected = 0
        for network in EVMSendNetwork.allCases {
            for tokenized in [false, true] { for legacy in [false, true] {
                let p = try plan(network, tokenized: tokenized, legacy: legacy)
                let s = try EVMSendCrypto.sign(p, privateKey: key)
                try EVMSendCrypto.verify(s, plan: p); accepted += 1
                let restored = try JSONDecoder().decode(EVMSignedSend.self, from: JSONEncoder().encode(s))
                try EVMSendCrypto.verify(restored, plan: p)
                for other in EVMSendNetwork.allCases where other != network {
                    let altered = try changed(p) { $0["network"] = other.rawValue }
                    try altered.validate()
                    XCTAssertThrowsError(try EVMSendCrypto.verify(s, plan: altered), "Replay \(network) -> \(other)")
                    rejected += 1
                }
            }}
        }
        XCTAssertEqual(accepted, 152); XCTAssertEqual(rejected, 5624)
    }

    func testSignedIntentRejectsValidButDifferentRecipientsAmountsFeesAndNonce() throws {
        var mutations = 0
        for network in EVMSendNetwork.allCases { for tokenized in [false, true] { for legacy in [false, true] {
            let p = try plan(network, tokenized: tokenized, legacy: legacy)
            let s = try EVMSendCrypto.sign(p, privateKey: key)
            var edits: [[String: Any]] = [
                ["recipient": alternate], ["amount": "999999"], ["nonce": 8],
                ["gasLimit": 71000], ["maxFeePerGas": 42000000000],
                ["sender": try EVMSendCrypto.address(privateKey: Data(repeating: 2, count: 32))]
            ]
            if tokenized { edits.append(["reference": alternate]) }
            if !legacy { edits.append(["maxPriorityFeePerGas": 2000000000]) }
            for edit in edits {
                let altered = try changed(p) { $0.merge(edit) { _, new in new } }
                try altered.validate()
                XCTAssertThrowsError(try EVMSendCrypto.verify(s, plan: altered), "Intent changed: \(edit.keys.sorted())")
                mutations += 1
            }
        }}}
        XCTAssertEqual(mutations, 1064)
    }

    func testEveryWireByteRejectsTamperingEvenWithRecomputedTransactionHash() throws {
        var checked = 0
        for tokenized in [false, true] { for legacy in [false, true] {
            let p = try plan(tokenized: tokenized, legacy: legacy)
            let s = try EVMSendCrypto.sign(p, privateKey: key)
            for index in s.bytes.indices {
                var bytes = s.bytes; bytes[index] ^= 1
                XCTAssertThrowsError(try EVMSendCrypto.verify(rehashed(s, bytes: bytes), plan: p), "Wire byte \(index)")
                checked += 1
            }
            for count in 0..<s.bytes.count {
                XCTAssertThrowsError(try EVMSendCrypto.verify(rehashed(s, bytes: Data(s.bytes.prefix(count))), plan: p))
                checked += 1
            }
            XCTAssertThrowsError(try EVMSendCrypto.verify(rehashed(s, bytes: s.bytes + Data([0])), plan: p))
        }}
        XCTAssertGreaterThan(checked, 800)
        print("EVM_WIRE_BYTE_AND_TRUNCATION_CASES=\(checked)")
    }

    func testWireBindingMutationControl() throws {
        var index = 0
        for tokenized in [false, true] { for legacy in [false, true] {
            let p = try plan(tokenized: tokenized, legacy: legacy)
            let s = try EVMSendCrypto.sign(p, privateKey: key)
            var bytes = s.bytes; bytes[bytes.count - 1] ^= 1
            XCTAssertThrowsError(try EVMSendCrypto.verify(rehashed(s, bytes: bytes), plan: p), "Wire binding removed: \(index)")
            index += 1
        }}
    }

    func testEverySafeThresholdRejectsInsufficientRepeatedAndReorderedOwners() throws {
        let executorKey = Data(repeating: 9, count: 32)
        let executor = try EVMSendCrypto.address(privateKey: executorKey)
        let keys = (1...15).map { Data(repeating: UInt8(20 + $0), count: 32) }
        let owners = try keys.map { try EVMSendCrypto.address(privateKey: $0) }
        var policies = 0, signedPlans = 0
        for count in 2...15 { for required in 1...count {
            let policy = try EVMMultisigPolicy(required: required, owners: Array(owners.prefix(count)),
                salt: Data(repeating: UInt8(required * 16 + count), count: 32), executor: executor)
            policies += 1
            for tokenized in [false, true] {
                let p = EVMSendPlan(network: .ethereum, sender: try policy.address, recipient: receiver,
                    reference: tokenized ? token : "native", decimals: tokenized ? 6 : 18,
                    requestedAmount: "1000000", amount: "1000000", assetBalance: balance, nativeBalance: balance,
                    nonce: 7, gasLimit: 400000, maxFeePerGas: 41000000000, maxPriorityFeePerGas: 1000000000,
                    blockHeight: 100, multisig: .init(policy: policy, safeNonce: 3, executorBalance: balance))
                let selected = Array(keys.prefix(count).suffix(required))
                let s = try EVMMultisigCrypto.sign(p, keys: selected, executorKey: executorKey)
                try EVMSendCrypto.verify(s, plan: p); signedPlans += 1
                let sigs = try XCTUnwrap(s.multisigSignatures)
                XCTAssertEqual(sigs.count, required * 65)
                XCTAssertThrowsError(try EVMMultisigCrypto.sign(p, keys: Array(selected.dropLast()), executorKey: executorKey))
                XCTAssertThrowsError(try EVMMultisigCrypto.sign(p, keys: selected + [selected[0]], executorKey: executorKey))
                XCTAssertThrowsError(try EVMMultisigCrypto.sign(p, keys: [Data(repeating: 90, count: 32)] + Array(selected.dropFirst()), executorKey: executorKey))
                if required > 1 {
                    let reversed = stride(from: sigs.count - 65, through: 0, by: -65).reduce(Data()) { $0 + Data(sigs[$1..<$1+65]) }
                    let reordered = EVMSignedSend(bytes: s.bytes, signature: s.signature, hash: s.hash, multisigSignatures: reversed)
                    XCTAssertThrowsError(try EVMSendCrypto.verify(reordered, plan: p))
                }
                let movedNonce = try changed(p) {
                    var context = try XCTUnwrap($0["multisig"] as? [String: Any]); context["safeNonce"] = 4; $0["multisig"] = context
                }
                try movedNonce.validate()
                XCTAssertThrowsError(try EVMSendCrypto.verify(s, plan: movedNonce))
            }
        }}
        XCTAssertEqual(policies, 119); XCTAssertEqual(signedPlans, 238)
    }

    func testDelegationAuthorizationCannotMoveAcrossChainOrNonce() throws {
        let owner = try EVMSendCrypto.address(privateKey: key)
        let removal = EVMPermissionRemoval(kind: .delegation, contract: owner, spender: alternate, expected: alternate)
        for network in EVMSendNetwork.allCases {
            let p = EVMSendPlan(network: network, sender: owner, recipient: owner, reference: "native", decimals: 18,
                requestedAmount: "0", amount: "0", assetBalance: balance, nativeBalance: balance, nonce: 7,
                gasLimit: 70000, maxFeePerGas: 41000000000, maxPriorityFeePerGas: 1000000000, blockHeight: 100, removal: removal)
            let s = try EVMSendCrypto.sign(p, privateKey: key)
            try EVMSendCrypto.verify(s, plan: p)
            XCTAssertEqual(s.bytes.first, 4); XCTAssertEqual(p.receiver, EVMPermissionRemoval.zero)
            XCTAssertEqual(p.value, "0"); XCTAssertEqual(try EVMSendCrypto.data(p), Data())
            for other in EVMSendNetwork.allCases where other != network {
                let otherPlan = try changed(p) { $0["network"] = other.rawValue }
                let otherSigned = try EVMSendCrypto.sign(otherPlan, privateKey: key)
                // Keep a valid outer signature for the destination chain while substituting only the authorization.
                let substituted = EVMSignedSend(bytes: otherSigned.bytes, signature: otherSigned.signature,
                    hash: otherSigned.hash, authorizationSignature: s.authorizationSignature)
                XCTAssertThrowsError(try EVMSendCrypto.verify(substituted, plan: otherPlan))
            }
            let next = try changed(p) { $0["nonce"] = 8 }
            let nextSigned = try EVMSendCrypto.sign(next, privateKey: key)
            XCTAssertThrowsError(try EVMSendCrypto.verify(.init(bytes: nextSigned.bytes, signature: nextSigned.signature,
                hash: nextSigned.hash, authorizationSignature: s.authorizationSignature), plan: next))
        }
    }
}
