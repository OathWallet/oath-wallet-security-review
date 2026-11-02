import Foundation
import OathAezeed
import OathBitcoin

@main struct ThreeFormats {
    struct Vector: Decodable {
        let words: String, electrum_address: String, aezeed_address: String, bip39_address: String
    }
    enum Failure: Error { case fixture, routing, address }

    @MainActor static func main() throws {
        let resources = URL(fileURLWithPath: CommandLine.arguments[1])
        let vector = try JSONDecoder().decode(Vector.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2])))
        let validator = try OathMnemonicValidator.load { resources.appendingPathComponent($0 + "." + $1) }
        let draft = OathRecoveryPhraseDraft(validator: validator)
        guard draft.receiveScan(vector.words), draft.matchingFormats == [.aezeed,.bip39,.electrum],
              draft.isAezeed, draft.submit() == nil else { throw Failure.fixture }
        let a = try BitcoinKeys.aezeedWallet(entropy: Aezeed.decode(vector.words).entropy)
        let lnd = try BitcoinKeys.addresses(branch: a.branches.first { $0.type == .nativeSegwit && $0.change == 0 }!, range: 0..<1)[0]
        guard lnd.address == vector.aezeed_address else { throw Failure.address }
        draft.selectFormat(.bip39)
        guard let bip39 = draft.submit(), bip39.explicitBIP39, bip39.phrase == vector.words,
              bip39.aezeed == nil, bip39.electrum == nil else { throw Failure.routing }
        draft.selectFormat(.electrum)
        guard draft.isElectrum, !draft.isAezeed, draft.submit() == nil else { throw Failure.routing }
        let wallet = try ElectrumBitcoin.wallet(ElectrumMnemonic.decode(vector.words))
        let bitcoin = try BitcoinKeys.addresses(branch: wallet.branches.first { $0.change == 0 }!, range: 0..<1)[0]
        guard bitcoin.address == vector.electrum_address, Set([lnd.address,bitcoin.address,vector.bip39_address]).count == 3 else { throw Failure.address }
        draft.isComposing = true
        guard draft.matchingFormats.isEmpty, draft.submit() == nil else { throw Failure.routing }
        draft.isComposing = false
        draft.clear()
        guard draft.matchingFormats.isEmpty, draft.preferredFormat == nil else { throw Failure.routing }
        print("All three format routes, two native derivations, composition and reset passed")
    }
}
