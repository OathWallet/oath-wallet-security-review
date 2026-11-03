import Foundation
import XCTest
@testable import OathAnkr

private actor ActivationProvider: AnkrTransport {
    enum Phase: Sendable { case absent, bootstrap, deployed, secured }
    let policy: NearMultisigPolicy
    let hash = SuiSendCrypto.base58(Data(repeating: 7, count: 32))
    var phase: Phase = .bootstrap
    var balance = "10000000000000000000000000"
    var gasPrice = "100000000"
    var nonce: UInt64 = 99
    var fault = ""
    var plan: NearSendPlan?
    var bundle: NearSignedSend?
    var final = false
    var broadcasts: [Data] = []
    var holdNext = false
    var held: CheckedContinuation<Void, Never>?
    var observer: CheckedContinuation<Void, Never>?
    init(_ policy: NearMultisigPolicy) { self.policy = policy }
    func set(_ phase: Phase, balance: String = "10000000000000000000000000", nonce: UInt64 = 99, gasPrice: String = "100000000", fault: String = "") {
        self.phase=phase;self.balance=balance;self.nonce=nonce;self.gasPrice=gasPrice;self.fault=fault
    }
    func register(_ plan: NearSendPlan, _ signed: NearSignedSend) { self.plan=plan;bundle=signed;final=false }
    func complete(_ next: Phase) { final=true;phase=next }
    func sent() -> [Data] { broadcasts }
    func armHold() { holdNext=true }
    func waitUntilHeld() async { if held != nil { return };await withCheckedContinuation { observer=$0 } }
    func release() { held?.resume();held=nil }
    private func envelope(_ result: NearJSON) throws -> (Data, Int) {
        (try JSONEncoder().encode(NearJSON.object(["jsonrpc":.string("2.0"),"id":.number("1"),"result":result])),200)
    }
    private func error(_ name: String, info: [String:NearJSON] = [:]) throws -> (Data, Int) {
        (try JSONEncoder().encode(NearJSON.object(["jsonrpc":.string("2.0"),"id":.number("1"),"error":.object(["cause":.object(["name":.string(name),"info":.object(info)])])])),200)
    }
    private func receipt() throws -> NearJSON {
        let p=try XCTUnwrap(plan),s=try XCTUnwrap(bundle),part=try XCTUnwrap(s.multisigParts?.first)
        let id=SuiSendCrypto.base58(Data(repeating:9,count:32)),terminal=NearJSON.object(["SuccessValue":.string("")])
        func outcome(_ id:String,_ children:[String],_ status:NearJSON)->NearJSON {
            .object(["id":.string(id),"block_hash":.string(hash),"outcome":.object(["executor_id":.string(p.sender),"tokens_burnt":.string("3"),"receipt_ids":.array(children.map(NearJSON.string)),"status":status])])
        }
        return .object(["transaction":.object(["hash":.string(part.hash),"signer_id":.string(p.sender),"receiver_id":.string(p.receiver),"public_key":.string(NearSendCrypto.keyString(part.publicKey)),"nonce":.number(String(p.nonce))]),"final_execution_status":.string("FINAL"),"status":terminal,"transaction_outcome":outcome(part.hash,[id],.object(["SuccessReceiptId":.string(id)])),"receipts_outcome":.array([outcome(id,[],terminal)])])
    }
    func send(_ request:URLRequest) async throws -> (Data,Int) {
        let call=try JSONDecoder().decode(NearJSON.self,from:XCTUnwrap(request.httpBody)),p=call["params"]
        switch call["method"].string {
        case "EXPERIMENTAL_protocol_config":return try envelope(.object(["chain_id":.string("testnet"),"transaction_validity_period":.number("86400"),"runtime_config":.object(["min_gas_purchase_price":.string("100000000"),"storage_amount_per_byte":.string("10000000000000000000")])]))
        case "gas_price":return try envelope(.object(["gas_price":.string(gasPrice)]))
        case "block":return try envelope(.object(["header":.object(["hash":.string(hash),"height":.number("100")])]))
        case "tx":
            XCTAssertEqual(p["wait_until"].string,"NONE")
            XCTAssertEqual(p["tx_hash"].string,bundle?.hash)
            return final ? try envelope(receipt()) : try error("UNKNOWN_TRANSACTION")
        case "broadcast_tx_async":
            let data=try XCTUnwrap(Data(base64Encoded:XCTUnwrap(p.array?.first?.string)))
            XCTAssertEqual(data,bundle?.bytes);broadcasts.append(data)
            return try envelope(.string(XCTUnwrap(bundle).hash))
        case "query":
            XCTAssertEqual(p["account_id"].string,policy.address);XCTAssertEqual(p["block_id"].string,hash)
            var fields:[String:NearJSON] = ["block_hash":.string(hash)]
            switch p["request_type"].string {
            case "view_account":
                if holdNext { holdNext=false;await withCheckedContinuation { held=$0;observer?.resume();observer=nil } }
                if phase == .absent { return try error("UNKNOWN_ACCOUNT",info:["requested_account_id":.string(policy.address)]) }
                fields["amount"] = .string(balance)
                fields["code_hash"] = .string(phase == .bootstrap ? String(repeating:"1",count:32):try NearMultisigPolicy.codeHash)
            case "view_access_key_list":
                let keyName=fault=="wrongBootstrap" ? NearSendCrypto.keyString(Data(repeating:12,count:32)):NearSendCrypto.keyString(policy.bootstrap)
                let permission:NearJSON=fault=="restrictedBootstrap" ? .object(["FunctionCall":.object([:])]):.string("FullAccess")
                let bootstrap=NearJSON.object(["public_key":.string(keyName),"access_key":.object(["nonce":.number(String(nonce)),"permission":permission])])
                var keys: [NearJSON] = phase == .bootstrap ? [bootstrap] : policy.publicKeys.map { key in
                    .object(["public_key":.string(NearSendCrypto.keyString(key)),"access_key":.object(["nonce":.number("99"),"permission":.object(["FunctionCall":.object(["allowance":.null,"receiver_id":.string(policy.address),"method_names":.array(NearMultisigPolicy.methods.map(NearJSON.string))])])])])
                }
                if phase == .deployed { keys.append(bootstrap) }
                if fault=="extraBootstrap" { keys.append(bootstrap) }
                fields["keys"] = .array(keys)
            case "call_function":
                let response:NearJSON
                switch p["method_name"].string {
                case "get_members":response = .array(policy.publicKeys.map { .object(["public_key":.string(NearSendCrypto.keyString($0))]) })
                case "get_num_confirmations":response = .number(String(policy.required))
                default:throw NearSendError.malformed
                }
                fields["result"] = .array(try JSONEncoder().encode(response).map { .number(String($0)) })
            default:throw NearSendError.malformed
            }
            return try envelope(.object(fields))
        default:throw NearSendError.malformed
        }
    }
}

