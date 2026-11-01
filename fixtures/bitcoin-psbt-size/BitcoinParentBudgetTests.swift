import Foundation
import XCTest
@testable import OathBitcoin

private final class ParentProtocol: URLProtocol, @unchecked Sendable {
    // Standard-shaped synthetic parents, each less than 100 kB.
    static let parents: [String: Data] = {
        var result: [String: Data] = [:]
        let output = BitcoinWire.little(UInt64(12_500)) + BitcoinWire.vector(Data([0,20]) + Data(repeating: 3, count: 20))
        for marker in 1...6 {
            var tx = BitcoinWire.little(UInt32(2)) + Data([1]) + Data(repeating: UInt8(marker), count: 32)
            tx += BitcoinWire.little(UInt32(0)) + Data([0]) + BitcoinWire.little(UInt32.max)
            tx += BitcoinWire.compact(2_900)
            for _ in 0..<2_900 { tx += output }
            tx += BitcoinWire.little(UInt32(0))
            result[try! BitcoinTransactions.txid(tx)] = tx
        }
        return result
    }()

    override class func canInit(with request: URLRequest) -> Bool {
        request.url?.host == "mempool.space" && request.url?.path.hasPrefix("/signet/api/tx/") == true
    }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        guard let url = request.url, url.lastPathComponent == "hex",
              let body = Self.parents[url.deletingLastPathComponent().lastPathComponent],
              let response = HTTPURLResponse(url: url, statusCode: 200, httpVersion: nil, headerFields: nil) else {
            client?.urlProtocol(self, didFailWithError: URLError(.badServerResponse))
            return
        }
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Data(body.hex.utf8))
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}

final class BitcoinParentBudgetTests: XCTestCase, @unchecked Sendable {
    private func load(_ count: Int) async throws -> [String: Data] {
        XCTAssertTrue(URLProtocol.registerClass(ParentProtocol.self))
        defer { URLProtocol.unregisterClass(ParentProtocol.self) }
        let ids = Array(ParentProtocol.parents.keys.sorted().prefix(count))
        var tx = BitcoinWire.little(UInt32(2)) + BitcoinWire.compact(UInt64(ids.count))
        for id in ids {
            tx += Data(try XCTUnwrap(Data(hex: id)).reversed()) + BitcoinWire.little(UInt32(0)) + Data([0]) + BitcoinWire.little(UInt32.max)
        }
        tx += Data([1]) + BitcoinWire.little(UInt64(10_000)) + BitcoinWire.vector(Data([0x51])) + BitcoinWire.little(UInt32(0))
        let packet = Data([0x70,0x73,0x62,0x74,0xff]) + BitcoinWire.pair(0,tx) + Data(repeating:0,count:ids.count+2)
        return try await BitcoinConnectClient().parents(psbt: packet.base64EncodedString(), network: .signet)
    }

    func testParentsCannotRetainMoreThanOnePacket() async throws {
        do {
            let parents = try await load(6)
            XCTAssertEqual(parents, ParentProtocol.parents)
            XCTFail("Six hash-verified parents exceeded the packet budget")
        } catch {
            XCTAssertEqual(error as? BitcoinConnectError, .tooLarge)
        }
    }
    func testSmallBatchReturnsBothHashVerifiedParents() async throws {
        let parents = try await load(2)
        let ids = Set(ParentProtocol.parents.keys.sorted().prefix(2))
        XCTAssertEqual(parents, ParentProtocol.parents.filter { ids.contains($0.key) })
    }
}
