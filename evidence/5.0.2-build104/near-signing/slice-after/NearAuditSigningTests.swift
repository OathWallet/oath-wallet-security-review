import XCTest
import CryptoKit
@testable import OathAnkr

final class NearAuditSigningTests: XCTestCase {
    func fixture() throws -> NearJSON {
        let path = try XCTUnwrap(ProcessInfo.processInfo.environment["OATH_NEAR_AUDIT_VECTORS"])
        return try JSONDecoder().decode(NearJSON.self,from:Data(contentsOf:URL(fileURLWithPath:path)))
    }
    func bytes(_ value:NearJSON,_ field:String) throws -> Data { try XCTUnwrap(Data(base64Encoded:try XCTUnwrap(value[field].string))) }
    func plan(_ v:NearJSON) throws -> NearSendPlan {
        let token=v["mode"].string != "native",registered=v["mode"].string == "registration"
        return NearSendPlan(network:.testnet,sender:try XCTUnwrap(v["sender"].string),recipient:"recipient.testnet",reference:token ? "wrap.testnet":"native",publicKey:try bytes(v,"publicKey"),decimals:24,
            requestedAmount:try XCTUnwrap(v["amount"].string),amount:try XCTUnwrap(v["amount"].string),assetBalance:try XCTUnwrap(v["balance"].string),nativeBalance:try XCTUnwrap(v["balance"].string),reserve:"0",storageDeposit:registered ? "1000":"0",fee:"1",gasPriceCeiling:"1",gas:token ? 50_000_000_000_000:0,storageGas:registered ? 30_000_000_000_000:0,nonce:try XCTUnwrap(UInt64(try XCTUnwrap(v["nonce"].string))),blockHash:try XCTUnwrap(v["block"].string),blockHeight:100,validityPeriod:86400)
    }
    func signed(_ v:NearJSON) throws -> NearSignedSend { try .init(bytes:bytes(v,"signed"),publicKey:bytes(v,"publicKey"),signature:bytes(v,"signature"),hash:XCTUnwrap(v["hash"].string)) }
    func request(_ v:NearJSON,raw:Data?=nil) throws -> WalletConnectNearRequest {
        try WalletConnectNearRequest(method:"near_signTransaction",chain:"near:testnet",account:XCTUnwrap(v["sender"].string),params:JSONEncoder().encode(NearJSON.object(["transaction":WalletConnectNearRequest.buffer(raw ?? bytes(v,"raw"))])))
    }
    func testIndependentPlanBytesHashesAndSignatures() throws {
        let vectors=try XCTUnwrap(fixture()["plans"].array);XCTAssertEqual(vectors.count,72)
        for v in vectors {
            let p=try plan(v),key=try bytes(v,"seed")
            XCTAssertNoThrow(try p.validate())
            XCTAssertEqual(try NearSendCrypto.publicKey(privateKey:key),try bytes(v,"publicKey"))
            XCTAssertEqual(try NearSendCrypto.raw(p),try bytes(v,"raw"))
            XCTAssertNoThrow(try NearSendCrypto.verify(signed(v),plan:p))
            let result=try NearSendCrypto.sign(p,privateKey:key)
            XCTAssertEqual(result.hash,v["hash"].string)
        }
    }
    func testIndependentActionsAndProductionSignatures() throws {
        let f=try fixture(),plans=try XCTUnwrap(f["plans"].array),actions=try XCTUnwrap(f["actions"].array)
        XCTAssertEqual(actions.count,10)
        var output=[[String:NearJSON]]()
        for (i,v) in (plans+actions).enumerated() {
            let raw=try bytes(v,"raw"),tx=try WalletConnectNearTransaction(raw),r=try request(v)
            XCTAssertEqual(tx.sender,v["sender"].string);XCTAssertEqual(tx.receiver,v["receiver"].string)
            XCTAssertEqual(String(tx.nonce),v["nonce"].string)
            if i>=72 { XCTAssertEqual(tx.actions.count,1);XCTAssertEqual(UInt64(tx.actions[0].kind),v["kind"].integer) }
            let review=WalletConnectNearReview(request:r,fee:"1",transactions:[tx],createdAt:.now)
            XCTAssertNoThrow(try WalletConnectNearAccess.verify(signed(v),review:review))
            let result=try r.sign(privateKey:bytes(v,"seed"),review:review)
            let buffer=try XCTUnwrap(result["data"].array).map { try XCTUnwrap($0.integer).exactByte() }
            output.append(["index":.number(String(i)),"signed":.string(Data(buffer).base64EncodedString())])
        }
        let path=try XCTUnwrap(ProcessInfo.processInfo.environment["OATH_NEAR_AUDIT_SIGNATURES"])
        try JSONEncoder().encode(output).write(to:URL(fileURLWithPath:path),options:.atomic)
    }
    func testChangedPlansAndTamperedSignaturesAreRejected() throws {
        for v in try XCTUnwrap(fixture()["plans"].array) {
            let p=try plan(v),s=try signed(v)
            for edit in [["recipient":"changed.testnet"],["amount":"2"],["blockHash":SuiSendCrypto.base58(Data(repeating:4,count:32))]] {
                let changed=try NearSendTests.changing(p,edit)
                XCTAssertThrowsError(try NearSendCrypto.verify(s,plan:changed))
            }
            var sig=s.signature;sig[0] ^= 1
            XCTAssertThrowsError(try NearSendCrypto.verify(.init(bytes:s.bytes,publicKey:s.publicKey,signature:sig,hash:s.hash),plan:p))
        }
    }
    func testNonzeroOriginDataSliceMatchesBytes() throws {
        let v=try XCTUnwrap(fixture()["actions"].array?.first),raw=try bytes(v,"raw")
        let padded=Data([99])+raw,slice=padded.dropFirst()
        XCTAssertEqual(slice.startIndex,1)
        XCTAssertEqual(try WalletConnectNearTransaction(slice),try WalletConnectNearTransaction(raw))
    }
    func testTruncatedAndTrailingActionBytesAreRejected() throws {
        for v in try XCTUnwrap(fixture()["actions"].array) {
            let raw=try bytes(v,"raw")
            for size in 0..<raw.count { XCTAssertThrowsError(try WalletConnectNearTransaction(Data(raw.prefix(size)))) }
            XCTAssertThrowsError(try WalletConnectNearTransaction(raw+Data([0])))
        }
    }
}
private extension UInt64 {
    func exactByte() throws -> UInt8 { try XCTUnwrap(UInt8(exactly:self)) }
}
