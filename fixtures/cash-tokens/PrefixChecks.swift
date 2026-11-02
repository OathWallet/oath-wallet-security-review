import Foundation

@main struct PrefixChecks {
    struct Case: Decodable {
        let wire: Data
        let locking: Data?
    }

    static func main() throws {
        let corpus = try JSONDecoder().decode([Case].self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        var accepted = 0
        var rejected = 0
        for (index, vector) in corpus.enumerated() {
            for sliced in [false, true] {
                let bytes = sliced ? (Data([0x13]) + vector.wire).dropFirst() : vector.wire
                do {
                    let script = try BitcoinCashTokens.lockingScript(bytes)
                    guard let expected = vector.locking, expected == script else { fatalError("Unexpected decoded script in case " + String(index)) }
                    accepted += 1
                } catch BitcoinError.invalidResponse {
                    guard vector.locking == nil else { fatalError("Unexpected rejection in case " + String(index)) }
                    rejected += 1
                }
            }
        }
        print("accepted=\(accepted) rejected=\(rejected)")
    }
}
