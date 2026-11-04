import Foundation
import XCTest
import CryptoKit
import stellarsdk
@testable import OathAnkr

actor StellarProviderReviewTransport: AnkrTransport {
    let base: StellarTransportFixture
    let sender: String, recipient: String, contract: String
    var target = "", field = "", replacement: StellarJSON = .null
    var simulationFault = ""
    var simulations = [String]()
    init(sender: String, recipient: String, issuer: String, contract: String) {
        self.sender = sender; self.recipient = recipient; self.contract = contract
        base = StellarTransportFixture(sender: sender, recipient: recipient, issuer: issuer)
    }
    func inject(_ target: String, _ field: String, _ value: StellarJSON) { self.target = target; self.field = field; replacement = value }
    func fault(_ value: String) { simulationFault = value }
    func send(_ request: URLRequest) async throws -> (Data, Int) {
        let path = request.url!.path
        if request.httpMethod == "POST", !path.hasSuffix("transactions_async"), let body = request.httpBody {
            let json = try JSONDecoder().decode(StellarJSON.self, from: body)
            if json["method"].string == "simulateTransaction" {
                let encoded = try XCTUnwrap(json["params"]["transaction"].string)
                let raw = try XCTUnwrap(Data(base64Encoded: encoded))
                let envelope = try XDRDecoder.decode(TransactionEnvelopeXDR.self, data: raw)
                guard case .v1(let e) = envelope,
                      let operation = e.tx.operations.first,
                      case .invokeHostFunctionOp(let op) = operation.body,
                      case .invokeContract(let call) = op.hostFunction else { throw StellarSendError.malformed }
                let function = call.functionName
                simulations.append(function)
                var result: [String: StellarJSON] = ["latestLedger": .number("100")]
                if function == "balance" {
                    // SCV_I128(10), high=0, low=1,000,000; independently packed fixture bytes.
                    result["results"] = .array([.object(["xdr": .string(Data([0,0,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,15,66,64]).base64EncodedString())])])
                } else if function == "decimals" {
                    result["results"] = .array([.object(["xdr": .string(Data([0,0,0,3,0,0,0,6]).base64EncodedString())])])
                } else if function == "transfer" {
                    // Independently encoded empty footprint, three resource limits and a 1000-stroop fee.
                    let resources = Data([0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,1, 0,0,0,1, 0,0,0,1, 0,0,0,0,0,0,3,232])
                    let invocation = SorobanAuthorizedInvocationXDR(function: .contractFn(call), subInvocations: [])
                    let auth = SorobanAuthorizationEntryXDR(credentials: .sourceAccount, rootInvocation: invocation)
                    var authBytes = try Data(XDREncoder.encode(auth))
                    if simulationFault == "changedAuthorization" { authBytes[authBytes.count - 5] ^= 1 }
                    result["transactionData"] = .string(resources.base64EncodedString())
                    result["minResourceFee"] = .string("1000")
                    result["results"] = .array([.object(["auth": .array([.string(authBytes.base64EncodedString())])])])
                    switch simulationFault {
                    case "restore": result["restorePreamble"] = .object([:])
                    case "error": result["error"] = .string("SYNTHETIC_UNTRUSTED_SIMULATION_DETAIL")
                    case "oldLedger": result["latestLedger"] = .number("99")
                    case "futureLedger": result["latestLedger"] = .number("125")
                    case "missingData": result["transactionData"] = .null
                    case "trailingData": result["transactionData"] = .string((resources + Data([0,0,0,0])).base64EncodedString())
                    case "feeUnderstated": result["minResourceFee"] = .string("1001")
                    case "feeExcessive": result["minResourceFee"] = .string("10000001")
                    case "missingAuth": result["results"] = .array([.object(["auth": .array([])])])
                    case "extraAuth": result["results"] = .array([.object(["auth": .array([.string(authBytes.base64EncodedString()), .string(authBytes.base64EncodedString())])])])
                    case "extraResult": result["results"] = .array([.object([:]), .object([:])])
                    default: break
                    }
                } else { throw StellarSendError.malformed }
                return (try JSONEncoder().encode(StellarJSON.object(["result": .object(result)])), 200)
            }
        }
        let (data, status) = try await base.send(request)
        var value = try JSONDecoder().decode(StellarJSON.self, from: data)
        if target == "sender", path.hasSuffix("/accounts/" + sender), var fields = value.fields {
            fields[field] = replacement; value = .object(fields)
        } else if target == "root", request.httpMethod != "POST", path.isEmpty || path == "/", var fields = value.fields {
            fields[field] = replacement; value = .object(fields)
        } else if target == "ledger", path.hasSuffix("/ledgers"), var row = value["_embedded"]["records"].array?.first?.fields {
            row[field] = replacement; value = .object(["_embedded": .object(["records": .array([.object(row)])])])
        }
        return (try JSONEncoder().encode(value), status)
    }
}

