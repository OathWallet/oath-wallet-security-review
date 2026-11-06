import Foundation
import XCTest
@testable import OathBitcoin

/// Public deterministic fixture material; no node, relay or funded account.
final class BitcoinConsentReviewTests: XCTestCase, BitcoinConnectFixture {
    private func foreignCoin(_ value: UInt64, index: UInt32) throws -> BitcoinSendCoin {
        let wallet = try BitcoinKeys.wallet(seed: Data(repeating: 42, count: 32))
        let branch = try XCTUnwrap(wallet.branches.first { $0.type == .nativeSegwit && $0.change == 0 })
        let a = try BitcoinKeys.addresses(branch: branch, range: index..<(index + 1))[0]
        var raw = BitcoinWire.little(UInt32(2)) + Data([1]) + Data(repeating: 42, count: 32)
        raw += BitcoinWire.little(index) + Data([0]) + BitcoinWire.little(UInt32.max) + Data([1])
        raw += BitcoinWire.little(value) + BitcoinWire.vector(Data(hex: a.script)!) + BitcoinWire.little(UInt32(0))
        return .init(accountID: "foreign", txid: try BitcoinTransactions.txid(raw), vout: 0,
                     value: Int64(value), address: a, previousTransaction: raw, compressed: true)
    }

    private func peerPlan(_ packet: BitcoinConnectPSBT, selected: [BitcoinConnectRequest.Input],
                          addresses: [BitcoinDerivedAddress], coins: [BitcoinSendCoin]) throws -> BitcoinConnectPlan {
        let inputs: [[String: Any]] = selected.map {
            var value: [String: Any] = ["address": $0.address, "index": $0.index]
            if let modes = $0.sighashTypes { value["sighashTypes"] = modes }
            return value
        }
        let req = try request("signPsbt", extra: ["psbt": packet.encoded, "signInputs": inputs])
        return try BitcoinConnectSigning.review(request: req, psbt: packet.encoded, inputs: req.signInputs!,
            addresses: addresses, previous: Dictionary(uniqueKeysWithValues: coins.map { ($0.txid, $0.previousTransaction) }))
    }

    func testAllByteSighashModesAndHighBitValues() throws {
        var accepted = 0, rejected = 0
        for type in BitcoinAddressType.allCases {
            let c = try coin(20000, type: type), transfer = try plan([c])
            let input = try XCTUnwrap(transfer.inputs.first)
            for flag in Array(UInt32(0)...UInt32(255)) + [0x100, 0x10001, 0x80000000, UInt32.max] {
                var packet = try BitcoinConnectPSBT(transfer.psbt)
                packet.set(3, BitcoinWire.little(flag), input: 0)
                let selected = [BitcoinConnectRequest.Input(address: input.address, index: 0, sighashTypes: [0, 1])]
                if flag == 1 || (flag == 0 && type == .taproot) {
                    let reviewed = try peerPlan(packet, selected: selected, addresses: transfer.reviewedAddresses, coins: [c])
                    let signed = try BitcoinConnectSigning.sign(reviewed, source: .seed(seed, account: 0))
                    try BitcoinConnectSigning.verify(signed, plan: reviewed)
                    accepted += 1
                } else {
                    XCTAssertThrowsError(try peerPlan(packet, selected: selected, addresses: transfer.reviewedAddresses, coins: [c]), "Weak hash accepted: \(type) / \(flag)")
                    rejected += 1
                }
            }
        }
        XCTAssertEqual(accepted, 5); XCTAssertEqual(rejected, 1035)
    }

    func testMixedInputsSignOnlyOwnedSelectionAndPreservePeerFields() throws {
        for type in BitcoinAddressType.allCases {
            for ownedFirst in [false, true] {
                let own = try coin(ownedFirst ? 9000 : 7000, type: type)
                let other = try foreignCoin(ownedFirst ? 7000 : 9000, index: 0)
                let base = try plan([own, other])
                var packet = try BitcoinConnectPSBT(base.psbt)
                let selected = try XCTUnwrap(base.inputs.first { $0.address == (try? BitcoinConnectNetwork.signet.address(mainnetAddress: own.address.address)) })
                XCTAssertEqual(selected.index, ownedFirst ? 0 : 1)
                let foreignIndex = 1 - selected.index
                let marker = BitcoinConnectPSBT.Pair(key: Data([0xfc, 1, 0x61, 1]), value: Data([7, 8, 9]))
                packet.maps[foreignIndex + 1].append(marker)
                packet.maps[0].append(marker)
                packet.maps[packet.maps.count - 1].append(marker)
                let reviewed = try peerPlan(packet, selected: [selected], addresses: [own.address, try address(change: 1)], coins: [own, other])
                XCTAssertEqual(reviewed.ownedInputs.count, 1)
                XCTAssertEqual(reviewed.ownedInputs[selected.index], own.address)
                let result = try BitcoinConnectSigning.sign(reviewed, source: .seed(seed, account: 0))
                try BitcoinConnectSigning.verify(result, plan: reviewed)
                let before = try BitcoinConnectPSBT(reviewed.psbt), after = try BitcoinConnectPSBT(result.psbt)
                XCTAssertEqual(before.transaction.serialize(), after.transaction.serialize())
                XCTAssertEqual(before.maps[foreignIndex + 1], after.maps[foreignIndex + 1])
                XCTAssertEqual(before.maps[0], after.maps[0])
                XCTAssertEqual(before.maps.suffix(reviewed.outputs.count), after.maps.suffix(reviewed.outputs.count))
                XCTAssertNil(after.field(7, input: foreignIndex)); XCTAssertNil(after.field(8, input: foreignIndex))
                XCTAssertNil(result.raw); XCTAssertNil(result.txid)
                let foreign = try XCTUnwrap(base.inputs.first { $0.index == foreignIndex })
                XCTAssertThrowsError(try peerPlan(packet, selected: [foreign], addresses: [own.address, try address(change: 1)], coins: [own, other]))
                XCTAssertThrowsError(try peerPlan(packet, selected: [selected, foreign], addresses: [own.address, try address(change: 1)], coins: [own, other]))
            }
        }
    }

