import Foundation
import OathDatabase
import OathAnkr

// Public synthetic keys only; actual vault, encrypted envelope, GRDB, EVM
// imported-key signing and typed-data implementations. No OS credential store.
@main struct CheckWalletConnectAuthorization {
    @MainActor static func main() async throws {
        var passed = 0, failed = 0
        func check(_ value: Bool, _ name: String) {
            print("\(value ? "PASS" : "FAIL"): \(name)")
            if value { passed += 1 } else { failed += 1 }
        }
        let pin: [UInt8] = [1,2,3,4,5,6]
        for typed in [false,true] {
            for operation in ["soft removal","permanent removal","remove and restore","other wallet removal","failed save","lock"] {
                let prefix = "\(typed ? "typed" : "message") / \(operation)"
                let folder = FileManager.default.temporaryDirectory.appendingPathComponent("OathRemovalAuth-"+UUID().uuidString)
                defer { try? FileManager.default.removeItem(at:folder) }
                let db = try await OathDatabase.open(at:folder.appendingPathComponent("wallet.sqlite"))
                try await OathDataEnvironment.seed(db)
                let storage = WalletMemory(), bio = MemoryBiometrics()
                let vault = OathWalletVault(storage:storage,biometricStore:bio,database:db)
                let key = Data(repeating:0,count:31)+Data([1])
                try await vault.create(digits:pin,importing:nil,privateKey:.init(bytes:key,networks:[.ethereum]))
                let target = try await vault.unlockedProfile().id.uuidString
                let second = try await vault.addWallet(requestID:UUID(),importing:nil,privateKey:.init(bytes:Data(repeating:0,count:31)+Data([2]),networks:[.ethereum])).id.uuidString
                let account = try await db.accounts(walletID:target).first!
                let message = Data("Oath delayed authorization fixture".utf8)
                let payload = try WalletConnectTypedData(json:Data("""
                {"types":{"EIP712Domain":[{"name":"chainId","type":"uint256"}],"Note":[{"name":"contents","type":"string"}]},"primaryType":"Note","domain":{"chainId":1},"message":{"contents":"Oath delayed authorization fixture"}}
                """.utf8),chainID:1,account:account.address)
                func sign(_ digits: [UInt8]?) async throws -> String {
                    if typed { return try await vault.signWalletConnectTypedData(walletID:target,accountID:account.id,data:payload,digits:digits,reason:"Fixture") }
                    return try await vault.signWalletConnectMessage(walletID:target,accountID:account.id,message:message,digits:digits,reason:"Fixture")
                }
                let expected = try typed ? payload.sign(privateKey:key,account:account.address) : OathWalletConnectMessage.sign(message,key:key,account:account.address)
                check(try await sign(pin)==expected,prefix+" initial signature")
                await bio.enroll(try await vault.biometricCredential())
                await bio.pauseNextRead()
                let pending = Task { try await sign(nil) }
                for _ in 0..<1000 { if await bio.isWaiting { break }; await Task.yield() }
                guard await bio.isWaiting else { throw OathWalletError.unavailable }
                check(true,prefix+" authentication held")
                if operation == "lock" { await vault.lock() }
                else {
                    let action = OathWalletRemovalAction(ids:[operation == "other wallet removal" ? second:target],permanently:false)
                    let grant = try await vault.authorizeWalletRemoval(action,digits:pin,reason:"Fixture")
                    if operation == "failed save" {
                        storage.rejectNextUpdate()
                        do { _ = try await vault.removeWallets(action,authorization:grant);check(false,prefix+" expected save failure") }
                        catch { check(error as? OathWalletError == .unavailable,prefix+" expected save failure") }
                    } else {
                        _ = try await vault.removeWallets(action,authorization:grant)
                        if operation == "permanent removal" {
                            let purge = OathWalletRemovalAction(ids:[target],permanently:true)
                            let approval = try await vault.authorizeWalletRemoval(purge,digits:pin,reason:"Fixture")
                            _ = try await vault.removeWallets(purge,authorization:approval)
                        } else if operation == "remove and restore" { _ = try await vault.recoverDeletedWallets([target]) }
                    }
                }
                let shouldSign = ["remove and restore","other wallet removal","failed save"].contains(operation)
                await bio.releaseRead()
                do { let signature = try await pending.value;check(shouldSign && signature==expected,prefix+" delayed result") }
                catch { check(!shouldSign && (error is CancellationError || error as? OathWalletError == .locked),prefix+" delayed result") }
            }
        }
        print("Removal authentication checks: \(passed) passed, \(failed) failed")
        if failed>0 { exit(1) }
    }
}
