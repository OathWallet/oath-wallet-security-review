import XCTest
@testable import OathAnkr

final class WalletConnectXrplAuditBoundaryTests: XCTestCase {
    // Public deterministic test material only; no wallet or provider is contacted.
    let base = WalletConnectXrplTests()
    func request(_ tx: [String:XrplJSON], extra: [String:XrplJSON] = [:]) throws -> WalletConnectXrplRequest {
        try base.request(tx, extra:extra)
    }
    func testDuplicateAndResourceBounds() throws {
        let encoded = try JSONEncoder().encode(XrplJSON.object(["tx_json":.object(base.tx())]))
        let valid = String(decoding:encoded,as:UTF8.self)
        for name in ["tx_json","submit","autofill"] {
            let json = "{\"\(name)\":null," + valid.dropFirst()
            let duplicate = name == "tx_json" ? json : "{\"\(name)\":false," + json.dropFirst()
            XCTAssertThrowsError(try WalletConnectXrplRequest(method:"xrpl_signTransaction",chain:"xrpl:1",account:base.owner,params:Data(duplicate.utf8)))
        }
        for bytes in [Data(repeating:32,count:150_001),Data([0xff,0xfe]),
                      Data((String(repeating:"[",count:34)+"0"+String(repeating:"]",count:34)).utf8),
                      Data("{\"tx_json\":{\"Account\":\"x\",\"Acc\\u006funt\":\"y\"}}".utf8)] {
            XCTAssertThrowsError(try WalletConnectXrplRequest(method:"xrpl_signTransaction",chain:"xrpl:1",account:base.owner,params:bytes))
        }
        _ = try WalletConnectXrplRequest(method:"xrpl_signTransaction",chain:"xrpl:1",account:base.owner,params:encoded)
    }
    func testAuthorityAndChainBoundaries() throws {
        for (field,value) in [("NetworkID",XrplJSON.number("1")),("Delegate",.string(base.destination)),
                             ("TxnSignature",.string("00")),("SigningPubKey",.string("00")),
                             ("Signers",.array([])),("Account",.string(base.destination))] {
            var tx=base.tx();tx[field]=value;XCTAssertThrowsError(try request(tx),field)
        }
        for chain in ["xrpl:2","xrpl:01","eip155:1",""] { XCTAssertThrowsError(try base.request(chain:chain)) }
        for method in ["xrpl_sign", "xrpl_signTransaction ", "personal_sign", ""] { XCTAssertThrowsError(try base.request(method:method)) }
        for flag in ["submit","autofill"] {
            for value in [XrplJSON.string("true"),.number("1"),.null,.array([])] {
                XCTAssertThrowsError(try request(base.tx(),extra:[flag:value]))
            }
        }
    }
    func testReviewMutationAndTimeBoundaries() throws {
        let r=try base.request(),epoch=Date(timeIntervalSince1970:1_800_000_000)
        let review=WalletConnectXrplReview(request:r,transaction:r.transaction,firstLedger:100,createdAt:epoch)
        for seconds in [0.0,120.0] { _=try r.sign(privateKey:base.key,review:review,now:epoch.addingTimeInterval(seconds)) }
        for seconds in [-0.001,120.001] { XCTAssertThrowsError(try r.sign(privateKey:base.key,review:review,now:epoch.addingTimeInterval(seconds))) }
        for (field,value) in [("Amount",XrplJSON.string("2000000")),("Destination",.string(base.owner)),
                             ("Fee",.string("13")),("Sequence",.number("43")),("LastLedgerSequence",.number("121")),
                             ("DestinationTag",.number("0"))] {
            var tx=base.tx();tx[field]=value
            let changed=WalletConnectXrplReview(request:r,transaction:.object(tx),firstLedger:100,createdAt:epoch)
            XCTAssertThrowsError(try r.sign(privateKey:base.key,review:changed,now:epoch),field)
        }
        for first in [UInt32(0),120,UInt32.max] {
            XCTAssertThrowsError(try WalletConnectXrplReview(request:r,transaction:r.transaction,firstLedger:first,createdAt:epoch).validate())
        }
    }
    func testSignedPayloadTampering() throws {
        let r=try base.request(),review=base.review(r),signed=try r.sign(privateKey:base.key,review:review)
        var wrongSignature=signed.signature;wrongSignature[wrongSignature.count-1] ^= 1
        let variants=[
            WalletConnectXrplSigned(bytes:signed.bytes+Data([0]),hash:signed.hash,transaction:signed.transaction,publicKey:signed.publicKey,signature:signed.signature),
            WalletConnectXrplSigned(bytes:signed.bytes,hash:String(repeating:"0",count:64),transaction:signed.transaction,publicKey:signed.publicKey,signature:signed.signature),
            WalletConnectXrplSigned(bytes:signed.bytes,hash:signed.hash,transaction:signed.transaction,publicKey:signed.publicKey,signature:wrongSignature),
            WalletConnectXrplSigned(bytes:signed.bytes,hash:signed.hash,transaction:signed.transaction,publicKey:try XrplSendCrypto.publicKey(privateKey:Data(repeating:8,count:32)),signature:signed.signature)]
        for v in variants { XCTAssertThrowsError(try r.verify(v,review:review)) }
        try r.verify(signed,review:review)
    }
    func testMultisignOrderingAndPriorSignatureTamper() throws {
        var tx=base.tx();tx["Account"] = .string(base.destination);tx["SigningPubKey"] = .string("")
        for byte in [UInt8(11),7,9] {
            let key=Data(repeating:byte,count:32),account=try XrplSendCrypto.address(privateKey:key)
            let params=XrplJSON.object(["tx_json":.object(tx),"tx_signer":.string(account)])
            let r=try WalletConnectXrplRequest(method:"xrpl_signTransactionFor",chain:"xrpl:1",account:account,params:JSONEncoder().encode(params))
            let review=base.review(r),signed=try r.sign(privateKey:key,review:review)
            try r.verify(signed,review:review);tx=try XCTUnwrap(signed.transaction.fields)
            let accounts=try XCTUnwrap(tx["Signers"]?.array).map{$0["Signer"]["Account"].string!}
            let sorted=try accounts.sorted { try XrplIdentity.accountBytes($0).lexicographicallyPrecedes(XrplIdentity.accountBytes($1)) }
            XCTAssertEqual(accounts,sorted)
        }
        tx["Amount"] = .string("2000000")
        let account=try XrplSendCrypto.address(privateKey:Data(repeating:12,count:32))
        let params=XrplJSON.object(["tx_json":.object(tx),"tx_signer":.string(account)])
        XCTAssertThrowsError(try WalletConnectXrplRequest(method:"xrpl_signTransactionFor",chain:"xrpl:1",account:account,params:JSONEncoder().encode(params)))
    }
    func testMemoUnknownFieldsAndNumericRoundTrip() throws {
        for value in [XrplJSON.number("9007199254740993"),.number("4294967296"),.number("-1"),.number("1.5"),.bool(true)] {
            var tx=base.tx();tx["DestinationTag"]=value;XCTAssertThrowsError(try request(tx))
        }
        var tx=base.tx();tx["Memos"] = .array([.object(["Memo":.object(["MemoData":.string("74657374"),"Hidden":.string("00")])])])
        XCTAssertThrowsError(try request(tx))
        for tag in ["0","4294967295"] {
            tx=base.tx();tx["DestinationTag"] = .number(tag)
            let r=try request(tx),review=base.review(r),signed=try r.sign(privateKey:base.key,review:review)
            XCTAssertEqual(signed.transaction["DestinationTag"],.number(tag))
        }
    }
}
