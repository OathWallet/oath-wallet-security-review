import Foundation

@main
struct PathChecks {
    static func main() throws {
        let mode = CommandLine.arguments[1]
        let canonical = "m/44'/0'/0'/0/0"
        let paths = ["standard": canonical, "short": "m/84'/0'/3'", "unknown": "m/42'/0'/0'/0/0",
                     "long": "m/44'/0'/0'/0/0/2147483647", "bits": "m/44/0'/0'/0'/0", "root": "m"]
        if let value = paths[mode] {
            guard let path = DerivationPath(value) else { exit(2) }
            let data = try JSONEncoder().encode(path)
            guard try JSONDecoder().decode(DerivationPath.self, from: data) == path else {
                print("Round-trip changed the derivation path")
                exit(1)
            }
            if mode == "standard" {
                let saved = try JSONDecoder().decode([String: UInt32].self, from: data)
                guard saved == ["purpose": 44, "coin": 0, "account": 0, "change": 0, "address": 0] else { exit(3) }
            }
        } else if ["negative", "wide", "bounds"].contains(mode) {
            guard let path = DerivationPath(canonical) else { exit(2) }
            let index = mode == "negative" ? -1 : (mode == "wide" ? Int(UInt32.max) + 1 : 5)
            guard path[index] == nil, path[4]?.value == 0 else { exit(3) }
        } else if mode == "legacy" {
            let data = Data(#"{"purpose":84,"coin":0,"account":9,"change":1,"address":6}"#.utf8)
            guard try JSONDecoder().decode(DerivationPath.self, from: data).description == "m/84'/0'/9'/1/6" else { exit(3) }
        } else if mode == "reject" {
            for value in [#"{"path":"m//3"}"#, #"{"path":"m/0/"}"#, #"{"path":"m/1","purpose":44}"#, #"{"path":null}"#] {
                do {
                    _ = try JSONDecoder().decode(DerivationPath.self, from: Data(value.utf8))
                    exit(3)
                } catch is DecodingError { }
            }
        } else { exit(2) }
        print("Passed", mode)
    }
}
