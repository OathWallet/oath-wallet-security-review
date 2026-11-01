import CryptoKit
import XCTest
@testable import OathAnkr
import stellarsdk

final class StellarEnvelopeLimitTests: XCTestCase {
    private let seed = Data(repeating: 7, count: 32)
    private func words(_ ns: UInt32...) -> Data {
        Data(ns.flatMap { n in [UInt8(truncatingIfNeeded:n >> 24),UInt8(truncatingIfNeeded:n >> 16),UInt8(truncatingIfNeeded:n >> 8),UInt8(truncatingIfNeeded:n)] })
    }
    // Independent hand-built XDR. One invoke-contract op for function "f";
    // argument is SCV_VOID wrapped in optional one-element SCV_VEC values.
    private func packet(_ depth: Int, count: UInt32 = 1, present: UInt32 = 1) throws -> Data {
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation: seed)
        var data = words(2,0) + key.publicKey.rawRepresentation
        data += words(100,0,42,0,0,1,0,24,0,1)
        data += Data(repeating:4,count:32) + words(1) + Data([102,0,0,0]) + words(count)
        for _ in 0..<depth { data += words(16,present,1) }
        return data + words(1,0,0,0)
    }
    private func request(_ data: Data) throws -> WalletConnectStellarRequest {
        try WalletConnectStellarRequest(method:"stellar_signXDR",chain:"stellar:testnet",
            account:StellarSendCrypto.address(privateKey:seed),params:JSONEncoder().encode(["xdr":data.base64EncodedString()]))
    }
    func testNestedEnvelopeMatchesIndependentDigest() throws {
        let req = try request(packet(2))
        let details = try req.details()
        XCTAssertEqual(details.hash,"4e9d4d8dcdc624735c66b21c8a26793b21e2d67d7214067ab288c0983be98277")
        let now = Date(timeIntervalSince1970:1_700_000_000)
        let signed = try req.sign(privateKey:seed,review:.init(request:req,details:details,firstLedger:1,createdAt:now),now:now)
        try req.verify(signed)
    }
    func testRecursiveVectorHitsDepthGuard() throws {
        XCTAssertThrowsError(try request(packet(512))) { error in
            guard case XDRDecoder.Error.maxDecodingDepthExceeded = error else { return XCTFail("Expected SDK nesting guard, got "+String(describing:error)) }
        }
    }
    func testForgedArgumentCountHitsRemainingBytesGuard() throws {
        XCTAssertThrowsError(try request(packet(0,count:.max))) { error in
            guard case StellarSDKError.xdrDecodingError(let message) = error else { return XCTFail("Expected SDK count guard") }
            XCTAssertTrue(message.contains("remaining bytes"))
        }
    }
    func testNoncanonicalVectorPresenceRejectedByApp() throws {
        XCTAssertThrowsError(try request(packet(1,present:2))) { XCTAssertEqual($0 as? StellarSendError,.malformed) }
    }
    func testTrailingWordRejectedByApp() throws {
        XCTAssertThrowsError(try request(packet(1)+words(0))) { XCTAssertEqual($0 as? StellarSendError,.malformed) }
    }
}
