import XCTest
import CryptoKit
@testable import OathAnkr

/// Synthetic keys only. No transport or funded account is used.
final class MultisigAuthorityReviewTests: XCTestCase {
    private let now = Date(timeIntervalSince1970: 2_000_000_000)
    private func keys(_ n: Int) -> [Data] {
        (1...n).map { Data(repeating: UInt8($0), count: 32) }
    }
    private func edKeys(_ n: Int) throws -> [Data] {
        try keys(n).map { ($0, try SuiSendCrypto.publicKey(privateKey: $0)) }
            .sorted { $0.1.lexicographicallyPrecedes($1.1) }.map(\.0)
    }
    private func aptos(_ policy: AptosMultisigPolicy, amount: UInt64 = 123456) throws -> AptosSendPlan {
        .init(network: .mainnet, sender: policy.address, recipient: try AptosIdentity.address("0xabc"),
              reference: "native", publicKey: policy.bytes, decimals: 8,
              requestedAmount: amount, amount: amount, assetBalance: 100_000_000, nativeBalance: 100_000_000,
              sequence: 7, gasUnitPrice: 100, maxGasAmount: 2000, expiration: 2_000_000_300,
              createdAt: now, multisig: policy)
    }
    private func sui(_ policy: SuiMultisigPolicy, amount: UInt64 = 1_000_000) throws -> SuiSendPlan {
        let funds = SuiSendFunds(coins: [], addressBalance: 1_000_000_000)
        return try .make(network: .mainnet, sender: policy.address, recipient: "0xabc", reference: "native",
                         amount: amount, native: funds, asset: funds, gasPrice: 1000, gasBudget: 5_000_000,
                         epoch: 1252, nonce: 42, now: now, multisig: policy)
    }
    private func thor(_ policy: ThorchainMultisigPolicy, amount: String = "100", sequence: UInt64 = 2) throws -> ThorchainSendPlan {
        try .init(network: .localTestnet, sender: policy.address(network: .localTestnet),
                  recipient: ThorchainSendCrypto.address(publicKey: ThorchainSendCrypto.publicKey(privateKey: Data(repeating: 99, count: 32)), network: .localTestnet),
                  reference: "native", memo: "Synthetic authority review", publicKey: policy.aminoPublicKey,
                  decimals: 8, requestedAmount: amount, amount: amount, assetBalance: "10000000", nativeBalance: "10000000",
                  accountNumber: 4, sequence: sequence, fee: 2000000, height: 100, timeoutHeight: 130, multisig: policy)
    }

    func testAptosEveryThresholdRejectsMissingDuplicateAndMisindexedSigners() throws {
        var policies = 0
        for count in 2...32 {
            let all = try edKeys(count), pubs = try all.map(AptosSendCrypto.publicKey)
            for required in 1...count {
                let policy = try AptosMultisigPolicy(required: required, publicKeys: pubs)
                let plan = try aptos(policy), selected = Array(all.prefix(required))
                let signed = try AptosSendCrypto.sign(plan, privateKeys: selected, now: now)
                try AptosSendCrypto.verify(signed, plan: plan)
                let parts = try XCTUnwrap(signed.signatures)
                XCTAssertEqual(parts.map(\.index), Array(0..<required))
                XCTAssertThrowsError(try AptosSendCrypto.sign(plan, privateKeys: Array(selected.dropLast()), now: now))
                let missing = Array(parts.dropLast())
                let wire = try AptosSendCrypto.raw(plan) + AptosSendCrypto.multisigAuthenticator(policy, signatures: missing)
                XCTAssertThrowsError(try AptosSendCrypto.verify(.init(bytes: wire, publicKey: policy.bytes, signature: Data(), hash: AptosSendCrypto.hash(wire), signatures: missing), plan: plan))
                var wrong = parts
                wrong[0] = .init(index: 32, signature: parts[0].signature)
                XCTAssertThrowsError(try AptosSendCrypto.verify(.init(bytes: signed.bytes, publicKey: policy.bytes, signature: Data(), hash: signed.hash, signatures: wrong), plan: plan))
                if required > 1 {
                    wrong = parts; wrong[1] = wrong[0]
                    let duplicate = try AptosSendCrypto.raw(plan) + AptosSendCrypto.multisigAuthenticator(policy, signatures: wrong)
                    XCTAssertThrowsError(try AptosSendCrypto.verify(.init(bytes: duplicate, publicKey: policy.bytes, signature: Data(), hash: AptosSendCrypto.hash(duplicate), signatures: wrong), plan: plan))
                }
                XCTAssertThrowsError(try AptosSendCrypto.verify(signed, plan: aptos(policy, amount: 123457)))
                policies += 1
            }
        }
        XCTAssertEqual(policies, 527)
        print("CORPUS aptos policies=527")
    }

