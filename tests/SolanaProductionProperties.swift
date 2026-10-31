import Foundation
import XCTest
@testable import OathAnkr

final class SolanaAuditProductionTests: XCTestCase {
    struct CurveVector: Decodable { let hex: String, isPoint: Bool }
    struct EncodingVector: Decodable { let hex: String, base58: String }
    struct TransactionVectors: Decodable { let vectors: [TransactionVector] }
    struct TransactionVector: Decodable { let name: String, account: String, unsigned: String, signed: String }
    struct Random {
        var state: UInt64 = 0x4f415448534f4c31
        mutating func next() -> UInt64 {
            state ^= state << 13; state ^= state >> 7; state ^= state << 17
            return state
        }
    }
    func vectors() throws -> [TransactionVector] {
        try JSONDecoder().decode(TransactionVectors.self, from: Data(contentsOf: XCTUnwrap(Bundle.module.url(forResource: "transactions", withExtension: "json")))).vectors
    }
    func request(_ bytes: Data, account: String) throws -> WalletConnectSolanaRequest {
        try WalletConnectSolanaRequest(method: "solana_signTransaction", chain: SolanaSendNetwork.devnet.walletConnectChain,
            account: account, params: JSONSerialization.data(withJSONObject: ["transaction": bytes.base64EncodedString()]))
    }
    func testIndependentBase58Vectors() throws {
        let rows = try JSONDecoder().decode([EncodingVector].self, from: Data(contentsOf: XCTUnwrap(Bundle.module.url(forResource: "encodings", withExtension: "json"))))
        XCTAssertEqual(rows.count, 528)
        for row in rows {
            let chars = Array(row.hex)
            let bytes = Data(stride(from: 0, to: chars.count, by: 2).map { UInt8(String(chars[$0...$0+1]), radix: 16)! })
            XCTAssertEqual(SolanaSendCrypto.encode(bytes), row.base58)
            XCTAssertEqual(try SolanaSendCrypto.decode(row.base58), bytes)
        }
        for text in ["", "0", "O", "I", "l", "1\n", String(repeating: "1", count: 89)] {
            XCTAssertThrowsError(try SolanaSendCrypto.decode(text))
        }
    }
    func testIndependentCurveExistenceVectors() throws {
        let rows = try JSONDecoder().decode([CurveVector].self, from: Data(contentsOf: XCTUnwrap(Bundle.module.url(forResource: "curve", withExtension: "json"))))
        XCTAssertEqual(rows.count, 1038)
        for row in rows {
            let chars = Array(row.hex)
            let bytes = Data(stride(from: 0, to: chars.count, by: 2).map { UInt8(String(chars[$0...$0+1]), radix: 16)! })
            XCTAssertEqual(SolanaCurve.isPoint(bytes), row.isPoint, row.hex)
        }
        for count in [0, 1, 31, 33, 64] {
            XCTAssertFalse(SolanaCurve.isPoint(Data(repeating: 0, count: count)))
        }
    }
    func testAllTruncationsAndNoncanonicalLengths() throws {
        for row in try vectors() {
            let bytes = try XCTUnwrap(Data(base64Encoded: row.unsigned))
            for size in 0..<bytes.count {
                XCTAssertThrowsError(try WalletConnectSolanaTransaction(bytes: Data(bytes.prefix(size)), account: row.account), "\(row.name) truncated at \(size)")
            }
            XCTAssertThrowsError(try WalletConnectSolanaTransaction(bytes: bytes + Data([0]), account: row.account))
            // These alternate short-vector encodings must not alias a canonical count.
            for prefix in [Data([0]), Data([20]), Data([0x81,0]), Data([0xff,0xff,4]), Data([0x80,0x80,0x80])] {
                XCTAssertThrowsError(try WalletConnectSolanaTransaction(bytes: prefix + bytes.dropFirst(), account: row.account))
            }
        }
        XCTAssertThrowsError(try WalletConnectSolanaTransaction(bytes: Data(repeating: 0, count: 1233), account: "fixture"))
    }
    func testSignatureSlotsAndImmutableMessages() throws {
        let rows = try vectors()
        XCTAssertEqual(rows.count, 3)
        for row in rows {
            let original = try XCTUnwrap(Data(base64Encoded: row.unsigned))
            let input = try request(original, account: row.account)
            let tx = input.transactions[0]
            try tx.verifySigned(XCTUnwrap(Data(base64Encoded: row.signed)), requireAll: true)
            let result = try input.sign(privateKey: Data(repeating: 1, count: 32)).transactions[0]
            try tx.verifySigned(result, requireAll: true)
            let start = tx.signatureOffset + 64 * tx.signerIndex, end = start + 64
            XCTAssertEqual(result.prefix(start), original.prefix(start))
            XCTAssertEqual(result.suffix(from: end), original.suffix(from: end))
            XCTAssertEqual(try WalletConnectSolanaTransaction(bytes: result, account: row.account).message, tx.message)
            XCTAssertThrowsError(try input.sign(privateKey: Data(repeating: 2, count: 32)))
            var tampered = result; tampered[start] ^= 1
            XCTAssertThrowsError(try tx.verifySigned(tampered, requireAll: true))
        }
    }
    func testSeededMutationsCannotRewriteUnselectedBytes() throws {
        let rows = try vectors(); var random = Random(), accepted = 0, rejected = 0
        for i in 0..<2048 {
            let row = rows[i % rows.count]
            var bytes = try XCTUnwrap(Data(base64Encoded: row.unsigned))
            let offset = Int(random.next() % UInt64(bytes.count))
            bytes[offset] ^= UInt8(1 << (random.next() % 8))
            let input: WalletConnectSolanaRequest
            do { input = try request(bytes, account: row.account) }
            catch { rejected += 1; continue }
            // Parse rejection is expected; any later invariant failure is a test
            // failure and must never be counted as another rejected mutation.
            accepted += 1
            let tx = input.transactions[0]
            XCTAssertNotEqual(input.fingerprint, try request(XCTUnwrap(Data(base64Encoded: row.unsigned)), account: row.account).fingerprint)
            let signed = try input.sign(privateKey: Data(repeating: 1, count: 32)).transactions[0]
            try tx.verifySigned(signed, requireAll: false)
            let start = tx.signatureOffset + 64 * tx.signerIndex, end = start + 64
            XCTAssertEqual(signed.prefix(start), bytes.prefix(start))
            XCTAssertEqual(signed.suffix(from: end), bytes.suffix(from: end))
            XCTAssertEqual(try WalletConnectSolanaTransaction(bytes: signed, account: row.account).message, tx.message)
        }
        XCTAssertGreaterThan(accepted, 0); XCTAssertGreaterThan(rejected, 0)
        XCTAssertEqual(accepted + rejected, 2048)
        print("SOLANA_MUTATIONS accepted=\(accepted) rejected=\(rejected) seed=0x4f415448534f4c31")
    }
}
