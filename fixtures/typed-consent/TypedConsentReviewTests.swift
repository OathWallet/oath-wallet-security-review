import XCTest
@testable import OathAnkr

final class TypedConsentReviewTests: XCTestCase {
    struct Corpus: Decodable {
        let vectors: [Vector], invalid: [Invalid]
    }
    struct Vector: Decodable {
        let name: String, json: String, chainId: String, account: String
        let domainHash: String, messageHash: String, digest: String, signature: String
        func decode(_ replacement: String? = nil, chain: UInt64? = nil, owner: String? = nil) throws -> WalletConnectTypedData {
            try WalletConnectTypedData(json: Data((replacement ?? json).utf8),
                chainID: chain ?? UInt64(chainId)!, account: owner ?? account)
        }
    }
    struct Invalid: Decodable { let name: String, json: String }
    func corpus() throws -> Corpus {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "typed-consent-review", withExtension: "json", subdirectory: "Fixtures"))
        return try JSONDecoder().decode(Corpus.self, from: Data(contentsOf: url))
    }
    func vector(_ name: String) throws -> Vector {
        try XCTUnwrap(corpus().vectors.first { $0.name == name })
    }
    func testIndependentEthersEncodingAndSignatures() throws {
        let rows = try corpus().vectors
        XCTAssertEqual(rows.count, 616)
        for v in rows {
            let decoded = try v.decode()
            XCTAssertEqual("0x" + TronSendCrypto.hex(decoded.domainSeparator), v.domainHash, v.name)
            XCTAssertEqual("0x" + TronSendCrypto.hex(decoded.messageHash), v.messageHash, v.name)
            XCTAssertEqual("0x" + TronSendCrypto.hex(decoded.digest), v.digest, v.name)
            XCTAssertEqual(try decoded.sign(privateKey: Data(repeating: 1, count: 32), account: v.account), v.signature, v.name)
        }
    }
    func testOutOfRangeAmountsAndWrongFixedByteLengthsReject() throws {
        let c = try corpus()
        XCTAssertEqual(c.invalid.count, 192)
        for row in c.invalid {
            XCTAssertThrowsError(try WalletConnectTypedData(json: Data(row.json.utf8), chainID: 1, account: c.vectors[0].account), row.name)
        }
    }
    func testDomainAndMessageSubstitutionsChangeDigest() throws {
        let base = try vector("binding-base").decode()
        for key in ["name", "version", "chainId", "verifyingContract"] {
            let changed = try vector("binding-domain-" + key).decode()
            XCTAssertNotEqual(base.digest, changed.digest, "Domain binding missing: " + key)
            XCTAssertEqual(base.messageHash, changed.messageHash)
        }
        for key in ["spender", "value", "nonce", "deadline"] {
            let changed = try vector("binding-message-" + key).decode()
            XCTAssertNotEqual(base.digest, changed.digest, "Message binding missing: " + key)
            XCTAssertEqual(base.domainSeparator, changed.domainSeparator)
        }
        for chain in ["1", "56", "9007199254740991", "9007199254740992", "9007199254740993", "18446744073709551615"] {
            let v = try vector("chain-" + chain)
            XCTAssertEqual(try v.decode().chainID, chain)
            XCTAssertThrowsError(try v.decode(chain: chain == "1" ? 56 : 1))
        }
    }
    func testPermissionClassificationAndSigningOwnerRemainBound() throws {
        let base = try vector("binding-base")
        XCTAssertThrowsError(try base.decode(owner: "0x3333333333333333333333333333333333333333"))
        let typed = try base.decode()
        XCTAssertThrowsError(try typed.sign(privateKey: Data(repeating: 2, count: 32), account: base.account))
        XCTAssertThrowsError(try typed.validatePermissionTime(now: Date(timeIntervalSince1970: 2_000_000_001)))
        XCTAssertNoThrow(try typed.validatePermissionTime(now: Date(timeIntervalSince1970: 2_000_000_000)))
        for row in try corpus().vectors where row.name.hasPrefix("permit2-limit-") {
            let d = try row.decode(), p = try XCTUnwrap(d.permission)
            XCTAssertEqual(p.atomicAmount, String(row.name.dropFirst("permit2-limit-".count)))
            XCTAssertEqual(p.spenderAddress, "0x2222222222222222222222222222222222222222")
            XCTAssertEqual(p.tokenAddress, "0x1111111111111111111111111111111111111111")
            XCTAssertEqual(p.isUnlimitedAllowance, row.name.hasSuffix("1461501637330902918203684832716283019655932542975"))
            XCTAssertFalse(p.isOneTimeTransfer)
            for (from,to) in [("0x000000000022D473030F116dDEE9F6B43aC78BA3", "0x3333333333333333333333333333333333333333"), ("\"name\":\"Permit2\"", "\"name\":\"Other\"")] {
                XCTAssertTrue(row.json.contains(from))
                XCTAssertNil(try row.decode(row.json.replacingOccurrences(of: from, with: to)).permission)
            }
        }
    }
    func testMalformedJSONCannotChooseAnUndisplayedValue() throws {
        let v = try vector("uint256-1")
        let field = "\"value\":\"1\""
        XCTAssertTrue(v.json.contains(field))
        for replacement in ["\"value\":\"1\",\"value\":\"2\"", "\"value\":\"1\",\"\\u0076alue\":\"2\"",
                            "\"value\":1e2", "\"value\":1.0", "\"value\":true", "\"value\":null", "\"value\":\"01\"",
                            "\"value\":\"1\",\"extra\":\"2\""] {
            XCTAssertThrowsError(try v.decode(v.json.replacingOccurrences(of: field, with: replacement)))
        }
        for suffix in ["{}", "null", "\0"] { XCTAssertThrowsError(try v.decode(v.json + suffix)) }
        let overflow = v.json.replacingOccurrences(of: "\"chainId\":\"1\"", with: "\"chainId\":\"18446744073709551616\"")
        XCTAssertNotEqual(overflow, v.json)
        XCTAssertThrowsError(try v.decode(overflow))
    }
    func testReviewRetainsNestedAndLosslessValues() throws {
        let typed = try vector("nested-8").decode()
        let fields = Dictionary(uniqueKeysWithValues: typed.fields.map { ($0.path, $0.value) })
        XCTAssertEqual(fields["message.leaves"], "8")
        XCTAssertEqual(fields["message.leaves[7].amount"], "1606938044258990275541962092341162602522202993782792835301383")
        XCTAssertEqual(fields["message.grid[7][0]"], "-57896044618658097711785492504343953926634992332820282019728792003956564819968")
        XCTAssertEqual(fields["message.raw[0]"], "0x")
        XCTAssertEqual(fields["message.ok"], "true")
        XCTAssertEqual(try vector("literal256").decode().fields.last?.value,
                       "115792089237316195423570985008687907853269984665640564039457584007913129639935")
        for (i, expected) in [(7,"a\\u{202E}b"),(8,"a\\u{200B}b"),(9,"a\\u{0000}b"),(10,"a\\u{000A}b")] {
            XCTAssertEqual(try vector("string-\(i)").decode().fields.last?.value, expected)
        }
        XCTAssertNotEqual(try vector("string-4").decode().digest, try vector("string-5").decode().digest)
    }
    func testRecognizedSignInRejectsCrossOriginAndFieldInjection() throws {
        let account = try vector("binding-base").account
        let text = "example.com wants you to sign in with your Ethereum account:\n\(account)\n\n\nURI: https://example.com/session\nVersion: 1\nChain ID: 1\nNonce: Audit12345\nIssued At: 2026-10-15T07:59:00Z"
        let now = Date(timeIntervalSince1970: 1_792_051_200)
        func parse(_ s: String) throws -> WalletConnectSignIn? {
            try WalletConnectSignIn.parse(Data(s.utf8), account: account, chainID: 1, website: "https://example.com", now: now)
        }
        XCTAssertNotNil(try parse(text))
        for origin in ["example.com.attacker.example", "attacker.example", "example.com@attacker.example", "example.com:444", "http://example.com", "example.com.", "example.com/attacker"] {
            XCTAssertThrowsError(try parse(text.replacingOccurrences(of: "example.com wants", with: origin + " wants")), origin)
        }
        for suffix in ["\nNonce: More12345", "\nChain ID: 56", "\nURI: https://attacker.example", "\nResources:\n- https://example.com\nChain ID: 56"] {
            XCTAssertThrowsError(try parse(text + suffix))
        }
    }
}