    func testEveryUnsignedWireByteRemainsBoundAfterSigning() throws {
        for type in BitcoinAddressType.allCases {
            let c = try coin(20000, type: type), base = try plan([c])
            let reviewed = try peerPlan(BitcoinConnectPSBT(base.psbt), selected: base.inputs, addresses: base.reviewedAddresses, coins: [c])
            let signed = try BitcoinConnectSigning.sign(reviewed, source: .seed(seed, account: 0))
            let packet = try BitcoinConnectPSBT(signed.psbt)
            let field = try XCTUnwrap(packet.maps[0].firstIndex { $0.key == Data([0]) })
            let unsigned = packet.maps[0][field].value
            for offset in unsigned.indices {
                var modified = packet
                modified.maps[0][field].value[offset] ^= 1
                let altered = try BitcoinConnectSigned(psbt: modified.encoded, raw: nil, txid: nil)
                XCTAssertThrowsError(try BitcoinConnectSigning.verify(altered, plan: reviewed), "Unsigned wire mutation accepted: \(type) / \(offset)")
            }
        }
    }

    func testEveryConsentProjectionIsRecomputedBeforeSigning() throws {
        let original = try plan([coin(20000)])
        let encoded = try JSONSerialization.jsonObject(with: JSONEncoder().encode(original)) as! [String: Any]
        var candidates: [[String: Any]] = []
        for field in ["fee", "debit"] {
            var changed = encoded; changed[field] = 0; candidates.append(changed)
        }
        for field in ["owned", "value", "address", "script"] {
            var changed = encoded, outputs = changed["outputs"] as! [[String: Any]]
            switch field {
            case "owned": outputs[0][field] = true
            case "value": outputs[0][field] = 1
            case "address": outputs[0][field] = try BitcoinConnectNetwork.signet.address(mainnetAddress: address(index: 99).address)
            default: outputs[0][field] = Data([0x6a]).base64EncodedString()
            }
            changed["outputs"] = outputs; candidates.append(changed)
        }
        for (index, value) in candidates.enumerated() {
            let modified = try JSONDecoder().decode(BitcoinConnectPlan.self, from: JSONSerialization.data(withJSONObject: value))
            XCTAssertThrowsError(try BitcoinConnectSigning.validate(modified), "Consent mutation accepted: \(index)")
        }
    }

    func testForeignParentsAndChangeCannotBeMisrepresented() throws {
        let own = try coin(9000), other = try foreignCoin(7000, index: 0)
        let base = try plan([own, other]), packet = try BitcoinConnectPSBT(base.psbt)
        let selected = try XCTUnwrap(base.inputs.first { $0.index == 0 })
        let ours = [own.address, try address(change: 1)]
        let control = try peerPlan(packet, selected: [selected], addresses: ours, coins: [own, other])
        try BitcoinConnectSigning.validate(control)
        for index in 0..<2 {
            var altered = packet
            let c = index == 0 ? own : other
            altered.set(1, BitcoinWire.little(UInt64(c.value) + 1) + BitcoinWire.vector(Data(hex: c.address.script)!), input: index)
            XCTAssertThrowsError(try peerPlan(altered, selected: [selected], addresses: ours, coins: [own, other]))
        }
        var wrongParents = [own.txid: own.previousTransaction, other.txid: other.previousTransaction]
        wrongParents[other.txid] = own.previousTransaction
        XCTAssertThrowsError(try BitcoinConnectSigning.review(request: control.request, psbt: control.psbt,
            inputs: control.inputs, addresses: ours, previous: wrongParents))
        let req = try request(extra: ["changeAddress": BitcoinConnectNetwork.signet.address(mainnetAddress: other.address.address)])
        XCTAssertThrowsError(try BitcoinConnectClient.transfer(req, coins: [.init(txid: own.txid, vout: 0, value: 20000, address: own.address)], change: address(change: 1), rate: 2))
    }

    func testDecodedDerivationMetadataCannotSelectAnotherLeafOrAccount() throws {
        for type in BitcoinAddressType.allCases {
            let original = try address(type)
            let encoded = try JSONSerialization.jsonObject(with: JSONEncoder().encode(original)) as! [String: Any]
            for (field, value) in [("path", "m/44'/0'/1'/0/0" as Any), ("index", 1 as Any), ("change", 1 as Any), ("branchID", "foreign" as Any)] {
                var json = encoded; json[field] = value
                let altered = try JSONDecoder().decode(BitcoinDerivedAddress.self, from: JSONSerialization.data(withJSONObject: json))
                XCTAssertNotEqual(original, altered)
                XCTAssertThrowsError(try UTXONetwork.bitcoin.privateKeyWIF(source: .seed(seed, account: 0), address: altered))
            }
            XCTAssertThrowsError(try UTXONetwork.bitcoin.privateKeyWIF(source: .seed(seed, account: 1), address: original))
            XCTAssertThrowsError(try UTXONetwork.bitcoin.privateKeyWIF(source: .seed(Data(repeating: 42, count: 32), account: 0), address: original))
        }
    }
}