final class StellarProviderReviewTests: XCTestCase {
    let key = Data(repeating: 21, count: 32)
    func fixture() throws -> (StellarSendClient, StellarProviderReviewTransport, String, String, String) {
        let a = try StellarSendCrypto.address(privateKey: key)
        let b = try StellarSendCrypto.address(privateKey: Data(repeating: 22, count: 32))
        let i = try StellarSendCrypto.address(privateKey: Data(repeating: 23, count: 32))
        let contract = StellarIdentity.encode(Array(repeating: 55, count: 32), version: 16)
        let t = StellarProviderReviewTransport(sender: a, recipient: b, issuer: i, contract: contract)
        return (try StellarSendClient(network: .testnet, transport: t), t, a, b, contract)
    }
    func testMalformedStateNeverProducesAQuoteOrBroadcast() async throws {
        let (control, _, sender, recipient, _) = try fixture()
        let valid = try await control.quote(sender: sender, recipient: recipient, reference: "native", decimals: 7, amount: "1")
        XCTAssertEqual(valid.kind, .payment)
        XCTAssertEqual(valid.amount, "1")
        let signed = try StellarSendCrypto.sign(valid, privateKey: key)
        try StellarSendCrypto.verify(signed, plan: valid)
        let cases: [(String, String, StellarJSON)] = [
            ("root", "history_latest_ledger", .number("4294967295")),
            ("root", "history_latest_ledger", .number("0")),
            ("root", "history_elder_ledger", .number("0")),
            ("root", "network_passphrase", .string("untrusted-network")),
            ("ledger", "sequence", .number("99")), ("ledger", "sequence", .number("104")),
            ("ledger", "base_reserve_in_stroops", .number("0")),
            ("ledger", "base_reserve_in_stroops", .number("100000001")),
            ("ledger", "base_fee_in_stroops", .number("0")),
            ("ledger", "base_fee_in_stroops", .number("10000001")),
            ("ledger", "closed_at", .string("1970-01-01T00:00:00Z")),
            ("ledger", "closed_at", .string("invalid")),
            ("sender", "sequence", .string("9223372036854775807")),
            ("sender", "sequence", .string("-1")),
            ("sender", "subentry_count", .number("18446744073709551615")),
            ("sender", "num_sponsoring", .number("18446744073709551615")),
            ("sender", "num_sponsored", .number("6")),
            ("sender", "balances", .array([])),
            ("sender", "signers", .array([])),
            ("sender", "thresholds", .object(["med_threshold": .number("2")]))]
        for (target, field, value) in cases {
            let (c,t,a,b,_) = try fixture(); await t.inject(target,field,value)
            do { _ = try await c.quote(sender:a,recipient:b,reference:"native",decimals:7,amount:"1"); XCTFail("Accepted \(target).\(field)") }
            catch { XCTAssertFalse(String(describing:error).contains("untrusted-network")) }
            let writes = await t.base.writes; XCTAssertTrue(writes.isEmpty)
        }
        XCTAssertEqual(cases.count,20)
    }
    func testContractSimulationBindsSDKAuthorizationAndExactAmounts() async throws {
        let (c,t,a,b,contract) = try fixture()
        for maximum in [false,true] {
            let p = try await c.quote(sender:a,recipient:b,reference:contract,decimals:6,amount:"123",maximum:maximum)
            XCTAssertEqual(p.kind,.contract); XCTAssertEqual(p.amount,maximum ? "1000000":"123")
            XCTAssertEqual(p.assetBalance,"1000000"); XCTAssertEqual(p.fee,1120)
            XCTAssertEqual(p.authorization.count,1)
            let signed = try StellarSendCrypto.sign(p,privateKey:key); try StellarSendCrypto.verify(signed,plan:p)
            let envelope = try XDRDecoder.decode(TransactionEnvelopeXDR.self,data:signed.bytes)
            guard case .v1(let e) = envelope else { return XCTFail() }
            XCTAssertEqual(e.tx.operations.count,1)
            let writes = await t.base.writes; XCTAssertTrue(writes.isEmpty)
        }
        let calls = await t.simulations
        XCTAssertEqual(calls.filter{$0 == "balance"}.count,2); XCTAssertEqual(calls.filter{$0 == "decimals"}.count,2); XCTAssertEqual(calls.filter{$0 == "transfer"}.count,2)
    }
    func testMalformedContractSimulationsCannotReachSigning() async throws {
        let faults = ["changedAuthorization","restore","error","oldLedger","futureLedger","missingData","trailingData","feeUnderstated","feeExcessive","missingAuth","extraAuth","extraResult"]
        for fault in faults {
            let (c,t,a,b,contract) = try fixture(); await t.fault(fault)
            do { _ = try await c.quote(sender:a,recipient:b,reference:contract,decimals:6,amount:"123"); XCTFail("Accepted \(fault)") }
            catch { XCTAssertFalse(String(describing:error).contains("SYNTHETIC_UNTRUSTED_SIMULATION_DETAIL")) }
            let calls = await t.simulations
            XCTAssertTrue(calls.contains("transfer"), "Must reach injected fault: \(fault)")
            let writes = await t.base.writes; XCTAssertTrue(writes.isEmpty)
        }
    }
    func testContractMultisigCannotUseBootstrapOrForeignKeys() async throws {
        let (c,t,a,b,contract) = try fixture()
        let keys = [Data(repeating: 31,count:32),Data(repeating:32,count:32)]
        let policy = try StellarMultisigPolicy(account:a,required:2,signers:keys.map{try StellarSendCrypto.address(privateKey:$0)})
        await t.base.multisig(policy)
        let p = try await c.quote(sender:a,recipient:b,reference:contract,decimals:6,amount:"123",multisig:policy)
        let signed = try StellarSendCrypto.sign(p,privateKeys:keys); try StellarSendCrypto.verify(signed,plan:p)
        XCTAssertThrowsError(try StellarSendCrypto.sign(p,privateKey:key))
        XCTAssertThrowsError(try StellarSendCrypto.sign(p,privateKeys:[keys[0],key]))
        await t.base.multisig(nil)
        let receipt = try await c.submit(signed,plan:p,reconcileFirst:false)
        XCTAssertEqual(receipt.outcome,.unknown)
        let writes = await t.base.writes; XCTAssertTrue(writes.isEmpty)
    }
}
