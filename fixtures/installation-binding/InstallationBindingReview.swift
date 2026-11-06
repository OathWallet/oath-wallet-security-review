import Foundation
import CryptoKit

private enum Injected: Error { case denied }
private final class Store: OathInstallationKeyStoring, OathInstallationCredentialClearing, @unchecked Sendable {
    private let lock = NSLock()
    private var key: Data?
    private var clears = 0
    private var writes = 0
    private var denied = false
    func read() throws -> Data? { try lock.withLock { if denied { throw Injected.denied }; return key } }
    func write(_ value: Data) throws { lock.withLock { key = value; writes += 1 } }
    func clear() throws { lock.withLock { clears += 1 } }
    func failReads(_ value: Bool) { lock.withLock { denied = value } }
    func replace(_ value: Data?) { lock.withLock { key = value } }
    var counts: [Int] { lock.withLock { [clears, writes] } }
    var security: OathInstallationSecurity { .init(keys: self, credentials: self) }
}

@main struct InstallationBindingReview {
    static func main() throws {
        let onlyPurpose = CommandLine.arguments.contains("--purpose-only")
        var results: [[String: Any]] = []
        var passed = 0, failed = 0
        func check(_ name: String, _ value: Bool) {
            results.append(["case": name, "passed": value])
            if value { passed += 1 } else { failed += 1 }
        }
        func rejects(_ name: String, _ operation: () throws -> Void) {
            do { try operation(); check(name, false) } catch { check(name, true) }
        }
        func edit(_ original: Data, _ changes: (inout [String: Any]) -> Void) throws -> Data {
            var body = try JSONSerialization.jsonObject(with: original) as! [String: Any]
            changes(&body)
            return try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        }
        let contexts = ["vault:vault-v1", "vault:unlock-attempts-v1", "biometric:synthetic", "passcode:synthetic"]
        let payload = Data((0..<256).map(UInt8.init))
        let store = Store(), security: OathInstallationSecurity
        security = store.security
        try security.prepare()
        let records = try contexts.map { try security.seal(payload, context: $0) }
        for i in contexts.indices {
            for j in contexts.indices where i != j {
                rejects("purpose-\(i)-\(j)") { _ = try security.open(records[i], context: contexts[j]) }
            }
        }
        if !onlyPurpose {
            for i in contexts.indices {
                check("roundtrip-\(i)", try security.open(records[i], context: contexts[i]) == payload)
                for altered in [contexts[i] + "\0", contexts[i] + " ", contexts[i].uppercased()] {
                    rejects("exact-purpose-\(i)-\(altered.debugDescription)") { _ = try security.open(records[i], context: altered) }
                }
            }
            let original = records[0]
            let body = try JSONSerialization.jsonObject(with: original) as! [String: Any]
            let sealed = Data(base64Encoded: body["sealed"] as! String)!
            for offset in sealed.indices {
                for bit in 0..<8 {
                    var changed = sealed; changed[offset] ^= UInt8(1 << bit)
                    let damaged = try edit(original) { $0["sealed"] = changed.base64EncodedString() }
                    rejects("sealed-bit-\(offset)-\(bit)") { _ = try security.open(damaged, context: contexts[0]) }
                }
            }
            for count in 0..<sealed.count {
                let shortened = try edit(original) { $0["sealed"] = sealed.prefix(count).base64EncodedString() }
                rejects("truncated-\(count)") { _ = try security.open(shortened, context: contexts[0]) }
            }
            for version in [-1, 0, 2, Int.max] {
                let altered = try edit(original) { $0["version"] = version }
                rejects("version-\(version)") { _ = try security.open(altered, context: contexts[0]) }
            }
            for value in ["00000000-0000-0000-0000-000000000000", "invalid", ""] {
                let altered = try edit(original) { $0["installationID"] = value }
                rejects("installation-id-\(value)") { _ = try security.open(altered, context: contexts[0]) }
            }
            for size in [0, 1, 31, 32, 4096] {
                let value = Data(repeating: 0x5a, count: size)
                let saved = try security.seal(value, context: contexts[0])
                check("length-\(size)", try security.open(saved, context: contexts[0]) == value)
            }
            let before = store.counts
            store.failReads(true)
            rejects("read-denied-prepare") { try security.prepare() }
            rejects("read-denied-open") { _ = try security.open(original, context: contexts[0]) }
            rejects("read-denied-seal") { _ = try security.seal(payload, context: contexts[0]) }
            check("read-denied-no-erasure-or-write", store.counts == before)
            store.failReads(false)
            check("read-recovery-preserves-ciphertext", try security.open(original, context: contexts[0]) == payload)
            let key = try store.read()!
            let keyObject = try JSONSerialization.jsonObject(with: key) as! [String: Any]
            let keyBytes = Data(base64Encoded: keyObject["key"] as! String)!
            for i in keyBytes.indices {
                var changed = keyBytes; changed[i] ^= 1
                store.replace(try edit(key) { $0["key"] = changed.base64EncodedString() })
                rejects("wrong-key-\(i)") { _ = try security.open(original, context: contexts[0]) }
            }
            store.replace(key)
            let other = Store().security
            for i in contexts.indices {
                rejects("other-installation-\(i)") { _ = try other.open(records[i], context: contexts[i]) }
            }
            try security.reset()
            for i in contexts.indices {
                rejects("reset-revokes-\(i)") { _ = try security.open(records[i], context: contexts[i]) }
                let current = try security.seal(payload, context: contexts[i])
                check("reset-fresh-\(i)", try security.open(current, context: contexts[i]) == payload)
            }
            check("reset-rotates-key", try store.read() != key)
            let concurrentStore = Store(), concurrent: OathInstallationSecurity
            concurrent = concurrentStore.security
            DispatchQueue.concurrentPerform(iterations: 64) { _ in try! concurrent.prepare() }
            check("concurrent-prepare-single-key", concurrentStore.counts == [1, 1])
        }
        let output: [String: Any] = ["passed": passed, "failed": failed, "skipped": 0, "cases": results]
        print(String(data: try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]), encoding: .utf8)!)
        if failed != 0 { exit(1) }
    }
}
