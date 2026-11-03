import XCTest
@testable import OathAnkr

final class NearAuditMultisigTests: XCTestCase {
    func vectors() throws -> [NearJSON] {
        let path=try XCTUnwrap(ProcessInfo.processInfo.environment["OATH_NEAR_AUDIT_VECTORS"])
        let f=try JSONDecoder().decode(NearJSON.self,from:Data(contentsOf:URL(fileURLWithPath:path)))
        let rows=try XCTUnwrap(f["bundles"].array);XCTAssertEqual(rows.count,50);return rows
    }
    func bytes(_ v:NearJSON,_ field:String) throws -> Data { try XCTUnwrap(Data(base64Encoded:try XCTUnwrap(v[field].string))) }
    func seeds(_ v:NearJSON) throws -> [Data] { try XCTUnwrap(v["signerSeeds"].array).map { try XCTUnwrap(Data(base64Encoded:try XCTUnwrap($0.string))) } }
    func plan(_ v:NearJSON) throws -> NearSendPlan {
        let keys=try XCTUnwrap(v["publicKeys"].array).map { try XCTUnwrap(Data(base64Encoded:try XCTUnwrap($0.string))) }
        let required=try XCTUnwrap(v["required"].integer),stage=try XCTUnwrap(NearMultisigContext.Stage(rawValue:try XCTUnwrap(v["stage"].string)))
        let nonce=try XCTUnwrap(UInt64(try XCTUnwrap(v["nonce"].string)))
        let policy=try NearMultisigPolicy(bootstrap:bytes(v,"bootstrap"),required:Int(required),publicKeys:keys)
        let context=NearMultisigContext(policy:policy,stage:stage,requestID:try XCTUnwrap(UInt32(exactly:try XCTUnwrap(v["requestID"].integer))),nonces:Array(repeating:nonce,count:stage == .transfer ? Int(required):1))
        let token=v["reference"].string != "native",registered=v["storage"].string != "0"
        return NearSendPlan(network:.testnet,sender:try XCTUnwrap(v["sender"].string),recipient:try XCTUnwrap(v["recipient"].string),reference:try XCTUnwrap(v["reference"].string),publicKey:stage == .transfer ? keys[0]:policy.bootstrap,decimals:24,requestedAmount:try XCTUnwrap(v["amount"].string),amount:try XCTUnwrap(v["amount"].string),assetBalance:try XCTUnwrap(v["balance"].string),nativeBalance:try XCTUnwrap(v["balance"].string),reserve:"0",storageDeposit:try XCTUnwrap(v["storage"].string),fee:"1",gasPriceCeiling:"1",gas:token ? 50_000_000_000_000:0,storageGas:registered ? 30_000_000_000_000:0,nonce:nonce,blockHash:try XCTUnwrap(v["block"].string),blockHeight:1,validityPeriod:86400,multisig:context)
    }
    func testIndependentBundleBytesAndSignatures() throws {
        var output=[[String:NearJSON]]();var total=0
        for v in try vectors() {
            let p=try plan(v),expected=try XCTUnwrap(v["parts"].array)
            let raw=try NearSendCrypto.multisigRaw(p),s=try NearSendCrypto.sign(p,privateKeys:Array(seeds(v).reversed())),parts=try XCTUnwrap(s.multisigParts)
            XCTAssertEqual(raw.count,expected.count);XCTAssertEqual(parts.count,expected.count)
            for i in expected.indices {
                XCTAssertEqual(raw[i].raw,try bytes(expected[i],"raw"));XCTAssertEqual(parts[i].bytes,raw[i].raw+Data([0])+parts[i].signature)
                XCTAssertEqual(parts[i].signature.count,64);XCTAssertEqual(parts[i].hash,expected[i]["hash"].string)
                XCTAssertEqual(parts[i].publicKey,try bytes(expected[i],"publicKey"));total+=1
            }
            let sdkParts=try expected.map { try NearMultisigPart(bytes:bytes($0,"signed"),publicKey:bytes($0,"publicKey"),signature:bytes($0,"signature"),hash:XCTUnwrap($0["hash"].string)) }
            let last=try XCTUnwrap(sdkParts.last)
            XCTAssertNoThrow(try NearSendCrypto.verify(.init(bytes:last.bytes,publicKey:last.publicKey,signature:last.signature,hash:last.hash,multisigParts:sdkParts),plan:p))
            output.append(["id":v["id"],"parts":.array(parts.map { .string($0.bytes.base64EncodedString()) })])
        }
        XCTAssertEqual(total,188)
        let path=try XCTUnwrap(ProcessInfo.processInfo.environment["OATH_NEAR_AUDIT_SIGNATURES"])
        try JSONEncoder().encode(output).write(to:URL(fileURLWithPath:path),options:.atomic)
    }
    func testRestartRoundtripRetainsEveryPartAndPlan() throws {
        for v in try vectors() {
            let p=try plan(v),s=try NearSendCrypto.sign(p,privateKeys:seeds(v))
            let restored=try JSONDecoder().decode(NearSendPlan.self,from:JSONEncoder().encode(p))
            let restoredSigned=try JSONDecoder().decode(NearSignedSend.self,from:JSONEncoder().encode(s))
            XCTAssertEqual(restored,p);XCTAssertEqual(restoredSigned,s)
            XCTAssertNoThrow(try NearSendCrypto.verify(restoredSigned,plan:restored))
        }
    }
    func testEverySignatureAndBundleOrderIsBound() throws {
        for v in try vectors() {
            let p=try plan(v),s=try NearSendCrypto.sign(p,privateKeys:seeds(v)),parts=try XCTUnwrap(s.multisigParts)
            func reject(_ changed:[NearMultisigPart]) {
                XCTAssertThrowsError(try NearSendCrypto.verify(.init(bytes:s.bytes,publicKey:s.publicKey,signature:s.signature,hash:s.hash,multisigParts:changed),plan:p))
            }
            for i in parts.indices {
                var changed=parts,sig=parts[i].signature;sig[0] ^= 1
                changed[i] = .init(bytes:parts[i].bytes,publicKey:parts[i].publicKey,signature:sig,hash:parts[i].hash)
                reject(changed)
            }
            reject(Array(parts.dropLast()));reject(parts+[parts[0]])
            if parts.count>1 { reject(Array(parts.reversed())) }
        }
    }
}
