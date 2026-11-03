import XCTest
import Foundation
@testable import WalletConnectKMS

final class EmptyEnvelopeBoundaryTests: XCTestCase {
    private let codings: [Envelope.CodingType] = [.base64Encoded, .base64UrlEncoded]

    func testEmptyBase64EnvelopeIsRejected() {
        XCTAssertThrowsError(try Envelope(.base64Encoded, envelopeString: ""))
    }

    func testEmptyBase64URLEnvelopeIsRejected() {
        XCTAssertThrowsError(try Envelope(.base64UrlEncoded, envelopeString: ""))
    }

    private func decodeEmpty(_ coding: Envelope.CodingType) throws {
        let serializer = Serializer(kms: KeyManagementServiceMock(), logger: ConsoleLoggerMock())
        let _: (String, String?, Data) = try serializer.deserialize(topic: "synthetic", codingType: coding, envelopeString: "")
    }

    func testEmptyBase64SerializerIsRejected() {
        XCTAssertThrowsError(try decodeEmpty(.base64Encoded))
    }

    func testEmptyBase64URLSerializerIsRejected() {
        XCTAssertThrowsError(try decodeEmpty(.base64UrlEncoded))
    }

    func testTruncatedTypeOneIsRejected() {
        for count in 1...32 {
            let bytes = Data([1] + Array(repeating: UInt8(0x42), count: count - 1))
            for coding in codings {
                XCTAssertThrowsError(try Envelope(coding, envelopeString: bytes.base64EncodedString()))
            }
        }
    }

    func testUnsupportedTypesAreRejected() {
        for byte in UInt8(3)...UInt8(255) {
            for coding in codings {
                XCTAssertThrowsError(try Envelope(coding, envelopeString: Data([byte]).base64EncodedString()))
            }
        }
    }

    func testMalformedBase64IsRejected() {
        for input in ["!", "A", "not base64", "é"] {
            for coding in codings { XCTAssertThrowsError(try Envelope(coding, envelopeString: input)) }
        }
    }

    func testValidTypeZeroAndTwoRoundTrip() throws {
        for type: Envelope.EnvelopeType in [.type0, .type2] {
            for bytes in [Data(), Data([0, 1, 0xFE, 0xFF])] {
                for coding in codings {
                    let expected = Envelope(type: type, sealbox: bytes, codingType: coding)
                    let decoded = try Envelope(coding, envelopeString: expected.serialised(codingType: coding))
                    XCTAssertEqual(decoded, expected)
                }
            }
        }
    }

    func testValidTypeOneRoundTrip() throws {
        for coding in codings {
            let expected = Envelope(type: .type1(pubKey: Data(repeating: 0x42, count: 32)), sealbox: Data([0, 0xFF]), codingType: coding)
            let decoded = try Envelope(coding, envelopeString: expected.serialised(codingType: coding))
            XCTAssertEqual(decoded, expected)
        }
    }

    func testValidPlaintextSerializerRoundTrip() throws {
        let serializer = Serializer(kms: KeyManagementServiceMock(), logger: ConsoleLoggerMock())
        for coding in codings {
            let encoded = try serializer.serialize(topic: nil, encodable: "synthetic control", envelopeType: .type2, codingType: coding)
            let decoded: (String, String?, Data) = try serializer.deserialize(topic: "synthetic", codingType: coding, envelopeString: encoded)
            XCTAssertEqual(decoded.0, "synthetic control")
            XCTAssertNil(decoded.1)
        }
    }
}
