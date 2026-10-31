import Foundation

@main struct PairingLinkBoundary {
    enum Failure: Error { case assertion }
    @MainActor static func main() throws {
        let now = Date(timeIntervalSince1970: 1_800_000_000)
        let topic = String(repeating: "a", count: 64)
        let key = String(repeating: "b", count: 64)
        let base = "wc:\(topic)@2?symKey=\(key)&relay-protocol=irn&expiryTimestamp=4102444800"
        for suffix in ["&relay-data=%26symKey%3D" + String(repeating: "c", count: 64), "&relay-data=%2526symKey%253Dliteral"] {
            let raw = base + suffix
            guard case .walletConnect(let value) = OathScanParser.walletConnect(raw, now: now), value == raw,
                  let url = URL(string: raw), OathWalletLink.parse(url, now: now) == .pair(raw) else { throw Failure.assertion }
        }
        guard case .invalid = OathScanParser.walletConnect(base + "&symKey=duplicate", now: now) else { throw Failure.assertion }
        print("App pairing boundary: 5 assertions passed; encoded relay-data reaches the SDK unchanged; raw duplicate field rejected")
    }
}