final class NearAuditMultisigActivationTests:XCTestCase,@unchecked Sendable {
    private func fixture() throws -> (NearMultisigPolicy,ActivationProvider) {
        let (p,_)=try NearMultisigTests().fixture();let policy=try XCTUnwrap(p.multisig?.policy)
        return (policy,ActivationProvider(policy))
    }
    private func client(_ provider:ActivationProvider) throws -> NearSendClient {
        try NearSendClient(network:.testnet,endpoints:[URL(string:"https://activation.invalid")!],transport:provider)
    }
    func testMissingAndUnderfundedAccountsNeverProducePlan() async throws {
        let (policy,provider)=try fixture(),c=try client(provider)
        for phase:ActivationProvider.Phase in [.absent,.bootstrap,.deployed] {
            await provider.set(phase,balance:"0")
            let (state,plan)=try await c.multisigSetup(policy)
            XCTAssertFalse(state.configured);XCTAssertNil(plan);XCTAssertEqual(state.balance,"0")
            let reserve=try NearSendAmount.multiply("10000000000000000000",UInt64(NearMultisigPolicy.code().count+32768))
            let minimum=try NearSendAmount.add(reserve,NearSendAmount.add("40000000000000000000000","1"))
            XCTAssertEqual(state.minimumFunding,minimum)
        }
    }
    func testDeploymentAndBootstrapRemovalAreSeparateStages() async throws {
        let (policy,provider)=try fixture(),c=try client(provider)
        for (phase,stage):(ActivationProvider.Phase,NearMultisigContext.Stage) in [(.bootstrap,.deploy),(.deployed,.secure)] {
            await provider.set(phase)
            let (state,optional)=try await c.multisigSetup(policy),plan=try XCTUnwrap(optional)
            XCTAssertFalse(state.configured);XCTAssertEqual(state.stage,stage);XCTAssertEqual(plan.multisig?.stage,stage)
            XCTAssertEqual(plan.publicKey,policy.bootstrap);XCTAssertEqual(plan.nonce,100)
            let signed=try NearSendCrypto.sign(plan,privateKeys:[Data(repeating:99,count:32)])
            XCTAssertEqual(signed.multisigParts?.count,1);XCTAssertEqual(signed.publicKey,policy.bootstrap)
            XCTAssertNoThrow(try NearSendCrypto.verifyMultisig(signed,plan:plan))
        }
        await provider.set(.secured)
        let (ready,plan)=try await c.multisigSetup(policy)
        XCTAssertTrue(ready.configured);XCTAssertNil(ready.stage);XCTAssertNil(plan)
    }
    func testUnexpectedBootstrapAuthorityAndNonceAreRejected() async throws {
        let (policy,provider)=try fixture()
        for phase:ActivationProvider.Phase in [.bootstrap,.deployed] {
            for fault in ["wrongBootstrap","restrictedBootstrap","extraBootstrap","exhaustedNonce"] {
                await provider.set(phase,nonce:fault=="exhaustedNonce" ? UInt64.max:99,fault:fault)
                do { _=try await client(provider).multisigSetup(policy);XCTFail("Accepted bootstrap fault: \(phase) \(fault)") }
                catch { XCTAssertEqual(error as? NearSendError,.changed) }
            }
        }
    }
    func testPreflightRejectsChangedStageNonceCostOrFunding() async throws {
        let (policy,provider)=try fixture(),c=try client(provider)
        for phase:ActivationProvider.Phase in [.bootstrap,.deployed] {
            await provider.set(phase)
            let (_,optional)=try await c.multisigSetup(policy),plan=try XCTUnwrap(optional)
            for change in ["stage","nonce","cost","funding"] {
                await provider.set(change=="stage" ? .secured:phase,balance:change=="funding" ? "0":"10000000000000000000000000",nonce:change=="nonce" ? 100:99,gasPrice:change=="cost" ? "200000000":"100000000")
                do { try await c.preflight(plan);XCTFail("Accepted changed \(change)") }
                catch { XCTAssertEqual(error as? NearSendError,.changed) }
            }
        }
    }
    func testCancellationAfterHeldStateCannotReturnActivationPlan() async throws {
        let (policy,provider)=try fixture(),c=try client(provider)
        await provider.armHold()
        let task=Task { try await c.multisigSetup(policy) }
        await provider.waitUntilHeld();task.cancel();await provider.release()
        do { _=try await task.value;XCTFail("Late state bypassed cancellation") }
        catch { XCTAssertTrue(error is CancellationError) }
        let sent=await provider.sent();XCTAssertTrue(sent.isEmpty)
    }
    func testEachStageReconcilesOriginalSignatureBeforeNextSetup() async throws {
        let (policy,provider)=try fixture()
        var expected:[Data]=[]
        for (phase,next):(ActivationProvider.Phase,ActivationProvider.Phase) in [(.bootstrap,.deployed),(.deployed,.secured)] {
            await provider.set(phase)
            let (_,optional)=try await client(provider).multisigSetup(policy),plan=try XCTUnwrap(optional)
            let signed=try NearSendCrypto.sign(plan,privateKeys:[Data(repeating:99,count:32)])
            await provider.register(plan,signed)
            let submitted=try await client(provider).submit(signed,plan:plan)
            XCTAssertEqual(submitted.outcome,.unknown);expected.append(signed.bytes)
            await provider.complete(next)
            let restored=try JSONDecoder().decode(NearSignedSend.self,from:JSONEncoder().encode(signed))
            let restoredPlan=try JSONDecoder().decode(NearSendPlan.self,from:JSONEncoder().encode(plan))
            let confirmed=try await client(provider).status(restored,plan:restoredPlan)
            XCTAssertEqual(confirmed.outcome,.confirmed);XCTAssertEqual(confirmed.hash,signed.hash);XCTAssertEqual(confirmed.fee,"6")
            let sent=await provider.sent();XCTAssertEqual(sent,expected)
        }
        let (state,plan)=try await client(provider).multisigSetup(policy)
        XCTAssertTrue(state.configured);XCTAssertNil(plan)
    }
}
