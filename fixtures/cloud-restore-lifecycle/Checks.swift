import Foundation
import Observation
import Synchronization

// Synthetic boundaries only. The production restore model is compiled unchanged.
enum CloudBackupError: Error { case authenticationFailed, passwordTooShort, passwordTooLong, unavailable, accountChanged, invalidDocument, fileConflict }
enum CloudRestoreError: Error { case missingFile, downloadTimedOut, downloadFailed, discoveryFailed }
enum OathWalletError: Error { case invalidPhrase, invalidPrivateKey, derivationFailed }
enum OathStringKey { case restoreDiscoveryFailed, restoreWrongPassword, restorePasswordDetail, cloudBackupUnavailable, cloudBackupAccountChanged, restoreInvalidBackup, restoreConflict, restoreMissing, restoreDownloadFailed, restoreFailed }
struct CloudLocation: Sendable { let accountID = "synthetic-account" }
struct CloudBackupEntry: Sendable { let id: String; let percentDownloaded: Double? }
struct OathRestoredWallet: Sendable { init(backup: Data) throws {} }
enum BackupDocument {
    static func open(_ data: Data, password: String) throws -> Data {
        guard password == "synthetic-test-password" else { throw CloudBackupError.authenticationFailed }
        return data
    }
}
enum OathDiagnostics {
    static let errors = Mutex(0)
    static func record(_ error: Error) { errors.withLock { $0 += 1 } }
    static var count: Int { errors.withLock { $0 } }
}
@MainActor final class Boundary {
    static let shared = Boundary()
    var stream: AsyncThrowingStream<[CloudBackupEntry], Error>.Continuation?
    var reads: [CheckedContinuation<Data, Error>] = []
    var save: CheckedContinuation<Void, Never>?
    var saves = 0
    var savesReturned = 0
    var verifyFailure = false
}
struct CloudDrive: Sendable {
    func location() async throws -> CloudLocation { CloudLocation() }
    @MainActor func verifyAccount(_ account: String) async throws {
        if Boundary.shared.verifyFailure { throw CloudBackupError.accountChanged }
    }
    @MainActor func read(_ entry: CloudBackupEntry, at location: CloudLocation) async throws -> Data {
        // Deliberately ignores cancellation so the model's late-response guards run.
        try await withCheckedThrowingContinuation { Boundary.shared.reads.append($0) }
    }
}
@MainActor final class CloudBackupDiscovery {
    let updates: AsyncThrowingStream<[CloudBackupEntry], Error>
    init(location: CloudLocation) throws {
        let pair = AsyncThrowingStream<[CloudBackupEntry], Error>.makeStream()
        updates = pair.stream
        Boundary.shared.stream = pair.continuation
    }
    func stop() { Boundary.shared.stream?.finish() }
}

