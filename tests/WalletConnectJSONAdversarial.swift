import Foundation

@main struct WalletConnectJSONAdversarial {
    static func main() throws {
        var checks = 0, failures = 0
        func check(_ ok: Bool, _ label: String) {
            checks += 1
            if !ok { failures += 1; print("FAIL: \(label)") }
        }
        func rejects(_ raw: String, limit: Int = 1024) -> Bool {
            do { _ = try WalletConnectJSON.decode(Data(raw.utf8), collectionLimit: limit); return false }
            catch { return true }
        }
        check(rejects("{\"a\":0,\"b\":0,\"c\":0}", limit: 2), "Object members obey collectionLimit")
        check(rejects("[0,0,0]", limit: 2), "Array members obey collectionLimit")
        check(!rejects("{\"a\":0,\"b\":0}", limit: 2), "Exact object limit is accepted")
        check(!rejects("[0,0]", limit: 2), "Exact array limit is accepted")
        check(rejects("{\"a\":0,\"\\u0061\":1}"), "Escaped duplicate member is rejected")
        check(rejects(String(repeating: "[", count: 34) + "0" + String(repeating: "]", count: 34)), "Depth bound")
        check(rejects(String(repeating: " ", count: 65537)), "Byte bound")
        let huge = "115792089237316195423570985008687907853269984665640564039457584007913129639935"
        check(try WalletConnectJSON.decode(Data(huge.utf8)) == .number(huge), "uint256 numeric lexeme retained exactly")
        for raw in ["[true,]", "{\"a\":1,}", "01", "1.", "1e", "{}{}", "\"\\ud800\"", "\"\u{0}\""] {
            check(rejects(raw), "Malformed JSON rejected")
        }
        // Deterministic bounded differential corpus. No sockets, secrets or blockchain calls.
        var seed: UInt64 = 0x4f41544820261031
        func random() -> UInt64 { seed = seed &* 6364136223846793005 &+ 1442695040888963407; return seed }
        for _ in 0..<2000 {
            let value = Int(random() % 1_000_000)
            let object: [String: Any] = ["n":value, "s":"fixture-\(random())", "v":[true,false]]
            let data = try JSONSerialization.data(withJSONObject:object, options:.sortedKeys)
            let parsed = try WalletConnectJSON.decode(data)
            check(parsed["n"] == .number(String(value)), "Generated integer matches reference")
            check(parsed["s"].string == object["s"] as? String, "Generated string matches reference")
            var mutated = data
            mutated[Int(random() % UInt64(mutated.count))] = 0
            check((try? WalletConnectJSON.decode(mutated)) == nil, "NUL mutation is rejected")
        }
        print("\(checks) checks, \(failures) failures; corpus seed 0x4f41544820261031")
        if failures != 0 { exit(1) }
    }
}
