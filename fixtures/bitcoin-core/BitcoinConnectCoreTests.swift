import Foundation
import XCTest
@testable import OathBitcoin

/// Addresses use the WalletConnect signet encoding. Core funds and checks the
/// same output scripts on a peerless regtest chain owned by this one process.
final class BitcoinConnectCoreTests: XCTestCase, BitcoinConnectFixture, @unchecked Sendable {
    func testConfirmedWalletConnectSignatures() async throws {
        guard let directory = ProcessInfo.processInfo.environment["OATH_CONNECT_REGTEST_DIR"] else {
            throw XCTSkip("Dedicated local regression chain required")
        }
        let rpc = LocalCore(directory: directory)
        let mining = try await rpc.string("getnewaddress", [])
        _ = try await rpc.call("generatetoaddress", [101, mining])
        var rejected = [Int]()
        for type in BitcoinAddressType.allCases {
            let own = try address(type)
            let funded = try await rpc.string("sendtoaddress", [BitcoinSendPlan.address(own, on: .regtest), 0.001])
            _ = try await rpc.call("generatetoaddress", [1, mining])
            let hex = try await rpc.string("getrawtransaction", [funded])
            let raw = try XCTUnwrap(Data(hex: hex))
            let outputs = try BitcoinTransactions.details(raw, network: .bitcoin).outputs
            let index = try XCTUnwrap(outputs.firstIndex { $0.script == own.script })
            let c = BitcoinSendCoin(accountID: "fixture", txid: funded, vout: index, value: outputs[index].value,
                                    address: own, previousTransaction: raw)
            let approved = try plan([c])
            var proposal = try BitcoinConnectPSBT(approved.psbt)
            if type == .nativeSegwit || type == .taproot {
                let different = try plan([c], request: request(extra: ["amount":"10001"]))
                let unrelated = try BitcoinConnectSigning.sign(different, source: .seed(seed, account: 0))
                let witness = try XCTUnwrap(BitcoinConnectPSBT(unrelated.psbt).field(8, input: 0))
                if type == .taproot {
                    proposal.set(0x13, Data(witness.dropFirst(2)), input: 0)
                } else {
                    let sig = witness.subdata(in: 2..<(2 + Int(witness[1])))
                    proposal.maps[1].append(.init(key: Data([2]) + witness.suffix(33), value: sig))
                }
            }
            let packet = try proposal.encoded
            let req = try request("signPsbt", extra: ["psbt": packet, "broadcast": true, "signInputs": approved.inputs.map {
                ["address": $0.address, "index": $0.index] as [String: Any]
            }])
            let checked = try BitcoinConnectSigning.review(request:req, psbt:packet, inputs:approved.inputs,
                addresses:approved.reviewedAddresses, previous:[funded: raw])
            let value = try BitcoinConnectSigning.sign(checked, source: .seed(seed, account: 0))
            try BitcoinConnectSigning.verify(value, plan: checked)
            let signedHex = try XCTUnwrap(value.raw).hex
            let verdict = try await rpc.call("testmempoolaccept", [[signedHex]])
            let row = try XCTUnwrap((verdict as? [[String: Any]])?.first)
            guard row["allowed"] as? Bool == true else {
                print("Rejected by Core: \(type.rawValue), \(row["reject-reason"] as? String ?? "reason unavailable")")
                rejected.append(type.rawValue)
                continue
            }
            let id = try await rpc.string("sendrawtransaction", [signedHex])
            XCTAssertEqual(id, value.txid)
            _ = try await rpc.call("generatetoaddress", [1, mining])
            let receipt = try await rpc.call("getrawtransaction", [id,true])
            XCTAssertGreaterThan(try XCTUnwrap((receipt as? [String:Any])?["confirmations"] as? Int), 0)
            print("Bitcoin Core accepted and mined WalletConnect \(type.rawValue)")
        }
        if !rejected.isEmpty {
            let kinds = rejected.sorted().map(String.init).joined(separator: ",")
            XCTFail("Bitcoin Core rejected wallet signatures for \(kinds)")
        }
    }
}

private struct LocalCore {
    let directory: String
    func string(_ method: String, _ params: [Any]) async throws -> String {
        let result = try await call(method,params); return try XCTUnwrap(result as? String)
    }
    func call(_ method: String, _ params: [Any]) async throws -> Any {
        let cookie = try String(contentsOfFile: directory + "/regtest/.cookie", encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines)
        var r = URLRequest(url: URL(string: "http://127.0.0.1:19743/wallet/oath-connect-proof")!)
        r.httpMethod="POST"; r.timeoutInterval=90
        r.setValue("Basic " + Data(cookie.utf8).base64EncodedString(), forHTTPHeaderField:"Authorization")
        r.httpBody = try JSONSerialization.data(withJSONObject:["jsonrpc":"2.0","id":1,"method":method,"params":params])
        let (data,_) = try await URLSession.shared.data(for:r)
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with:data) as? [String:Any])
        if let error = json["error"] as? [String:Any] {
            throw NSError(domain:"AuditCore."+method,code:error["code"] as? Int ?? -1)
        }
        return try XCTUnwrap(json["result"])
    }
}