    func testSuiEveryThresholdAndSignerBitBindsPolicy() throws {
        var policies = 0, changedBits = 0
        for count in 2...10 {
            let all = try edKeys(count), pubs = try all.map(SuiSendCrypto.publicKey)
            for required in 1...count {
                let policy = try SuiMultisigPolicy(required: required, publicKeys: pubs), plan = try sui(policy)
                let signed = try SuiSendCrypto.sign(plan, privateKeys: Array(all.prefix(required)), now: now)
                try SuiSendCrypto.verify(signed, sender: policy.address)
                XCTAssertThrowsError(try SuiSendCrypto.sign(plan, privateKeys: Array(all.prefix(required - 1)), now: now))
                let bitmapOffset = 2 + 65 * required
                for bit in 0..<16 {
                    var envelope = signed.signature; envelope[bitmapOffset + bit / 8] ^= 1 << (bit % 8)
                    XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: envelope, digest: signed.digest), sender: policy.address))
                    changedBits += 1
                }
                let changed = try sui(policy, amount: 1_000_001).transactionBytes()
                XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: changed, signature: signed.signature, digest: SuiSendCrypto.digest(changed)), sender: policy.address))
                policies += 1
            }
        }
        XCTAssertEqual(policies, 54); XCTAssertEqual(changedBits, 864)
        print("CORPUS sui policies=54 changed-bits=864")
    }

    func testSuiExhaustiveBitmapCannotAttributeSignaturesToOtherMembers() throws {
        let all = try edKeys(3), policy = try SuiMultisigPolicy(required: 2, publicKeys: all.map(SuiSendCrypto.publicKey))
        let signed = try SuiSendCrypto.sign(sui(policy), privateKeys: Array(all.prefix(2)), now: now)
        let offset = 2 + 65 * 2
        var accepted = [Int]()
        for bitmap in 0...65535 {
            var envelope = signed.signature; envelope[offset] = UInt8(bitmap & 255); envelope[offset+1] = UInt8(bitmap >> 8)
            do { try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: envelope, digest: signed.digest), sender: policy.address); accepted.append(bitmap) }
            catch { XCTAssertEqual(error as? SuiSendError, .signing) }
        }
        XCTAssertEqual(accepted, [3])
        print("CORPUS sui bitmap-values=65536 accepted=1 rejected=65535")
    }

    func testPoliciesRejectDuplicateKeysAndPersistedOrderChanges() throws {
        let all = try edKeys(3), pubs = try all.map(SuiSendCrypto.publicKey)
        for required in [0, 4, Int.max] {
            XCTAssertThrowsError(try AptosMultisigPolicy(required: required, publicKeys: pubs))
            XCTAssertThrowsError(try SuiMultisigPolicy(required: required, publicKeys: pubs))
        }
        for publicKeys in [[pubs[0],pubs[0]], [pubs[0],Data(pubs[1].dropLast())], [pubs[0],pubs[1]+Data([0])], Array(pubs.reversed())] {
            let json = try JSONSerialization.data(withJSONObject: ["required":2,"publicKeys":publicKeys.map { $0.base64EncodedString() }])
            XCTAssertThrowsError(try JSONDecoder().decode(AptosMultisigPolicy.self, from: json))
            XCTAssertThrowsError(try JSONDecoder().decode(SuiMultisigPolicy.self, from: json))
        }
        let a = try AptosMultisigPolicy(required: 2, publicKeys: pubs), s = try SuiMultisigPolicy(required: 2, publicKeys: pubs)
        XCTAssertEqual(try JSONDecoder().decode(AptosMultisigPolicy.self, from: JSONEncoder().encode(a)), a)
        XCTAssertEqual(try JSONDecoder().decode(SuiMultisigPolicy.self, from: JSONEncoder().encode(s)), s)
        XCTAssertNotEqual(a.address, try AptosMultisigPolicy(required: 1, publicKeys: pubs).address)
        XCTAssertNotEqual(s.address, try SuiMultisigPolicy(required: 1, publicKeys: pubs).address)
    }

    func testThorchainThresholdsRetainAmountSequenceAndWireBinding() throws {
        var policies = 0
        for count in 2...7 {
            let all = keys(count), pubs = try all.map(ThorchainSendCrypto.publicKey)
            for required in 1...count {
                let policy = try ThorchainMultisigPolicy(required: required, publicKeys: pubs), plan = try thor(policy)
                let signed = try ThorchainSendCrypto.sign(plan, privateKeys: Array(all.prefix(required)))
                try ThorchainSendCrypto.verify(signed, plan: plan)
                XCTAssertThrowsError(try ThorchainSendCrypto.verify(signed, plan: thor(policy, amount: "101")))
                XCTAssertThrowsError(try ThorchainSendCrypto.verify(signed, plan: thor(policy, sequence: 3)))
                for index in [0,1,signed.bytes.count / 2,signed.bytes.count-1] {
                    var changed = signed.bytes; changed[index] ^= 1
                    let hash = TronSendCrypto.hex(Data(SHA256.hash(data: changed))).uppercased()
                    XCTAssertThrowsError(try ThorchainSendCrypto.verify(.init(bytes: changed, signature: signed.signature, hash: hash), plan: plan))
                }
                policies += 1
            }
        }
        XCTAssertEqual(policies, 27)
        print("CORPUS thorchain policies=27 altered-plans=54 altered-wires=108")
    }

    func testSuiThresholdMutationControl() throws {
        for (index, pair) in [(2,2),(3,2),(3,3)].enumerated() {
            let all = try edKeys(pair.0), policy = try SuiMultisigPolicy(required: pair.1, publicKeys: all.map(SuiSendCrypto.publicKey))
            let signed = try SuiSendCrypto.sign(sui(policy), privateKeys: Array(all.prefix(pair.1)), now: now)
            // Keep one genuine member signature for these exact bytes, the full
            // original policy and its address. Only the threshold is unsatisfied.
            let envelope = Data([3,1]) + signed.signature.subdata(in: 2..<67) + Data([1,0]) + policy.bytes
            XCTAssertThrowsError(try SuiSendCrypto.verify(.init(bytes: signed.bytes, signature: envelope, digest: signed.digest), sender: policy.address), "Threshold guard removed: \(index)")
        }
    }
}