@main struct Checks {
    @MainActor static var passed = 0
    @MainActor static var failed = 0
    @MainActor static func check(_ value: Bool, _ name: String) {
        if value { passed += 1 } else { failed += 1 }
        print("\(value ? "PASS" : "FAIL"): \(name)")
    }
    @MainActor static func until(_ label: String, _ condition: @MainActor () -> Bool) async {
        let deadline = ContinuousClock.now.advanced(by: .seconds(5))
        while !condition() {
            if ContinuousClock.now >= deadline { print("TIMEOUT: \(label)"); exit(2) }
            await Task.yield()
        }
    }
    @MainActor static func ready(_ model: OathCloudRestoreModel) async {
        Boundary.shared.stream = nil
        model.start()
        await until("discovery constructed") { Boundary.shared.stream != nil }
        Boundary.shared.stream?.yield([CloudBackupEntry(id: "fixture", percentDownloaded: 50)])
        await until("discovery delivered") { model.phase == .ready }
    }
    @MainActor static func begin(_ model: OathCloudRestoreModel, password: String = "synthetic-test-password", holdSave: Bool = false) async {
        model.choose(CloudBackupEntry(id: "fixture", percentDownloaded: 50))
        model.restore(password: password) { _ in
            Boundary.shared.saves += 1
            if holdSave { await withCheckedContinuation { Boundary.shared.save = $0 } }
            Boundary.shared.savesReturned += 1
        }
        await until("read started") { !Boundary.shared.reads.isEmpty }
    }
    @MainActor static func main() async {
        let model = OathCloudRestoreModel()
        await ready(model)
        check(model.entries.count == 1, "discovery publishes current entries")
        model.choose(CloudBackupEntry(id: "absent", percentDownloaded: 0))
        check(model.selected == nil, "unknown entry cannot be selected")
        await begin(model)
        check(model.busy && model.phase == .downloading, "download owns busy state")
        check(model.downloadProgress == 0.5, "download progress uses current entry")
        let attempt = model.attempt
        model.choose(CloudBackupEntry(id: "fixture", percentDownloaded: 0))
        check(model.attempt == attempt, "busy selection cannot replace attempt")
        model.restore(password: "synthetic-test-password") { _ in fatalError("duplicate save") }
        check(Boundary.shared.reads.count == 1, "duplicate restore cannot start another read")
        Boundary.shared.reads.removeFirst().resume(returning: Data([1]))
        await until("successful restore") { model.phase == .completed }
        check(Boundary.shared.saves == 1, "successful restore saves exactly once")
        check(!model.busy && model.notice == nil, "successful restore clears busy without error")
        model.stop()
        check(model.entries.isEmpty && model.selected == nil, "stop clears discovered and selected entries")

        await ready(model)
        await begin(model, password: "wrong-test-password")
        let wrongAttempt = model.attempt
        Boundary.shared.reads.removeFirst().resume(returning: Data([1]))
        await until("wrong password reported") { model.notice == .restoreWrongPassword }
        check(model.phase == .ready && !model.busy, "wrong password permits retry")
        check(model.attempt != wrongAttempt, "wrong password replaces secure field identity")
        check(Boundary.shared.saves == 1, "wrong password never reaches local save")

        await begin(model)
        Boundary.shared.verifyFailure = true
        Boundary.shared.reads.removeFirst().resume(returning: Data([1]))
        await until("account rejected") { model.notice == .cloudBackupAccountChanged }
        check(Boundary.shared.saves == 1, "account change after decryption prevents save")
        Boundary.shared.verifyFailure = false

        await begin(model)
        let oldRead = Boundary.shared.reads.removeFirst()
        model.stop()
        await ready(model)
        let newAttempt = model.attempt
        let errors = OathDiagnostics.count
        oldRead.resume(throwing: CloudRestoreError.missingFile)
        await until("late old failure handled") { OathDiagnostics.count > errors }
        check(model.notice == nil && model.phase == .ready, "canceled read failure cannot set current error")
        check(model.attempt == newAttempt && model.entries.count == 1, "canceled failure cannot reset new discovery")

        await begin(model, holdSave: true)
        Boundary.shared.reads.removeFirst().resume(returning: Data([1]))
        await until("save suspended") { Boundary.shared.save != nil }
        check(model.phase == .saving && model.busy, "local save remains busy until completion")
        model.stop()
        await ready(model)
        // Completion and the model's subsequent ownership guard run on the main
        // actor without another suspension. Observe the callback return first.
        Boundary.shared.save?.resume(); Boundary.shared.save = nil
        await until("old save returned") { Boundary.shared.savesReturned == 2 }
        check(model.phase == .ready && model.notice == nil, "late old save cannot finish new discovery")
        await begin(model, password: "wrong-test-password")
        Boundary.shared.reads.removeFirst().resume(returning: Data([1]))
        await until("new attempt completes after old save") { model.notice == .restoreWrongPassword }
        check(model.phase == .ready, "late old save cannot complete newer attempt")
        check(Boundary.shared.saves == 2, "new failed attempt cannot repeat old save")

        await begin(model)
        let pending = Boundary.shared.reads.removeFirst()
        Boundary.shared.stream?.finish(throwing: CloudBackupError.accountChanged)
        await until("discovery account failure") { model.notice == .cloudBackupAccountChanged }
        check(model.entries.isEmpty && model.selected == nil, "discovery failure clears restore selection")
        let discoveredAttempt = model.attempt
        let errors2 = OathDiagnostics.count
        pending.resume(throwing: CloudRestoreError.missingFile)
        await until("invalidated read returns") { OathDiagnostics.count > errors2 }
        check(model.notice == .cloudBackupAccountChanged && model.attempt == discoveredAttempt, "invalidated read cannot overwrite discovery failure")
        check(Boundary.shared.saves == 2, "discovery invalidation prevents pending save")
        model.stop()
        print("Cloud restore lifecycle checks: \(passed) passed, \(failed) failed")
        exit(failed == 0 ? 0 : 1)
    }
}
