import XCTest
import CryptoKit
@testable import OathAnkr

final class MultichainConsentReviewTests: XCTestCase {
    let date = Date(timeIntervalSince1970: 1_800_000_000)
    let sui = WalletConnectSuiTests()
    let near = WalletConnectNearTests()
    let dot = WalletConnectPolkadotTests()

    func testSuiEverySingleByteAlterationCannotReuseConsent() throws {
        let original = try sui.request(), review = try sui.review(original, date:date)
        let raw = try XCTUnwrap(original.transaction)
        var valid = 0, malformed = 0
        for index in raw.indices {
            var bytes = raw; bytes[index] ^= 1
            let altered: WalletConnectSuiRequest
            do { altered = try sui.request(value:bytes.base64EncodedString()) }
            catch { malformed += 1; continue }
            XCTAssertNotEqual(altered, original)
            XCTAssertThrowsError(try altered.sign(privateKey:Data(repeating:7,count:32),review:review,now:date), "Altered byte \(index)")
            // A fresh consent can sign the same structurally valid transaction.
            let ownReview = try sui.review(altered,date:date)
            let signed = try altered.sign(privateKey:Data(repeating:7,count:32),review:ownReview,now:date)
            XCTAssertEqual(signed.transaction?.bytes, bytes)
            valid += 1
        }
        XCTAssertGreaterThan(valid, 0); XCTAssertGreaterThan(malformed, 0)
        XCTAssertEqual(valid + malformed, raw.count)
        print("CORPUS sui single-byte valid=\(valid) malformed=\(malformed) total=\(raw.count)")
    }

