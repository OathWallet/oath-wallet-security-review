import XCTest
@testable import OathAnkr

final class XrplAuditSigningTests: XCTestCase {
    struct Signer: Decodable { let account: String, key: String }
    struct Vector: Decodable { let kind: String, value: String, reference: String, fee: String, bytes: String, hash: String; let threshold: Int, tag: UInt32? }
    struct Hash: Decodable { let input: String, digest: String }
    struct Fixture: Decodable { let account: String, publicKey: String, key: String, recipient: String; let signers: [Signer], vectors: [Vector], hashes: [Hash] }
    func fixture() throws -> Fixture {
        let path = try XCTUnwrap(ProcessInfo.processInfo.environment["OATH_XRPL_REVIEW_VECTOR"])
        return try JSONDecoder().decode(Fixture.self,from:Data(contentsOf:URL(fileURLWithPath:path)))
    }
    func plan(_ f: Fixture,_ v: Vector) throws -> XrplSendPlan {
        let setup = XrplMultisigSetup(rawValue:v.kind), auth = ["trust","authorize"].contains(v.kind), closure=v.kind == "closure"
        let amount = v.reference.contains(".") ? try XrplIdentity.issuedAmount(v.value) : v.value
        let balance: UInt64 = closure ? 1_000_000 : 100_000_000_000_000_000
        let policy = v.threshold > 0 ? try XrplMultisigPolicy(account:f.account,required:v.threshold,signers:f.signers.map(\.account)) : nil
        return .init(network:.testnet,sender:f.account,recipient:setup != nil || auth ? f.account:f.recipient,reference:v.reference,destinationTag:v.tag,
            requestedAmount:closure ? String(balance):amount,amount:amount,assetDebit:auth ? "0":amount,assetBalance:v.reference == "native" ? String(balance):amount,
            nativeBalance:balance,reserve:1_000_000,fee:try XCTUnwrap(UInt64(v.fee)),sequence:42,firstLedger:380,lastLedger:400,
            recipientReserve:closure ? 0:nil,accountDeletionFee:closure ? UInt64(v.fee):nil,multisig:policy,multisigSetup:setup,tokenAuthorization:auth ? true:nil)
    }
    func sign(_ f: Fixture,_ v: Vector,_ p: XrplSendPlan) throws -> XrplSignedSend {
        if v.threshold > 0 && p.multisigSetup == nil { return try XrplMultisigCrypto.sign(p,privateKeys:f.signers.prefix(v.threshold).map{try TronIdentity.hex($0.key)}) }
        return try XrplSendCrypto.sign(p,privateKey:TronIdentity.hex(f.key))
    }
    func changed(_ p: XrplSendPlan,_ field: String,_ value: Any) throws -> XrplSendPlan {
        var j=try XCTUnwrap(JSONSerialization.jsonObject(with:JSONEncoder().encode(p)) as? [String:Any]);j[field]=value
        return try JSONDecoder().decode(XrplSendPlan.self,from:JSONSerialization.data(withJSONObject:j))
    }
    func testIndependentSDKBytesAndHashes() throws {
        let f=try fixture();XCTAssertEqual(f.vectors.count,61)
        XCTAssertEqual(try XrplSendCrypto.hex(XrplSendCrypto.publicKey(privateKey:TronIdentity.hex(f.key))),f.publicKey)
        for v in f.vectors {
            let p=try plan(f,v), signed=try sign(f,v,p)
            XCTAssertEqual(XrplSendCrypto.hex(signed.bytes),v.bytes,"\(v.kind)/\(v.threshold)/\(v.value)")
            XCTAssertEqual(signed.hash,v.hash)
            try XrplSendCrypto.verify(signed,plan:p)
        }
    }
    func testAlteredPlanCannotReuseSignature() throws {
        let f=try fixture()
        for v in f.vectors {
            let p=try plan(f,v),signed=try sign(f,v,p)
            for (field,value) in [("sequence",43 as Any),("lastLedger",401 as Any),("fee",p.fee+1 as Any),("destinationTag",7 as Any),("recipient",f.signers[0].account as Any),("amount","0" as Any)] {
                // Configuration intents already carry zero Amount and do not serialize it.
                if field == "amount" && p.amount == "0" { continue }
                let altered=try changed(p,field,value)
                XCTAssertThrowsError(try XrplSendCrypto.verify(signed,plan:altered),"\(v.kind):\(field)")
            }
        }
    }
    func testCorruptedEnvelopeAndSignerSetAreRejected() throws {
        let f=try fixture()
        for v in f.vectors {
            let p=try plan(f,v),signed=try sign(f,v,p)
            let appended=XrplSignedSend(bytes:signed.bytes+Data([0]),publicKey:signed.publicKey,signature:signed.signature,hash:XrplSendCrypto.transactionHash(signed.bytes+Data([0])),signers:signed.signers)
            XCTAssertThrowsError(try XrplSendCrypto.verify(appended,plan:p))
            let wrongHash=XrplSignedSend(bytes:signed.bytes,publicKey:signed.publicKey,signature:signed.signature,hash:String(repeating:"0",count:64),signers:signed.signers)
            XCTAssertThrowsError(try XrplSendCrypto.verify(wrongHash,plan:p))
            if let signers=signed.signers {
                let first=try XCTUnwrap(signers.first)
                let missing=XrplSignedSend(bytes:signed.bytes,publicKey:signed.publicKey,signature:signed.signature,hash:signed.hash,signers:Array(signers.dropLast()))
                XCTAssertThrowsError(try XrplSendCrypto.verify(missing,plan:p))
                let repeated=XrplSignedSend(bytes:signed.bytes,publicKey:Data(),signature:Data(),hash:signed.hash,signers:Array(repeating:first,count:signers.count+1))
                XCTAssertThrowsError(try XrplSendCrypto.verify(repeated,plan:p))
            } else {
                var signature=signed.signature;signature[signature.count-1] ^= 1
                let bad=XrplSignedSend(bytes:signed.bytes,publicKey:signed.publicKey,signature:signature,hash:signed.hash)
                XCTAssertThrowsError(try XrplSendCrypto.verify(bad,plan:p))
            }
        }
    }
    func testRIPEMDBlockBoundariesMatchOpenSSL() throws {
        let f=try fixture();XCTAssertEqual(f.hashes.count,13)
        for v in f.hashes { XCTAssertEqual(XrplSendCrypto.hex(XrplRIPEMD160.hash(v.input.isEmpty ? Data() : try TronIdentity.hex(v.input))).lowercased(),v.digest) }
    }
}
