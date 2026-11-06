import Foundation
import Darwin

// Diagnostic only. Never treats a failed baseline as passing.
@main
struct FileProtectionProbe {
    static func main() throws {
        let roots = [FileManager.default.temporaryDirectory,
                     URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)]
        var results = [[String: Any]]()
        for (index, root) in roots.enumerated() {
            let directory = root.appendingPathComponent("installation-probe-" + UUID().uuidString)
            defer { try? FileManager.default.removeItem(at: directory) }
            let store = OathInstallationKeyFile(directory: directory)
            do {
                try store.write(Data("public fixture".utf8))
                for (kind, original) in [("file",store.url),("directory",directory)] {
                    let fresh = URL(fileURLWithPath: original.path)
                    let values = try fresh.resourceValues(forKeys: [.isExcludedFromBackupKey, .volumeSupportsExtendedSecurityKey, .volumeNameKey])
                    let count = listxattr(fresh.path, nil, 0, 0)
                    var names = [CChar](repeating: 0, count: max(0, count))
                    let loaded = count > 0 ? listxattr(fresh.path, &names, names.count, 0) : count
                    let namesText = loaded > 0 ? names.map { UInt8(bitPattern:$0) }.split(separator:0).map { String(decoding:$0,as:UTF8.self) } : []
                    results.append(["root":index == 0 ? "default-temp" : "scratch", "kind":kind,
                        "backupExcluded":values.isExcludedFromBackup as Any? ?? NSNull(),
                        "xattrNames":namesText, "xattrReadResult":loaded])
                }
            } catch {
                results.append(["root":index == 0 ? "default-temp" : "scratch", "error":String(describing:error)])
            }
        }
        let data = try JSONSerialization.data(withJSONObject:results, options:[.prettyPrinted,.sortedKeys])
        print(String(decoding:data,as:UTF8.self))
    }
}
