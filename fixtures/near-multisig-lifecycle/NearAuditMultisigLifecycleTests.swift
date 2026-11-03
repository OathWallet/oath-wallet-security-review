import Foundation
import XCTest
@testable import OathAnkr

/// Synthetic provider state only. Production signing, receipts and submission run unchanged.
private actor LifecycleProvider: AnkrTransport {
    let plan: NearSendPlan
    let signed: NearSignedSend
    let nonces: [UInt64]
    var finalized = 0
    var failureIndex: Int?
    var wrongID = false
    var wrongRequest = false
    let headHash = SuiSendCrypto.base58(Data(repeating: 4, count: 32))
    let inclusionHash = SuiSendCrypto.base58(Data(repeating: 5, count: 32))
    var height: UInt64 = 3
    var observedNonce: UInt64 = 99
    var sent: [Data] = []
    var holdNext = false
    var held: CheckedContinuation<Void, Never>?
    var observer: CheckedContinuation<Void, Never>?
    init(_ plan: NearSendPlan, _ signed: NearSignedSend) throws {
        self.plan = plan; self.signed = signed
        nonces = try NearSendCrypto.multisigRaw(plan).map(\.nonce)
    }
    func configure(finalized: Int = 0, failure: Int? = nil, wrongID: Bool = false, wrongRequest: Bool = false, expired: Bool = false, nonce: UInt64 = 99) {
        self.finalized = finalized; failureIndex = failure
        self.wrongID = wrongID; self.wrongRequest = wrongRequest
        height = expired ? plan.blockHeight + plan.validityPeriod + 1 : 3
        observedNonce = nonce
    }
    func broadcasts() -> [Data] { sent }
    func armHold() { holdNext = true }
    func waitUntilHeld() async {
        if held != nil { return }
        await withCheckedContinuation { observer = $0 }
    }
    func release() { held?.resume(); held = nil }
    func receipt(_ index: Int) -> NearJSON {
        let part = signed.multisigParts![index]
        let id = SuiSendCrypto.base58(Data(repeating: UInt8(index + 20), count: 32))
        let value = index == 0 ? String(plan.multisig!.requestID + (wrongID ? 1 : 0)) : "null"
        let terminal: NearJSON = failureIndex == index
            ? .object(["Failure": .object(["ActionError": .object([:])])])
            : .object(["SuccessValue": .string(Data(value.utf8).base64EncodedString())])
        func outcome(_ id: String, _ children: [String], _ status: NearJSON) -> NearJSON {
            .object(["id": .string(id), "block_hash": .string(inclusionHash), "outcome": .object([
                "executor_id": .string(plan.sender), "tokens_burnt": .string("3"),
                "receipt_ids": .array(children.map(NearJSON.string)), "status": status])])
        }
        return .object(["transaction": .object([
            "hash": .string(part.hash), "signer_id": .string(plan.sender), "receiver_id": .string(plan.receiver),
            "public_key": .string(NearSendCrypto.keyString(part.publicKey)), "nonce": .number(String(nonces[index]))]),
            "final_execution_status": .string("FINAL"), "status": terminal,
            "transaction_outcome": outcome(part.hash, [id], .object(["SuccessReceiptId": .string(id)])),
            "receipts_outcome": .array([outcome(id, [], terminal)])])
    }
    func send(_ request: URLRequest) async throws -> (Data, Int) {
        let call = try JSONDecoder().decode(NearJSON.self, from: XCTUnwrap(request.httpBody))
        let p = call["params"], policy = plan.multisig!.policy
        let result: NearJSON
        switch call["method"].string {
        case "EXPERIMENTAL_protocol_config": result = .object(["chain_id": .string("testnet")])
        case "block":
            if let included = p["block_id"].string {
                XCTAssertEqual(included, inclusionHash)
                result = .object(["header": .object(["hash": .string(inclusionHash), "height": .number("2")])])
            } else {
                result = .object(["header": .object(["hash": .string(headHash), "height": .number(String(height))])])
            }
        case "tx":
            XCTAssertEqual(p["wait_until"].string, "NONE")
            XCTAssertEqual(p["sender_account_id"].string, plan.sender)
            let index = try XCTUnwrap(signed.multisigParts!.firstIndex { $0.hash == p["tx_hash"].string })
            if holdNext {
                holdNext = false
                await withCheckedContinuation { held = $0; observer?.resume(); observer = nil }
            }
            if index < finalized { result = receipt(index) }
            else { return (try JSONEncoder().encode(NearJSON.object(["jsonrpc": .string("2.0"), "id": .number("1"), "error": .object(["cause": .object(["name": .string("UNKNOWN_TRANSACTION")])])])), 200) }
        case "broadcast_tx_async":
            let bytes = try XCTUnwrap(Data(base64Encoded: XCTUnwrap(p.array?.first?.string)))
            let part = try XCTUnwrap(signed.multisigParts!.first { $0.bytes == bytes })
            sent.append(bytes); result = .string(part.hash)
        case "query":
            XCTAssertEqual(p["block_id"].string, headHash)
            var fields: [String: NearJSON] = ["block_hash": .string(headHash)]
            switch p["request_type"].string {
            case "view_account": fields["code_hash"] = .string(try NearMultisigPolicy.codeHash); fields["amount"] = .string(plan.nativeBalance)
            case "view_access_key": fields["nonce"] = .number(String(observedNonce))
            case "view_access_key_list": fields["keys"] = .array(policy.publicKeys.map { pub in
                .object(["public_key": .string(NearSendCrypto.keyString(pub)), "access_key": .object(["nonce": .number("99"), "permission": .object(["FunctionCall": .object(["allowance": .null, "receiver_id": .string(plan.sender), "method_names": .array(NearMultisigPolicy.methods.map(NearJSON.string))])])])])
            })
            case "call_function":
                let response: NearJSON
                switch p["method_name"].string {
                case "get_members": response = .array(policy.publicKeys.map { .object(["public_key": .string(NearSendCrypto.keyString($0))]) })
                case "get_num_confirmations": response = .number(String(policy.required))
                case "get_request": response = wrongRequest ? .object(["receiver_id": .string("other.testnet"), "actions": .array([])]) : try plan.multisig!.request(plan)
                default: throw NearSendError.malformed
                }
                fields["result"] = .array(try JSONEncoder().encode(response).map { .number(String($0)) })
            default: throw NearSendError.malformed
            }
            result = .object(fields)
        default: throw NearSendError.malformed
        }
        return (try JSONEncoder().encode(NearJSON.object(["jsonrpc": .string("2.0"), "id": .number("1"), "result": result])), 200)
    }
}

