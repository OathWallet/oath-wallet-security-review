import XCTest
import CryptoKit
@testable import OathAnkr

/// Audit-only synthetic inputs. No funded account, RPC service or production key.
@MainActor final class AptosIntentReviewTests: XCTestCase {
    private let now = Date(timeIntervalSince1970: 2_000_000_000)
    private let key = Data(repeating: 1, count: 32)
    private func plan(_ reference: String = "native", live: Bool = false) throws -> AptosSendPlan {
        let date=live ? Date.now : now
        return .init(network:.testnet, sender:try AptosSendCrypto.address(privateKey:key),
            recipient:try AptosSendCrypto.address(privateKey:Data(repeating:2, count:32)),
            reference:try AptosIdentity.reference(reference), publicKey:try AptosSendCrypto.publicKey(privateKey:key),
            decimals:reference == "native" ? 8 : 6, requestedAmount:123456, amount:123456,
            assetBalance:100_000_000, nativeBalance:100_000_000, sequence:7, gasUnitPrice:100,
            maxGasAmount:2000, expiration:UInt64(date.timeIntervalSince1970)+300, createdAt:date)
    }
    private func altered(_ p: AptosSendPlan, _ changes: [String: Any]) throws -> AptosSendPlan {
        var json = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(p)) as? [String: Any])
        for (k, v) in changes { json[k] = v }
        return try JSONDecoder().decode(AptosSendPlan.self, from: JSONSerialization.data(withJSONObject: json))
    }
    private func reject(_ signed: AptosSignedSend, _ p: AptosSendPlan, _ reason: String,
                        file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertThrowsError(try AptosSendCrypto.verify(signed, plan: p), reason, file: file, line: line) {
            XCTAssertEqual($0 as? AptosSendError, .signing, reason, file: file, line: line)
        }
    }

    func testEverySignedWireByteIsBoundToApprovedPlan() throws {
        for ref in ["native", "0x123::example::Token", "0x456"] {
            let p = try plan(ref), s = try AptosSendCrypto.sign(p, privateKey: key, now: now)
            try AptosSendCrypto.verify(s, plan: p)
            for i in s.bytes.indices {
                var wire = s.bytes; wire[i] ^= 1
                reject(.init(bytes: wire, publicKey: s.publicKey, signature: s.signature,
                             hash: AptosSendCrypto.hash(wire)), p, "Wire mutation accepted at \(i), \(ref)")
            }
            for wire in [s.bytes + Data([0]), Data(s.bytes.dropLast()), Data()] {
                reject(.init(bytes: wire, publicKey: s.publicKey, signature: s.signature,
                             hash: AptosSendCrypto.hash(wire)), p, "Wire length mutation accepted")
            }
        }
    }

    func testChangedApprovedFieldsCannotReuseSignature() throws {
        for ref in ["native", "0x123::example::Token", "0x456"] {
            let p = try plan(ref), s = try AptosSendCrypto.sign(p, privateKey: key, now: now)
            let changes: [[String: Any]] = [
                ["recipient": try AptosIdentity.address("0x777")], ["amount": 123455],
                ["sequence": 8], ["gasUnitPrice": 101], ["maxGasAmount": 2001],
                ["expiration": p.expiration + 1], ["network": "mainnet"],
                ["reference": try AptosIdentity.reference("0x789::other::Token")]
            ]
            for change in changes {
                let changed = try altered(p, change)
                try changed.validate(now: now) // Reject at signature binding, not an invalid-plan precondition.
                reject(s, changed, "Approved field substitution accepted: \(change.keys.sorted())")
            }
        }
    }

    func testOfficialSDKVectorsRemainAuthoritative() throws {
        struct Vector: Decodable { let reference, publicKey, raw, signature, signed, hash: String }
        let url = try XCTUnwrap(Bundle.module.url(forResource: "vectors", withExtension: "json", subdirectory: "Fixtures/AptosSend"))
        let vectors = try JSONDecoder().decode([Vector].self, from: Data(contentsOf: url))
        XCTAssertEqual(vectors.count, 4)
        for v in vectors {
            let p = try plan(v.reference)
            XCTAssertEqual(try AptosSendCrypto.raw(p), try TronIdentity.hex(v.raw))
            let sdk = AptosSignedSend(bytes: try TronIdentity.hex(v.signed), publicKey: try TronIdentity.hex(v.publicKey),
                                      signature: try TronIdentity.hex(v.signature), hash: v.hash)
            try AptosSendCrypto.verify(sdk, plan: p)
            XCTAssertEqual(AptosSendCrypto.hash(sdk.bytes), v.hash)
        }
    }

    func testSignatureKeyAndHashSubstitutionRejected() throws {
        let p = try plan(), s = try AptosSendCrypto.sign(p, privateKey: key, now: now)
        let other = try AptosSendCrypto.publicKey(privateKey: Data(repeating: 2, count: 32))
        reject(.init(bytes:s.bytes, publicKey:other, signature:s.signature, hash:s.hash), p, "Wrong public key")
        reject(.init(bytes:s.bytes, publicKey:s.publicKey, signature:Data(repeating:0, count:64), hash:s.hash), p, "Wrong signature")
        reject(.init(bytes:s.bytes, publicKey:s.publicKey, signature:s.signature, hash:"0x" + String(repeating:"0", count:64)), p, "Wrong hash")
        reject(.init(bytes:s.bytes, publicKey:s.publicKey, signature:s.signature, hash:s.hash, signatures:[]), p, "Wrong authenticator family")
    }

    private func multi(_ indexes: [Int]) throws -> (AptosSendPlan, [Data]) {
        let keys = try (1...32).map { n -> (Data, Data) in
            let key = Data(repeating: UInt8(n), count: 32)
            return (key, try AptosSendCrypto.publicKey(privateKey: key))
        }.sorted { $0.1.lexicographicallyPrecedes($1.1) }
        let policy = try AptosMultisigPolicy(required: indexes.count, publicKeys: keys.map(\.1))
        let p = try plan()
        let m = AptosSendPlan(network:p.network, sender:policy.address, recipient:p.recipient,
            reference:p.reference, publicKey:policy.bytes, decimals:p.decimals, requestedAmount:p.requestedAmount,
            amount:p.amount, assetBalance:p.assetBalance, nativeBalance:p.nativeBalance, sequence:p.sequence,
            gasUnitPrice:p.gasUnitPrice, maxGasAmount:p.maxGasAmount, expiration:p.expiration,
            createdAt:p.createdAt, multisig:policy)
        return (m, indexes.map { keys[$0].0 })
    }

    func testMultisigThresholdAndBitmapByteBoundaries() throws {
        for indexes in [[0], [31], [0, 7], [7, 8], [15, 16], [0, 7, 8, 15, 16, 31], Array(0..<32)] {
            let (p, keys) = try multi(indexes)
            let s = try AptosSendCrypto.sign(p, privateKeys: Array(keys.reversed()), now: now)
            try AptosSendCrypto.verify(s, plan:p)
            XCTAssertEqual(s.signatures?.map(\.index), indexes)
            var expected = [UInt8](repeating:0, count:4)
            for index in indexes { expected[index / 8] |= UInt8(1 << (7 - index % 8)) }
            XCTAssertEqual(Array(s.bytes.suffix(5)), [4] + expected)
            var wire=s.bytes; wire[wire.count-1] ^= 1
            reject(.init(bytes:wire, publicKey:s.publicKey, signature:s.signature,
                         hash:AptosSendCrypto.hash(wire), signatures:s.signatures), p, "Multisig bitmap substitution")
        }
    }

    func testMultisigCannotChangeSignerThresholdOrderOrPlan() throws {
        let (p, keys) = try multi([0, 31]), s = try AptosSendCrypto.sign(p, privateKeys:keys, now:now)
        let sigs = try XCTUnwrap(s.signatures)
        for bad in [Array(sigs.reversed()), [sigs[0], sigs[0]], [sigs[0]],
                    [sigs[0], .init(index:32, signature:sigs[1].signature)],
                    [sigs[0], .init(index:-1, signature:sigs[1].signature)],
                    [sigs[0], .init(index:30, signature:sigs[1].signature)]] {
            reject(.init(bytes:s.bytes, publicKey:s.publicKey, signature:s.signature, hash:s.hash, signatures:bad), p, "Changed multisig signer set")
        }
        let changed = try altered(p, ["amount":123455]); try changed.validate(now:now)
        reject(s, changed, "Multisig changed amount")
        XCTAssertThrowsError(try AptosSendCrypto.sign(p, privateKeys:[keys[0], keys[0]], now:now))
        XCTAssertThrowsError(try AptosSendCrypto.sign(p, privateKeys:[keys[0]], now:now))
        XCTAssertThrowsError(try AptosSendCrypto.sign(p, privateKey:keys[0], now:now))
    }

    func testCorruptedSignedTransactionNeverReachesTransport() async throws {
        let p = try plan(live:true), s = try AptosSendCrypto.sign(p, privateKey:key)
        var wire=s.bytes; wire[0] ^= 1
        let t=AptosSendFixture(plan:p), c=try AptosSendClient(network:p.network, transport:t)
        for reconcile in [false, true] {
            do {
                _ = try await c.submit(.init(bytes:wire, publicKey:s.publicKey, signature:s.signature,
                        hash:AptosSendCrypto.hash(wire)), plan:p, reconcileFirst:reconcile)
                XCTFail("Corrupt bytes submitted")
            } catch { XCTAssertEqual(error as? AptosSendError, .signing) }
        }
        let calls=await t.paths; XCTAssertTrue(calls.isEmpty, "Invalid signature performed network work")
    }

    func testWrongNetworkNeverReachesTransport() async throws {
        let p=try plan(live:true), s=try AptosSendCrypto.sign(p, privateKey:key), t=AptosSendFixture(plan:p)
        let c=try AptosSendClient(network:.mainnet, transport:t)
        do { _ = try await c.submit(s, plan:p, reconcileFirst:false); XCTFail("Wrong network submitted") }
        catch { XCTAssertEqual(error as? AptosSendError, .wrongNetwork) }
        let calls=await t.paths; XCTAssertTrue(calls.isEmpty)
    }

    func testSimulationCannotSubstituteTransactionFields() async throws {
        for ref in ["native", "0x123::example::Token", "0x456"] {
            let p=try plan(ref, live:true)
            let valid=try AptosSendClient(network:p.network, transport:AptosSendFixture(plan:p))
            _ = try await valid.quote(sender:p.sender, recipient:p.recipient, reference:p.reference,
                                     publicKey:p.publicKey, decimals:p.decimals, amount:String(p.amount))
            var fields=["sender", "sequence_number", "max_gas_amount", "gas_unit_price", "expiration_timestamp_secs", "function", "type", "type_arguments", "recipient", "amount"]
            if ref == "0x456" { fields += ["metadata", "minimum_deposit"] }
            for field in fields {
                let t=AptosMutationTransport(plan:p, field:field), c=try AptosSendClient(network:p.network, transport:t)
                do {
                    _ = try await c.quote(sender:p.sender, recipient:p.recipient, reference:p.reference,
                                         publicKey:p.publicKey, decimals:p.decimals, amount:String(p.amount))
                    XCTFail("Simulation substitution accepted: \(ref), \(field)")
                } catch { XCTAssertEqual(error as? AptosSendError, .changed, "\(ref), \(field)") }
                let count=await t.mutations; XCTAssertGreaterThan(count,0)
                let sent=await t.fixture.broadcast; XCTAssertNil(sent)
            }
        }
    }
}

