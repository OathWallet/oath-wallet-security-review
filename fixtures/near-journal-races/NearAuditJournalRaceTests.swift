import Foundation
import XCTest
import GRDB
@testable import OathAnkr
@testable import OathDatabase

private actor ReservationGate {
    var waiting: [CheckedContinuation<Void, Never>] = []
    func enter() async {
        await withCheckedContinuation { continuation in
            waiting.append(continuation)
            if waiting.count == 2 {
                let ready = waiting; waiting.removeAll()
                ready.forEach { $0.resume() }
            }
        }
    }
}

@MainActor final class NearAuditJournalRaceTests: XCTestCase {
    func testConcurrentDuplicateWalletsReserveExactlyOneSender() async throws {
        for _ in 0..<8 {
            let fixture = NearSendJournalTests()
            let (db, folder, plan) = try await fixture.fixture()
            defer { try? FileManager.default.removeItem(at: folder) }
            try await fixture.draft("one", plan: plan, db: db)
            try await fixture.draft("two", wallet: 2, plan: plan, db: db)
            let gate = ReservationGate()
            let results = await withTaskGroup(of: String.self, returning: [String].self) { group in
                for id in ["one", "two"] {
                    group.addTask {
                        await gate.enter()
                        do { try await db.queueNearSend(sendID: id, plan: plan); return "queued" }
                        catch { return error as? NearSendError == .busy ? "busy" : "unexpected: \(error)" }
                    }
                }
                var values: [String] = []
                for await value in group { values.append(value) }
                return values.sorted()
            }
            XCTAssertEqual(results, ["busy", "queued"])
            let counts = try await db.pool.read { db in
                [try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM sends WHERE state='queued'")!,
                 try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM nearSendPlans")!,
                 try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM sends WHERE state='draft'")!]
            }
            XCTAssertEqual(counts, [1, 1, 1], "Losing transaction must roll back its plan and state")
        }
    }

    func testLateAcknowledgementsPreserveEveryTerminalStateAfterReopen() async throws {
        for outcome: NearSendReceipt.Outcome in [.confirmed, .failed, .expired] {
            let fixture = NearSendJournalTests()
            let (db, folder, plan) = try await fixture.fixture()
            defer { try? FileManager.default.removeItem(at: folder) }
            try await fixture.draft("one", plan: plan, db: db)
            try await db.queueNearSend(sendID: "one", plan: plan)
            let signed = try NearSendCrypto.sign(plan, privateKey: fixture.key)
            try await db.journalNearSignature(sendID: "one", signed: signed)
            let terminal = NearSendReceipt(hash: signed.hash, outcome: outcome,
                fee: outcome == .expired ? nil : "12", block: outcome == .expired ? nil : 101)
            try await db.settleNearSend(sendID: "one", receipt: terminal)
            let before = try await snapshot(db)
            let reopened = try await OathDatabase.open(at: folder.appendingPathComponent("wallet.sqlite"))
            for _ in 0..<3 {
                try await reopened.settleNearSend(sendID: "one", receipt: .init(hash: signed.hash, outcome: .accepted))
                try await reopened.settleNearSend(sendID: "one", receipt: .init(hash: signed.hash, outcome: .unknown))
            }
            let after = try await snapshot(reopened)
            XCTAssertEqual(after, before)
            let restored = try await reopened.send("one")
            XCTAssertEqual(try JSONDecoder().decode(NearSignedSend.self, from: XCTUnwrap(restored?.signedPayload)), signed)
            let foreign = try await reopened.nearSubmission(walletID: "w2", hash: signed.hash)
            XCTAssertNil(foreign)
        }
    }

    func testMalformedReceiptsCannotPartiallyMutateSignedJournal() async throws {
        let fixture = NearSendJournalTests()
        let (db, folder, plan) = try await fixture.fixture()
        defer { try? FileManager.default.removeItem(at: folder) }
        try await fixture.draft("one", plan: plan, db: db)
        try await db.queueNearSend(sendID: "one", plan: plan)
        let signed = try NearSendCrypto.sign(plan, privateKey: fixture.key)
        try await db.journalNearSignature(sendID: "one", signed: signed)
        let before = try await snapshot(db)
        let invalid: [NearSendReceipt] = [
            .init(hash: String(repeating: "1", count: 32), outcome: .confirmed, fee: "12", block: 101),
            .init(hash: signed.hash, outcome: .confirmed, fee: nil, block: 101),
            .init(hash: signed.hash, outcome: .failed, fee: "-1", block: 101),
            .init(hash: signed.hash, outcome: .confirmed, fee: "12", block: 99),
            .init(hash: signed.hash, outcome: .confirmed, fee: "12", block: nil),
            .init(hash: signed.hash, outcome: .accepted, fee: "12", block: nil),
            .init(hash: signed.hash, outcome: .accepted, fee: nil, block: 101),
            .init(hash: signed.hash, outcome: .expired, fee: "0", block: nil),
            .init(hash: signed.hash, outcome: .expired, fee: nil, block: 101)
        ]
        for receipt in invalid {
            do { try await db.settleNearSend(sendID: "one", receipt: receipt); XCTFail("Malformed receipt accepted") }
            catch { XCTAssertTrue(error is NearSendError || error is StoreError) }
            let after = try await snapshot(db)
            XCTAssertEqual(after, before)
        }
    }

    private func snapshot(_ database: OathDatabase) async throws -> [String] {
        try await database.pool.read { db in
            let queries = [
                "SELECT state || ':' || COALESCE(failureCode,'NULL') || ':' || updatedAt FROM sends WHERE id='one'",
                "SELECT state || ':' || COALESCE(feeAtomic,'NULL') || ':' || COALESCE(blockHeight,'NULL') || ':' || updatedAt FROM transactions",
                "SELECT CAST(COUNT(*) AS TEXT) FROM sendBalanceRefreshes",
                "SELECT CAST(COUNT(*) AS TEXT) FROM sendStatusChecks"
            ]
            return try queries.map { try XCTUnwrap(String.fetchOne(db, sql: $0)) }
        }
    }
}
