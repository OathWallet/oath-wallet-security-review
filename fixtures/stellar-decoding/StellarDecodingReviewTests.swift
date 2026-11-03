import Foundation
import XCTest
import stellarsdk
@testable import OathAnkr

final class StellarDecodingReviewTests: XCTestCase {
    func vectors() throws -> StellarJSON {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "StellarReview", withExtension: "json", subdirectory: "Fixtures"))
        return try JSONDecoder().decode(StellarJSON.self, from: Data(contentsOf: url))
    }
    func rows(_ key: String) throws -> [StellarJSON] { try XCTUnwrap(vectors()[key].array) }
    func string(_ row: StellarJSON, _ key: String) throws -> String { try XCTUnwrap(row[key].string) }

    func testIndependentStrkeyCorpusAndSDKAgreement() throws {
        let values = try rows("addresses"); XCTAssertEqual(values.count, 64)
        for row in values {
            let raw = try XCTUnwrap(row["bytes"].array).map { UInt8(try XCTUnwrap($0.integer)) }
            let account = try string(row,"account"), contract = try string(row,"contract")
            XCTAssertEqual(try StellarIdentity.address(account), account)
            XCTAssertEqual(try StellarIdentity.bytes(account,version:48), raw)
            XCTAssertEqual(StellarIdentity.encode(raw,version:48), account)
            XCTAssertEqual(try StellarIdentity.reference(contract), contract)
            XCTAssertEqual(try PublicKey(raw).accountId, account)
            XCTAssertEqual(try Data(raw).encodeContractId(), contract)
            XCTAssertThrowsError(try StellarIdentity.address(string(row,"bad_checksum")))
            XCTAssertThrowsError(try StellarIdentity.address(account.lowercased()))
            XCTAssertThrowsError(try StellarIdentity.address(contract))
            XCTAssertThrowsError(try StellarIdentity.reference(account))
            XCTAssertEqual(try StellarDecoding.scAddress(row["sc_account"]),account)
            XCTAssertEqual(try StellarDecoding.scAddress(row["sc_contract"]),contract)
            XCTAssertEqual(try StellarDecoding.scAddress(row["sc_muxed"]),account)
        }
    }
    func testIndependentAssetContractNetworkAndIssuerBinding() throws {
        let values = try rows("contracts"); XCTAssertEqual(values.count,128)
        for row in values {
            XCTAssertEqual(try StellarIdentity.contract(code:string(row,"code"),issuer:string(row,"issuer"),network:string(row,"network")),try string(row,"contract"))
        }
        XCTAssertEqual(try string(vectors(),"native_contract"),StellarIdentity.nativeContract)
        let issuer = try string(rows("addresses")[0],"account")
        for code in ["", "abcdefghijklmn", "A B", "USD/", "€", "Ａ", "x\0y"] {
            XCTAssertThrowsError(try StellarIdentity.contract(code:code,issuer:issuer))
        }
    }
    func testExactDecimalAndSignedXDRCorpus() throws {
        let values = try rows("amounts"); XCTAssertEqual(values.count,128)
        for row in values {
            let decimals = Int(try XCTUnwrap(row["decimals"].integer))
            let n = try string(row,"integer")
            XCTAssertEqual(try StellarIdentity.atomic(string(row,"decimal"),decimals:decimals),n)
            XCTAssertEqual(try StellarDecoding.scAmount(row["xdr"]),n)
            XCTAssertEqual(try StellarDecoding.scAmount(row["negative_xdr"],allowNegative:true),try string(row,"negative"))
            if n != "0" { XCTAssertThrowsError(try StellarDecoding.scAmount(row["negative_xdr"])) }
        }
        for bad in ["-1","+1","1e7","NaN","Infinity","1,000"," 1","1 ",".1","1.","١","１","1.00000001"] {
            XCTAssertThrowsError(try StellarIdentity.atomic(bad))
        }
        XCTAssertThrowsError(try StellarIdentity.atomic("1",decimals:-1))
        XCTAssertThrowsError(try StellarIdentity.atomic("1",decimals:256))
        XCTAssertThrowsError(try StellarIdentity.uint("170141183460469231731687303715884105728"))
    }
    func testCAP67AmountMapVariants() throws {
        let values = try rows("maps"); XCTAssertEqual(values.count,72)
        for row in values { XCTAssertEqual(try StellarDecoding.scAmount(row["xdr"]),try string(row,"amount")) }
    }
    func testTruncatedAndUnknownXDRCannotProduceValues() throws {
        for row in try rows("addresses").prefix(8) {
            for key in ["sc_account","sc_contract","sc_muxed"] {
                let data = try XCTUnwrap(Data(base64Encoded:string(row,key)))
                for count in 0..<data.count { XCTAssertThrowsError(try StellarDecoding.scAddress(.string(data.prefix(count).base64EncodedString()))) }
                XCTAssertThrowsError(try StellarDecoding.scAddress(.string((data+Data([0])).base64EncodedString())))
            }
        }
        for row in try rows("maps").prefix(9) {
            let data = try XCTUnwrap(Data(base64Encoded:string(row,"xdr")))
            for count in 0..<data.count { XCTAssertThrowsError(try StellarDecoding.scAmount(.string(data.prefix(count).base64EncodedString()))) }
        }
        let values=try rows("malformed"); XCTAssertEqual(values.count,256)
        for value in values {
            XCTAssertThrowsError(try StellarDecoding.scAmount(value))
            XCTAssertThrowsError(try StellarDecoding.scAddress(value))
            XCTAssertThrowsError(try StellarDecoding.scText(value))
        }
        for bad in ["%", "A",String(repeating:"A",count:4097)] {
            XCTAssertThrowsError(try StellarDecoding.scAmount(.string(bad)))
        }
    }
    func testFeeAndMovementStateOwnerContractBinding() throws {
        let values = try rows("events"); XCTAssertEqual(values.count,12)
        for row in values {
            let owner=try string(row,"owner"), event=try StellarDecoding.event(row["row"],owner:owner)
            if row["accepted"] == .bool(false) { XCTAssertNil(event); continue }
            let value = try XCTUnwrap(event)
            XCTAssertEqual(value.amount,try string(row,"expected_amount"))
            XCTAssertEqual(value.successful,row["row"]["inSuccessfulContractCall"] == .bool(true))
            XCTAssertEqual(value.direction,try string(row,"direction"))
            XCTAssertEqual(value.reference,"native")
            let third=try string(rows("addresses")[2],"account")
            XCTAssertThrowsError(try StellarDecoding.event(row["row"],owner:third))
            if value.kind == "fee" {
                var fields=try XCTUnwrap(row["row"].fields)
                fields["contractId"] = try rows("addresses")[0]["contract"]
                XCTAssertThrowsError(try StellarDecoding.event(.object(fields),owner:owner))
            }
        }
    }
    func testHoldingsBindOwnerAmountsAndMetadata() throws {
        let owner=try string(rows("addresses")[0],"account"), issuer=try string(rows("addresses")[1],"account")
        for row in try rows("amounts") {
            var holding:[String:StellarJSON] = ["blockchain":.string("stellar_soroban"),"holderAddress":.string(owner),"contractAddress":try rows("addresses")[0]["contract"],"tokenDecimals":row["decimals"],"balanceRawInteger":row["integer"],"balance":row["decimal"],"tokenName":.string("Synthetic token"),"tokenSymbol":.string("SYN")]
            XCTAssertEqual(try StellarDecoding.indexedHolding(.object(holding),owner:owner).amount,try string(row,"integer"))
            XCTAssertThrowsError(try StellarDecoding.indexedHolding(.object(holding),owner:issuer))
            holding["balanceRawInteger"] = .string(row["integer"] == .string("0") ? "1":"0")
            XCTAssertThrowsError(try StellarDecoding.indexedHolding(.object(holding),owner:owner))
            holding["balanceRawInteger"] = row["integer"]
            holding["blockchain"] = .string("ethereum")
            XCTAssertThrowsError(try StellarDecoding.indexedHolding(.object(holding),owner:owner))
        }
        let balance:StellarJSON = .object(["asset_type":.string("native"),"balance":.string("1.0000001")])
        let valid:StellarJSON = .object(["account_id":.string(owner),"balances":.array([balance])])
        XCTAssertEqual(try StellarDecoding.classicHoldings(valid,owner:owner).first?.amount,"10000001")
        for balances in [[],[balance,balance]] as [[StellarJSON]] {
            XCTAssertThrowsError(try StellarDecoding.classicHoldings(.object(["account_id":.string(owner),"balances":.array(balances)]),owner:owner))
        }
        XCTAssertThrowsError(try StellarDecoding.classicHoldings(valid,owner:issuer))
    }
}
