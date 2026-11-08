import Foundation
import OathDatabase
import OathAnkr

// This fixture captures the released credential BEFORE waiting. Disabling or
// replacing enrollment cannot hide a stale reply by changing the test double.
actor HeldCredentialBiometrics: OathBiometricCredentialStoring {
    private var credential: Data?
    private var hold = false
    private var continuation: CheckedContinuation<Void, Never>?
    var isWaiting: Bool { continuation != nil }
    func enroll(_ value: Data) { credential = value }
    func pause() { hold = true }
    func release() { continuation?.resume(); continuation = nil }
    func hasEnrollment() -> Bool { credential != nil }
    func disable() { credential = nil }
    func read(reason: String) async throws -> Data {
        guard let captured = credential else { throw OathBiometricCredentialError.missing }
        if hold {
            hold = false
            // Intentionally cancellation-resistant, like an already released OS reply.
            await withCheckedContinuation { continuation = $0 }
        }
        return captured
    }
    func enableIfAvailable(strings: OathLocalizer,
        credentialProvider: (@Sendable () async throws -> Data)?) async -> OathBiometricSetupResult { .unavailable }
}

@main struct CheckWalletConnectAuthorization {
    @MainActor static func main() async throws {
        var passed = 0, failed = 0
        func check(_ value: Bool, _ name: String) {
            print("\(value ? "PASS" : "FAIL"): \(name)")
            if value { passed += 1 } else { failed += 1 }
        }
        let pin: [UInt8] = [1,2,3,4,5,6], replacement: [UInt8] = [6,5,4,3,2,1]
        for typed in [false,true] {
            for operation in ["unchanged", "lock and reopen", "rotate passcode", "disable biometrics", "disable passcode", "cancel", "switch wallet", "cross-wallet account"] {
                let prefix = "\(typed ? "typed" : "message") / \(operation)"
                let folder = FileManager.default.temporaryDirectory.appendingPathComponent("OathLateAuth-"+UUID().uuidString)
                defer { try? FileManager.default.removeItem(at:folder) }
                let db = try await OathDatabase.open(at:folder.appendingPathComponent("wallet.sqlite"))
                try await OathDataEnvironment.seed(db)
                let bio = HeldCredentialBiometrics()
                let vault = OathWalletVault(storage:WalletMemory(),biometricStore:bio,database:db)
                let key = Data(repeating:0,count:31)+Data([1])
                try await vault.create(digits:pin,importing:nil,privateKey:.init(bytes:key,networks:[.ethereum]))
                let target = try await vault.unlockedProfile().id
                let second = try await vault.addWallet(requestID:UUID(),importing:nil,privateKey:.init(bytes:Data(repeating:0,count:31)+Data([2]),networks:[.ethereum])).id
                _ = try await vault.selectWallet(target)
                let accounts = try await db.accounts(walletID:target.uuidString)
                let secondAccounts = try await db.accounts(walletID:second.uuidString)
                guard let account = accounts.first, let other = secondAccounts.first else { throw OathWalletError.unavailable }
                let message = Data("Oath delayed credential fixture".utf8)
                let payload = try WalletConnectTypedData(json:Data("""
                {"types":{"EIP712Domain":[{"name":"chainId","type":"uint256"}],"Note":[{"name":"contents","type":"string"}]},"primaryType":"Note","domain":{"chainId":1},"message":{"contents":"Oath delayed credential fixture"}}
                """.utf8),chainID:1,account:account.address)
                func sign(_ digits: [UInt8]?, wrongAccount: Bool = false) async throws -> String {
                    let accountID = wrongAccount ? other.id : account.id
                    if typed { return try await vault.signWalletConnectTypedData(walletID:target.uuidString,accountID:accountID,data:payload,digits:digits,reason:"Fixture") }
                    return try await vault.signWalletConnectMessage(walletID:target.uuidString,accountID:accountID,message:message,digits:digits,reason:"Fixture")
                }
                let expected = try typed ? payload.sign(privateKey:key,account:account.address) : OathWalletConnectMessage.sign(message,key:key,account:account.address)
                check(try await sign(pin)==expected,prefix+" initial signature")
                await bio.enroll(try await vault.biometricCredential())
                await bio.pause()
                let pending = Task { try await sign(nil,wrongAccount:operation == "cross-wallet account") }
                for _ in 0..<500 { if await bio.isWaiting { break }; try await Task.sleep(for:.milliseconds(10)) }
                guard await bio.isWaiting else { throw OathWalletError.unavailable }
                check(true,prefix+" captured credential held")
                switch operation {
                case "lock and reopen":
                    await vault.lock()
                    _ = try await vault.unlock(digits:pin)
                case "rotate passcode":
                    let grant = try await vault.authorizeSecurityChange(digits:pin)
                    try await vault.setPasscode(replacement,authorization:grant)
                case "disable biometrics": try await vault.disableBiometrics()
                case "disable passcode":
                    let grant = try await vault.authorizeSecurityChange(digits:pin)
                    try await vault.setPasscode(nil,authorization:grant)
                case "cancel": pending.cancel()
                case "switch wallet": _ = try await vault.selectWallet(second)
                default: break
                }
                await bio.release()
                do {
                    let signature = try await pending.value
                    check(["unchanged","switch wallet","rotate passcode"].contains(operation) && signature==expected,prefix+" delayed result")
                } catch {
                    let expectedError: Bool
                    switch operation {
                    case "lock and reopen", "cancel": expectedError = error is CancellationError
                    case "disable biometrics", "disable passcode": expectedError = error as? OathBiometricCredentialError == .missing
                    case "cross-wallet account": expectedError = error as? OathWalletError == .locked
                    default: expectedError = false
                    }
                    check(expectedError,prefix+" delayed result")
                }
                if operation == "rotate passcode" {
                    do { _ = try await sign(pin); check(false,prefix+" old passcode rejected") }
                    catch { check(error as? OathWalletError == .wrongPasscode,prefix+" old passcode rejected") }
                }
                check(try await sign(operation == "rotate passcode" ? replacement:pin)==expected,prefix+" fresh request remains usable")
            }
        }
        print("Late authentication checks: \(passed) passed, \(failed) failed")
        if failed>0 { exit(1) }
    }
}
