import Foundation
import OathDatabase
import OathAnkr

/// Real production vault/passcode/journal and imported-key signer. Only the
/// OS biometric store and HD derivation are host fixtures; no app or network.
@main struct CheckTonSendAuthorization {
    @MainActor static func main() async throws {
        var checks = 0
        func check(_ value:Bool,_ reason:String) { precondition(value,reason); checks += 1 }
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent("TonVault-"+UUID().uuidString)
        defer { try? FileManager.default.removeItem(at:folder) }
        let db = try await OathDatabase.open(at:folder.appendingPathComponent("wallet.sqlite"))
        try await OathDataEnvironment.seed(db)
        let biometrics = MemoryBiometrics()
        let vault = OathWalletVault(storage:WalletMemory(),biometricStore:biometrics,database:db)
        let pin:[UInt8] = [1,2,3,4,5,6]
        try await vault.create(digits:pin,importing:nil,privateKey:.init(bytes:Data(repeating:7,count:32),networks:[.ton]))
        let profile = try await vault.unlockedProfile()
        let account = try await db.accounts(walletID:profile.id.uuidString).first!
        let plan = TonSendPlan(network:.mainnet,sender:account.address,recipient:try TonSendCrypto.address(publicKey:TonSendCrypto.publicKey(privateKey:Data(repeating:8,count:32))),reference:"native",publicKey:try TonSendCrypto.publicKey(privateKey:Data(repeating:7,count:32)),decimals:9,
            requestedAmount:1000,amount:1000,assetBalance:100000000,nativeBalance:100000000,sequence:0,expiration:UInt32(Date.now.timeIntervalSince1970)+300,deploy:true,bounce:false,fee:1_000_000,feeReserve:2_000_000,attached:1000)
        let quote = OathTonQuote(walletID:profile.id.uuidString,accountID:account.id,assetID:"ton:native",plan:plan)
        let now = Date.now.timeIntervalSince1970
        try await db.saveDraft(.init(id:"send",walletID:quote.walletID,accountID:account.id,networkID:"ton",assetID:quote.assetID,idempotencyKey:"send",recipient:plan.recipient,amountAtomic:String(plan.amount),state:"draft",createdAt:now,updatedAt:now))
        try await db.queueTonSend(sendID:"send",plan:plan)
        do { _ = try await vault.signTonSend(sendID:"send",quote:quote,digits:[9,9,9,9,9,9],reason:"Test"); preconditionFailure("Wrong PIN signed") }
        catch { check(error as? OathWalletError == .wrongPasscode,"Wrong PIN rejected") }
        let unsigned = try await db.send("send"); check(unsigned?.signedPayload == nil,"Failed authentication persists no signature")
        do { _ = try await vault.signTonSend(sendID:"send",quote:quote,digits:nil,reason:"Test"); preconditionFailure("Missing biometrics signed") }
        catch { check(error is OathBiometricCredentialError,"Missing biometrics returns passcode fallback") }
        let signed = try await vault.signTonSend(sendID:"send",quote:quote,digits:pin,reason:"Test")
        try TonSendCrypto.verify(signed,plan:plan); check(!signed.bytes.isEmpty,"Authenticated signature covers exact reviewed bytes")
        let wrong = OathTonQuote(walletID:"other-wallet",accountID:account.id,assetID:quote.assetID,plan:plan)
        do { _ = try await vault.signTonSend(sendID:"send",quote:wrong,digits:pin,reason:"Test"); preconditionFailure("Wrong wallet signed") }
        catch { check(error as? TonSendError == .changed,"Cross-wallet request rejected") }
        await biometrics.enroll(try await vault.biometricCredential())
        let authenticated = try await vault.signTonSend(sendID:"send",quote:quote,digits:nil,reason:"Test")
        try TonSendCrypto.verify(authenticated,plan:plan); check(!authenticated.bytes.isEmpty,"Biometrics authorize identical intent")
        await biometrics.pauseNextRead()
        let pending = Task { try await vault.signTonSend(sendID:"send",quote:quote,digits:nil,reason:"Test") }
        for _ in 0..<200 {
            if await biometrics.isWaiting { break }
            try await Task.sleep(for:.milliseconds(5))
        }
        check(await biometrics.isWaiting,"Biometric read entered")
        await vault.lock(); await biometrics.releaseRead()
        do { _ = try await pending.value; preconditionFailure("Locked vault accepted stale authorization") }
        catch { check(error is CancellationError || error as? OathWalletError == .locked,"Lock invalidates in-flight authorization") }
        do { _ = try await vault.signTonSend(sendID:"send",quote:quote,digits:pin,reason:"Test"); preconditionFailure("Locked vault signed") }
        catch { check(error as? OathWalletError == .locked,"Locked signing rejected") }
        _ = try await vault.unlock(digits: pin)
        let gate = AuditPreparationGate()
        let stale = Task { try await vault.signTonSend(sendID:"send",quote:quote,digits:pin,reason:"Test",prepare: { await gate.hold() }) }
        for _ in 0..<400 where !(await gate.waiting) { try await Task.sleep(for:.milliseconds(5)) }
        check(await gate.waiting,"Preparation entered before generation change")
        await vault.lock()
        _ = try await vault.unlock(digits: pin)
        await gate.release()
        do { _ = try await stale.value; preconditionFailure("Old authentication survived lock and unlock") }
        catch { check(error is CancellationError,"Lock and reopen invalidates the earlier authenticated operation") }
        check(try await db.send("send")?.signedPayload == nil,"Stale operation wrote no signature")

        let cancellationGate = AuditPreparationGate()
        let cancelled = Task { try await vault.signTonSend(sendID:"send",quote:quote,digits:pin,reason:"Test",prepare: { await cancellationGate.hold() }) }
        for _ in 0..<400 where !(await cancellationGate.waiting) { try await Task.sleep(for:.milliseconds(5)) }
        check(await cancellationGate.waiting,"Cancellation-resistant preparation entered")
        cancelled.cancel(); await cancellationGate.release()
        do { _ = try await cancelled.value; preconditionFailure("Cancelled authorization signed") }
        catch { check(error is CancellationError,"Caller cancellation prevents signing after delayed preparation") }
        check(try await db.send("send")?.signedPayload == nil,"Cancelled operation wrote no signature")

        do { _ = try await vault.signTonSend(sendID:"send",quote:quote,digits:pin,reason:"Test",prepare: { throw AuditPreparationFailure.rejected }); preconditionFailure("Failed preparation signed") }
        catch { check(error as? AuditPreparationFailure == .rejected,"Preparation failure propagates after authentication") }
        let fresh = try await vault.signTonSend(sendID:"send",quote:quote,digits:pin,reason:"Test")
        try TonSendCrypto.verify(fresh,plan:plan)
        check(!fresh.bytes.isEmpty,"Fresh independent authorization still works")
        let altered = OathTonQuote(walletID:quote.walletID,accountID:quote.accountID,assetID:"ton:other",plan:plan)
        do { _ = try await vault.signTonSend(sendID:"send",quote:altered,digits:pin,reason:"Test"); preconditionFailure("Unreviewed asset signed") }
        catch { check(error as? TonSendError == .changed,"Queued asset identity remains bound") }
        check(try await db.send("send")?.signedPayload == nil,"No test operation implicitly journaled a signature")
        print("TON authorization review: \(checks) checks passed. Production vault, PIN and imported-key signer; synthetic biometric store, no HD derivation, network, simulator or device.")
    }
}

private enum AuditPreparationFailure: Error { case rejected }
private actor AuditPreparationGate {
    private var continuation: CheckedContinuation<Void,Never>?
    var waiting: Bool { continuation != nil }
    func hold() async { await withCheckedContinuation { continuation = $0 } }
    func release() { let c = continuation; continuation = nil; c?.resume() }
}
