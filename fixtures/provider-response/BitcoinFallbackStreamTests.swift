import Foundation
import XCTest
@testable import OathBitcoin

// Run one case per network-denied process. Both real default providers are
// intercepted by URLProtocol and the accepted transaction contains no funds.
private final class FallbackFixture: URLProtocol, @unchecked Sendable {
    static let lock = NSLock()
    nonisolated(unsafe) static var tailSent = false
    nonisolated(unsafe) static var routes: [String] = []
    private var cancelled = false
    static let parent: Data = {
        var tx = BitcoinWire.little(UInt32(2)) + Data([1]) + Data(repeating: 9, count: 32)
        tx += BitcoinWire.little(UInt32(1)) + Data([0]) + BitcoinWire.little(UInt32.max)
        tx += Data([1]) + BitcoinWire.little(UInt64(1000)) + BitcoinWire.vector(Data([0x51])) + BitcoinWire.little(UInt32(0))
        return tx
    }()
    static let hash = try! BitcoinTransactions.txid(parent)
    override class func canInit(with request: URLRequest) -> Bool {
        guard let url = request.url, ["blockstream.info", "mempool.space"].contains(url.host) else { return false }
        return ["/api/v1/fees/recommended", "/api/fee-estimates", "/api/tx/"+hash+"/raw"].contains(url.path)
    }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let url = request.url!, host = url.host!
        Self.lock.withLock { Self.routes.append(host) }
        let head = HTTPURLResponse(url: url, statusCode: 200, httpVersion: "HTTP/1.1", headerFields: [:])!
        client?.urlProtocol(self, didReceive: head, cacheStoragePolicy: .notAllowed)
        let raw = url.lastPathComponent == "raw"
        if (raw && host == "blockstream.info") || (!raw && host == "mempool.space") {
            client?.urlProtocol(self, didLoad: Data(repeating: 42, count: (raw ? 4_000_000 : 65_536) + 16_384))
            DispatchQueue.global().asyncAfter(deadline: .now() + 2) { [self] in
                let deliver = Self.lock.withLock { if cancelled { return false }; Self.tailSent = true; return true }
                guard deliver else { return }
                client?.urlProtocolDidFinishLoading(self)
            }
        } else {
            client?.urlProtocol(self, didLoad: raw ? Self.parent : Data(#"{"3":2}"#.utf8))
            client?.urlProtocolDidFinishLoading(self)
        }
    }
    override func stopLoading() { Self.lock.withLock { cancelled = true } }
}

final class BitcoinFallbackStreamTests: XCTestCase, @unchecked Sendable {
    override func setUp() {
        super.setUp()
        FallbackFixture.lock.withLock { FallbackFixture.routes = []; FallbackFixture.tailSent = false }
        XCTAssertTrue(URLProtocol.registerClass(FallbackFixture.self))
    }
    override func tearDown() { URLProtocol.unregisterClass(FallbackFixture.self); super.tearDown() }
    private func verify(_ hosts: [String]) {
        XCTAssertEqual(FallbackFixture.lock.withLock { FallbackFixture.routes }, hosts)
        if FallbackFixture.lock.withLock({ FallbackFixture.tailSent }) { XCTFail("Fallback consumed the oversized response tail") }
    }
    func testFeeFallbackMovesToNextHostAtLimit() async throws {
        let fee = try await BitcoinFeeFallback().rate { throw BitcoinSendError.feeUnavailable }
        XCTAssertEqual(fee, 2000)
        verify(["mempool.space","blockstream.info"])
    }
    func testParentFallbackAuthenticatesNextHostsTransaction() async throws {
        let result = try await BitcoinTransactionFallback().transactions(txids: [FallbackFixture.hash])
        XCTAssertEqual(result, [FallbackFixture.hash:FallbackFixture.parent])
        verify(["blockstream.info","mempool.space"])
    }
}