private actor AptosMutationTransport: AnkrTransport {
    let fixture: AptosSendFixture
    let field: String
    var mutations=0
    init(plan:AptosSendPlan, field:String) { fixture=AptosSendFixture(plan:plan);self.field=field }
    func send(_ request:URLRequest) async throws -> (Data,Int) {
        let (data,status)=try await fixture.send(request)
        guard request.url?.path.hasSuffix("/simulate") == true else { return (data,status) }
        guard var rows=try JSONSerialization.jsonObject(with:data) as? [[String:Any]],
              var tx=rows.first, var payload=tx["payload"] as? [String:Any],
              var args=payload["arguments"] as? [Any] else { throw AptosSendError.malformed }
        switch field {
        case "sender": tx[field]="0x777"
        case "sequence_number", "max_gas_amount", "gas_unit_price", "expiration_timestamp_secs":
            guard let text=tx[field] as? String, let value=UInt64(text) else { throw AptosSendError.malformed }
            tx[field]=String(value + 1)
        case "function": payload[field]="0x1::aptos_account::create_account"
        case "type": payload[field]="script_payload"
        case "type_arguments": payload[field]=["0x999::other::Token"]
        case "recipient": args[args.count == 4 ? 1 : 0]="0x777"
        case "metadata": args[0]=["inner":"0x999"]
        case "minimum_deposit": args[3]="1"
        case "amount":
            let index=args.count == 4 ? 2 : 1
            guard let text=args[index] as? String, let value=UInt64(text) else { throw AptosSendError.malformed }
            args[index]=String(value + 1)
        default: throw AptosSendError.malformed
        }
        payload["arguments"]=args;tx["payload"]=payload;rows[0]=tx;mutations += 1
        return (try JSONSerialization.data(withJSONObject:rows),status)
    }
}