final class NearAuditMultisigLifecycleTests: XCTestCase, @unchecked Sendable {
    private func client(_ provider: LifecycleProvider) throws -> NearSendClient {
        try NearSendClient(network: .testnet, endpoints: [URL(string: "https://synthetic.invalid")!], transport: provider)
    }
    func testStagedTransferColdRestartPreservesBytesAndFees() async throws {
        for quorum in [1, 2, 5, 10] {
            for token in [false, true] {
                let (p, keys) = try NearMultisigTests().fixture(required: quorum, count: max(2, quorum), token: token)
                let s = try NearSendCrypto.sign(p, privateKeys: keys), provider = try LifecycleProvider(p, s)
                let planBytes = try JSONEncoder().encode(p), signedBytes = try JSONEncoder().encode(s)
                for index in 0..<s.multisigParts!.count {
                    await provider.configure(finalized: index)
                    // New client/cache and decoded durable bytes on every reconciliation pass.
                    let restored = try JSONDecoder().decode(NearSignedSend.self, from: signedBytes)
                    let restoredPlan = try JSONDecoder().decode(NearSendPlan.self, from: planBytes)
                    let result = try await client(provider).submit(restored, plan: restoredPlan)
                    XCTAssertEqual(result.outcome, .unknown)
                    let sent = await provider.broadcasts()
                    XCTAssertEqual(sent, Array(s.multisigParts!.prefix(index + 1)).map(\.bytes))
                }
                await provider.configure(finalized: s.multisigParts!.count)
                let final = try await client(provider).status(s, plan: p)
                XCTAssertEqual(final.outcome, .confirmed); XCTAssertEqual(final.hash, s.hash)
                XCTAssertEqual(final.fee, String(6 * s.multisigParts!.count))
                let sent = await provider.broadcasts(); XCTAssertEqual(sent.count, s.multisigParts!.count)
            }
        }
    }
    func testStatusNeverBroadcastsAndFailureStopsRemainingParts() async throws {
        let (p, keys) = try NearMultisigTests().fixture(), s = try NearSendCrypto.sign(p, privateKeys: keys)
        for index in 0..<s.multisigParts!.count {
            let provider = try LifecycleProvider(p, s)
            await provider.configure(finalized: index)
            let pending = try await client(provider).status(s, plan: p)
            XCTAssertEqual(pending.outcome, .unknown)
            await provider.configure(finalized: index + 1, failure: index)
            let failed = try await client(provider).submit(s, plan: p)
            XCTAssertEqual(failed.outcome, .failed); XCTAssertEqual(failed.fee, String(6 * (index + 1)))
            let sent = await provider.broadcasts(); XCTAssertTrue(sent.isEmpty)
        }
    }
    func testChangedRequestAndProposalIDNeverReleaseConfirmation() async throws {
        let (p, keys) = try NearMultisigTests().fixture(), s = try NearSendCrypto.sign(p, privateKeys: keys)
        let conflict = try LifecycleProvider(p, s)
        await conflict.configure(finalized: 1, wrongID: true)
        let result = try await client(conflict).submit(s, plan: p)
        XCTAssertEqual(result.outcome, .failed)
        let conflictingSent = await conflict.broadcasts(); XCTAssertTrue(conflictingSent.isEmpty)
        let changed = try LifecycleProvider(p, s)
        await changed.configure(finalized: 1, wrongRequest: true)
        do { _ = try await client(changed).submit(s, plan: p); XCTFail("Released a confirmation for a changed request") }
        catch { XCTAssertEqual(error as? NearSendError, .changed) }
        let changedSent = await changed.broadcasts(); XCTAssertTrue(changedSent.isEmpty)
    }
    func testExpiryRequiresUnusedPartNonce() async throws {
        let (p, keys) = try NearMultisigTests().fixture(), s = try NearSendCrypto.sign(p, privateKeys: keys)
        for completed in [0, 1, 2] {
            let nonce = try NearSendCrypto.multisigRaw(p)[completed].nonce
            for used in [false, true] {
                let provider = try LifecycleProvider(p, s)
                await provider.configure(finalized: completed, expired: true, nonce: used ? nonce : nonce - 1)
                let result = try await client(provider).submit(s, plan: p)
                XCTAssertEqual(result.outcome, used ? .unknown : .expired)
                let sent = await provider.broadcasts(); XCTAssertTrue(sent.isEmpty)
            }
        }
    }
    func testCancelledStatusReplyNeverReleasesNextPart() async throws {
        let (p, keys) = try NearMultisigTests().fixture(), s = try NearSendCrypto.sign(p, privateKeys: keys)
        let provider = try LifecycleProvider(p, s), c = try client(provider)
        await provider.configure(finalized: 1); await provider.armHold()
        let task = Task { try await c.submit(s, plan: p) }
        await provider.waitUntilHeld(); task.cancel(); await provider.release()
        do { _ = try await task.value; XCTFail("Cancelled reply continued submission") }
        catch { XCTAssertTrue(error is CancellationError) }
        let sent = await provider.broadcasts(); XCTAssertTrue(sent.isEmpty)
    }
    func testConcurrentReplaysOnlyBroadcastIdenticalAuthorizedPart() async throws {
        let (p, keys) = try NearMultisigTests().fixture(), s = try NearSendCrypto.sign(p, privateKeys: keys)
        let provider = try LifecycleProvider(p, s), c = try client(provider)
        async let first = c.submit(s, plan: p)
        async let second = c.submit(s, plan: p)
        let results = try await [first, second]
        XCTAssertTrue(results.allSatisfy { $0.outcome == .unknown })
        let sent = await provider.broadcasts()
        XCTAssertEqual(sent.count, 2); XCTAssertTrue(sent.allSatisfy { $0 == s.multisigParts![0].bytes })
    }
}
