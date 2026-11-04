import Foundation
import Observation

struct CloudBackupRecord: Sendable {
    let walletID: String
    var state = "queued"
    var enabled = true
    var failureCode: String?
    var encryptedDocument: Data? = Data()
}
struct OathWalletVault: Sendable {}
enum ProbeError: Error { case failed }
enum OathDiagnostics { static func record(_ error: any Error) {} }
actor ProbeDB {
    func reconcileRemovedCloudBackups() async throws {}
    func cloudBackup(walletID: String) async throws -> CloudBackupRecord? { nil }
    nonisolated func observeCloudBackup(walletID: String) -> AsyncThrowingStream<CloudBackupRecord?, Error> {
        AsyncThrowingStream { $0.finish() }
    }
}
actor OathDataEnvironment {
    static let shared = OathDataEnvironment()
    func database() async throws -> ProbeDB { ProbeDB() }
}
actor Gates {
    static let shared = Gates()
    private var pending: [String: CheckedContinuation<Void, Error>] = [:]
    private var entered: [String: CheckedContinuation<Void, Never>] = [:]
    private var calls: [String: Int] = [:]
    func hold(_ name: String) async throws {
        calls[name, default: 0] += 1
        try await withCheckedThrowingContinuation { c in
            precondition(pending[name] == nil)
            pending[name] = c
            entered.removeValue(forKey: name)?.resume()
        }
    }
    func wait(_ name: String) async {
        if pending[name] != nil { return }
        await withCheckedContinuation { entered[name] = $0 }
    }
    func release(_ name: String, fails: Bool) {
        guard let c = pending.removeValue(forKey: name) else { fatalError("missing entered gate") }
        if fails { c.resume(throwing: ProbeError.failed) } else { c.resume() }
    }
    func count(_ name: String) -> Int { calls[name, default: 0] }
}
actor OathCloudBackupService {
    static let shared = OathCloudBackupService()
    func create(walletID: String, password: String, vault: OathWalletVault) async throws {
        try await Gates.shared.hold(walletID)
    }
    func disable(walletID: String) async throws { try await Gates.shared.hold(walletID) }
    func checkAvailability(for record: CloudBackupRecord?) async throws {
        guard let record else { fatalError("missing fixture record") }
        try await Gates.shared.hold(record.walletID)
    }
    func resume() async throws {}
    nonisolated static func failureCode(_ error: any Error) -> String { "failed" }
}

@main struct Checks {
    @MainActor static func main() async {
        var passed=0, failed=0
        func check(_ ok: Bool, _ label: String) {
            if ok { passed += 1; print("PASS: \(label)") }
            else { failed += 1; print("FAIL: \(label)") }
        }
        func start(_ model: OathCloudBackupModel, _ operation: String, _ id: String) -> Task<Void, Never> {
            switch operation {
            case "create": model.create(walletID: id, password: "synthetic fixture password", vault: .init())
            case "disable": model.disable(walletID: id)
            case "retry": model.record=CloudBackupRecord(walletID: id); model.retry(walletID: id)
            default: fatalError("unknown operation")
            }
            guard let task=model.reviewTask else { fatalError("missing production task") }
            return task
        }
        for operation in ["create", "disable", "retry"] {
            for fails in [false, true] {
                let label="stale \(operation) \(fails ? "failure" : "success")"
                let model=OathCloudBackupModel(), oldID=label+" old", newID=label+" new"
                let old=start(model,operation,oldID)
                await Gates.shared.wait(oldID)
                model.cancelPreparation()
                let new=start(model,"create",newID)
                await Gates.shared.wait(newID)
                await Gates.shared.release(oldID,fails:fails)
                await old.value // Proves the old catch/defer has completed before assertions.
                check(model.preparing,label+": preserves newer progress")
                check(model.reviewTask != nil,label+": preserves newer task")
                check(model.failure == nil,label+": preserves newer error state")
                check(await Gates.shared.count(newID)==1,label+": new service entered once")
                await Gates.shared.release(newID,fails:false)
                await new.value
                check(!model.preparing && model.reviewTask == nil,label+": current completion finishes")
                check(model.failure == nil,label+": current completion succeeds")
            }
        }
        for operation in ["create", "disable", "retry"] {
            for fails in [false,true] {
                let label="current \(operation) \(fails ? "failure" : "success")"
                let model=OathCloudBackupModel();model.failure="previous"
                let task=start(model,operation,label)
                await Gates.shared.wait(label)
                await Gates.shared.release(label,fails:fails)
                await task.value
                check(model.failure == (fails ? "failed" : nil),label+": reports current result")
                check(!model.preparing && model.reviewTask == nil,label+": finishes task")
            }
        }
        let duplicate=OathCloudBackupModel()
        let task=start(duplicate,"create","duplicate")
        await Gates.shared.wait("duplicate")
        duplicate.create(walletID:"not-started",password:"synthetic fixture password",vault:.init())
        check(duplicate.preparing && duplicate.reviewTask != nil,"duplicate: keeps original operation")
        await Gates.shared.release("duplicate",fails:false)
        await task.value
        check(await Gates.shared.count("not-started")==0,"duplicate: does not start second create")
        let cancelled=OathCloudBackupModel()
        let canceledTask=start(cancelled,"create","cancel-only")
        await Gates.shared.wait("cancel-only")
        cancelled.cancelPreparation()
        check(!cancelled.preparing && cancelled.reviewTask == nil,"cancel: clears presentation immediately")
        await Gates.shared.release("cancel-only",fails:true)
        await canceledTask.value
        check(cancelled.failure == nil && !cancelled.preparing,"cancel: late failure stays invisible")
        print("Backup settings checks: \(passed) passed, \(failed) failed")
        fflush(nil)
        if failed != 0 { exit(1) }
    }
}
