import Foundation
import OathCloudBackup

// Serialization-only synthetic fixtures. These identities are intentionally not
// cryptographically valid; the app's separate policy/key checks are not stubbed
// into this test or claimed as exercised here.
@main @MainActor enum MultisigRecoveryBoundary {
    static var checks = 0
    static let phrase = Array(repeating: "abandon", count: 11).joined(separator: " ") + " about"
    static func data(_ byte: UInt8, _ count: Int = 32) -> String {
        Data(repeating: byte, count: count).base64EncodedString()
    }
    static func require(_ condition: Bool, _ label: String) {
        checks += 1
        guard condition else { fatalError("Recovery boundary failed: " + label) }
    }
    static func encoded(_ value: [String: Any]) throws -> Data {
        try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
    }
    static func rejects(_ value: [String: Any], _ label: String) throws {
        let bytes = try encoded(value)
        require((try? JSONDecoder().decode(MultisigCredential.self, from: bytes)) == nil, label)
    }
    static func main() throws {
        for type in ["bitcoin", "tron", "solana", "xrpl", "stellar", "aptos", "sui", "near", "evm", "ton", "thorchain"] {
            var material: [String: Any] = ["version": 1, "required": 2]
            let addressLength = ["tron":34, "solana":44, "xrpl":34, "stellar":56][type]
            var signer1: [String: Any] = ["key": data(1)]
            var signer2: [String: Any] = ["mnemonic": phrase, "language":"english", "passphrase":" public fixture "]
            if type == "bitcoin" {
                signer1 = ["wif": "K" + String(repeating:"1", count:51)]
            } else if let addressLength {
                signer1["address"] = String(repeating:"A", count:addressLength)
                signer2["address"] = String(repeating:"B", count:addressLength)
                material["address"] = String(repeating:"C", count:addressLength)
                material[type == "solana" ? "createSeed" : "accountKey"] = data(3)
            } else if type == "evm" {
                signer1["address"] = "0x" + String(repeating:"a", count:40)
                signer2["address"] = "0x" + String(repeating:"b", count:40)
                material["address"] = "0x" + String(repeating:"c", count:40)
                material["network"] = "ethereum"
                material["salt"] = data(4); material["executorKey"] = data(3)
            } else {
                signer1["publicKey"] = type == "thorchain" ? (Data([2]) + Data(repeating:1,count:32)).base64EncodedString() : data(1)
                signer2["publicKey"] = type == "thorchain" ? (Data([3]) + Data(repeating:2,count:32)).base64EncodedString() : data(2)
                switch type {
                case "near": material["address"] = String(repeating:"c",count:64); material["bootstrapSeed"] = data(3)
                case "ton": material["address"] = "0:" + String(repeating:"c",count:64)
                case "thorchain": material["address"] = "thor1" + String(repeating:"c",count:38)
                default: material["address"] = "0x" + String(repeating:"c",count:64)
                }
            }
            material["signers"] = [signer1, signer2]
            let document: [String: Any] = ["format":"oath.wallet.multisig-credential", "version":1, "type":type, "material":material]
            let credential = try JSONDecoder().decode(MultisigCredential.self, from: encoded(document))
            require(credential.isValid && credential.required == 2 && credential.signers.count == 2, type + " valid shape")
            require(credential.signers.map(\.number) == [1,2], type + " original order")
            require(credential.signers[1].mnemonic == phrase && credential.signers[1].passphrase == " public fixture ", type + " material preserved")
            let roundTrip = try JSONDecoder().decode(MultisigCredential.self, from: JSONEncoder().encode(credential))
            require(roundTrip == credential, type + " round trip")
            var bad = document; bad["version"] = 2; try rejects(bad, type + " outer version")
            bad = document; bad["format"] = "other"; try rejects(bad, type + " format")
            bad = document; bad["type"] = "unsupported"; try rejects(bad, type + " type")
            for threshold in [0, -1, 3, Int.max] {
                var invalid = material; invalid["required"] = threshold
                bad = document; bad["material"] = invalid; try rejects(bad, type + " threshold")
            }
            var invalid = material; invalid["version"] = 0
            bad = document; bad["material"] = invalid; try rejects(bad, type + " inner version")
            invalid = material; invalid["signers"] = [signer1]
            bad = document; bad["material"] = invalid; try rejects(bad, type + " signer count")
            var ambiguous = signer1; ambiguous["mnemonic"] = phrase; ambiguous["language"] = "english"
            invalid = material; invalid["signers"] = [ambiguous,signer2]
            bad = document; bad["material"] = invalid; try rejects(bad, type + " ambiguous signer")
            var oversized = signer2; oversized["mnemonic"] = String(repeating:"a",count:16_384)
            invalid = material; invalid["signers"] = [signer1,oversized]
            bad = document; bad["material"] = invalid; try rejects(bad, type + " mnemonic bound")
            oversized = signer2; oversized["passphrase"] = String(repeating:"a",count:257)
            invalid = material; invalid["signers"] = [signer1,oversized]
            bad = document; bad["material"] = invalid; try rejects(bad, type + " passphrase bound")
            oversized = signer2; oversized["passphrase"] = "public\u{0}fixture"
            invalid = material; invalid["signers"] = [signer1,oversized]
            bad = document; bad["material"] = invalid; try rejects(bad, type + " embedded NUL")
            if type != "bitcoin" {
                invalid = material; invalid["signers"] = [signer1,signer1]
                bad = document; bad["material"] = invalid; try rejects(bad, type + " duplicate identity")
            }
        }
        print("MULTISIG_RECOVERY_OK families=11 checks=\(checks) scope=serialization")
    }
}