    func testSuiMessageIntentAndConsentTimeBoundaries() throws {
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation:Data(repeating:7,count:32))
        for text in ["hello", "SGVsbG8=", "مرحبا 🌍", String(repeating:"x",count:8192)] {
            let r = try sui.request("sui_signPersonalMessage",value:text)
            let signed = try XCTUnwrap(Data(base64Encoded: r.sign(privateKey:key.rawRepresentation).signature))
            let signature = signed.dropFirst().prefix(64)
            let bytes = Data(text.utf8)
            XCTAssertTrue(key.publicKey.isValidSignature(signature,for:SuiSendCrypto.hash(Data([3,0,0])+SuiBCS.vector(bytes))))
            XCTAssertFalse(key.publicKey.isValidSignature(signature,for:SuiSendCrypto.hash(Data([0,0,0])+bytes)))
            XCTAssertFalse(key.publicKey.isValidSignature(signature,for:bytes))
        }
        let r = try sui.request(), review = try sui.review(r,date:date)
        for offset:TimeInterval in [-1, 121] {
            XCTAssertThrowsError(try r.sign(privateKey:key.rawRepresentation,review:review,now:date.addingTimeInterval(offset)))
        }
        for offset:TimeInterval in [0, 120] {
            XCTAssertNoThrow(try r.sign(privateKey:key.rawRepresentation,review:review,now:date.addingTimeInterval(offset)))
        }
    }

    func nearBatch(_ bytes:[Data]) throws -> WalletConnectNearRequest {
        try .init(method:"near_signTransactions",chain:"near:testnet",account:"sender.testnet",params:JSONEncoder().encode(NearJSON.object(["transactions":.array(bytes.map(WalletConnectNearRequest.buffer))])))
    }
    func nearReview(_ r:WalletConnectNearRequest) throws -> WalletConnectNearReview {
        .init(request:r,fee:"1",transactions:try r.transactions.map(WalletConnectNearTransaction.init),createdAt:date)
    }
    func testNearEveryBatchLengthBindsBytesOrderAndNonce() throws {
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation:near.key)
        var checked = 0
        for size in 1...16 {
            let raws = try (0..<size).map { try near.raw(nonce:9_007_199_254_740_993+UInt64($0)) }
            let r = try nearBatch(raws), review = try nearReview(r)
            let response = try XCTUnwrap(r.sign(privateKey:near.key,review:review,now:date).array)
            XCTAssertEqual(response.count,size)
            for index in raws.indices {
                let signed = Data(try XCTUnwrap(response[index]["data"].array).map { UInt8($0.integer!) })
                XCTAssertEqual(signed.prefix(raws[index].count),raws[index])
                XCTAssertTrue(key.publicKey.isValidSignature(signed.suffix(64),for:Data(SHA256.hash(data:raws[index]))))
                var changed = raws
                // A valid changed transfer amount keeps nonce ordering intact.
                changed[index] = try near.raw(nonce:9_007_199_254_740_993+UInt64(index),actions:[Data([3])+NearSendCrypto.u128("2000000000000000000000")])
                let altered = try nearBatch(changed)
                XCTAssertThrowsError(try altered.sign(privateKey:near.key,review:review,now:date))
                XCTAssertNoThrow(try altered.sign(privateKey:near.key,review:nearReview(altered),now:date))
                checked += 1
            }
            if size > 1 {
                XCTAssertThrowsError(try nearBatch(Array(raws.reversed())))
                XCTAssertThrowsError(try nearBatch(Array(repeating:raws[0],count:size)))
            }
            for offset:TimeInterval in [-1,121] { XCTAssertThrowsError(try r.sign(privateKey:near.key,review:review,now:date.addingTimeInterval(offset))) }
            for offset:TimeInterval in [0,120] { XCTAssertNoThrow(try r.sign(privateKey:near.key,review:review,now:date.addingTimeInterval(offset))) }
        }
        XCTAssertEqual(checked,136)
        print("CORPUS near batches=16 altered-items=\(checked)")
    }

    func testNearAuthorityChangesRemainExplicitAndCannotReplaceTransfer() throws {
        let publicKey = try NearSendCrypto.publicKey(privateKey:Data(repeating:9,count:32))
        let add = Data([5,0])+publicKey+NearSendCrypto.le(UInt64(0))+Data([1])
        let remove = Data([6,0])+publicKey
        let destroy = Data([7])+NearSendCrypto.text("beneficiary.testnet")
        let original = try near.request(near.raw()), review = try nearReview(original)
        for (action,kind,text) in [(add,UInt8(5),"FULL ACCESS"),(remove,6,"Delete access key"),(destroy,7,"DELETE ACCOUNT")] {
            let r = try near.request(near.raw(actions:[action]))
            let parsed = try WalletConnectNearTransaction(r.transactions[0])
            XCTAssertEqual(parsed.actions.count,1); XCTAssertEqual(parsed.actions[0].kind,kind)
            XCTAssertTrue(parsed.actions[0].description.contains(text))
            if kind == 5 { XCTAssertTrue(parsed.actions[0].fullAccess) }
            if kind == 7 { XCTAssertTrue(parsed.actions[0].description.contains("beneficiary.testnet")) }
            else { XCTAssertTrue(parsed.actions[0].description.contains(NearSendCrypto.keyString(publicKey))) }
            XCTAssertThrowsError(try r.sign(privateKey:near.key,review:review,now:date))
            XCTAssertNoThrow(try r.sign(privateKey:near.key,review:nearReview(r),now:date))
        }
    }

    func testPolkadotEveryFixtureRejectsAlteredConsent() throws {
        var checked = 0
        for f in try dot.fixtures().vectors {
            let original = try dot.request(f.params,account:f.account), review = dot.review(original,date:date)
            XCTAssertNoThrow(try original.sign(privateKey:Data(repeating:1,count:32),review:review,now:date))
            let changes:[(String,TronJSON)] = [
                ("nonce",.string("0x12345678")),("tip",.string("0x12345678")),
                ("specVersion",.string("0x12345678")),("transactionVersion",.string("0x12345678")),
                ("method",.string(PolkadotIdentity.hex(original.call+Data([0]))))
            ]
            for (field,value) in changes {
                var body = f.params.fields!, payload = body["transactionPayload"]!.fields!
                payload[field] = value; body["transactionPayload"] = .object(payload)
                let altered = try dot.request(.object(body),account:f.account)
                XCTAssertNotEqual(altered,original)
                XCTAssertThrowsError(try altered.sign(privateKey:Data(repeating:1,count:32),review:review,now:date),field)
                XCTAssertNoThrow(try altered.sign(privateKey:Data(repeating:1,count:32),review:dot.review(altered,date:date),now:date))
                checked += 1
            }
            for offset:TimeInterval in [-6,91] { XCTAssertThrowsError(try original.sign(privateKey:Data(repeating:1,count:32),review:review,now:date.addingTimeInterval(offset))) }
            for offset:TimeInterval in [-5,0,90] { XCTAssertNoThrow(try original.sign(privateKey:Data(repeating:1,count:32),review:review,now:date.addingTimeInterval(offset))) }
        }
        XCTAssertGreaterThan(checked,0)
        print("CORPUS polkadot altered-payloads=\(checked)")
    }

    func testPolkadotMessageDomainCannotSignRawTransactionBytes() throws {
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation:Data(repeating:1,count:32))
        for f in try dot.fixtures().vectors {
            let tx = try dot.request(f.params,account:f.account)
            let raw = try tx.encoded().payload
            let params:TronJSON = .object(["address":.string(f.account),"data":.string(PolkadotIdentity.hex(raw)),"type":.string("bytes")])
            let r = try dot.request(params,account:f.account,method:"polkadot_signMessage")
            let signature = try PolkadotIdentity.bytes(XCTUnwrap(r.sign(privateKey:key.rawRepresentation)["signature"].string))
            XCTAssertTrue(try key.publicKey.isValidSignature(signature,for:XCTUnwrap(r.message)))
            XCTAssertFalse(key.publicKey.isValidSignature(signature,for:raw))
            XCTAssertThrowsError(try r.sign(privateKey:Data(repeating:2,count:32)))
        }
    }

    func testSuiConsentBindingMutationControl() throws {
        let original = try sui.request(), review = try sui.review(original,date:date)
        var raw = try XCTUnwrap(original.transaction); raw[raw.count-9] ^= 1
        let params = ["address":sui.account,"transaction":sui.bytes]
        let changed = [
            try sui.request(value:raw.base64EncodedString()),
            try sui.request("sui_signAndExecuteTransaction"),
            try WalletConnectSuiRequest(method:"sui_signTransaction",chain:"sui:mainnet",account:sui.account,params:JSONEncoder().encode(params))
        ]
        for (index,r) in changed.enumerated() {
            XCTAssertThrowsError(try r.sign(privateKey:Data(repeating:7,count:32),review:review,now:date),"Consent binding removed: \(index)")
            XCTAssertNoThrow(try r.sign(privateKey:Data(repeating:7,count:32),review:sui.review(r,date:date),now:date))
        }
    }
}
