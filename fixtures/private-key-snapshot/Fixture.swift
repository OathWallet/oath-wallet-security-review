
// Audit-only injection into an isolated source copy. Never shipped.
// The key is deliberately invalid, no encrypted wallet or user secret is loaded.
enum OathSnapshotProbe {
    static let enabled = true
    static let walletID = "11111111-1111-4111-8111-111111111111"
    @MainActor static func record(_ event: String, session: OathWalletSession, model: OathPrivateKeyModel? = nil) {
        let file = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("snapshot-probe.jsonl")
        let row: [String: Any] = ["event": event, "locked": session.isLocked,
            "unlocked": session.isUnlocked, "revealed": model?.phase == .revealed,
            "has_value": model?.key != nil, "uptime": ProcessInfo.processInfo.systemUptime]
        guard let data = try? JSONSerialization.data(withJSONObject: row, options: [.sortedKeys]) else { return }
        var previous = (try? Data(contentsOf: file)) ?? Data()
        previous.append(data); previous.append(10)
        try? previous.write(to: file, options: .atomic)
    }
}

struct OathSnapshotReader: OathPrivateKeyReading {
    static let account = OathPrivateKeyAccount(id: "synthetic-account", chain: .ethereum,
        address: "SYNTHETIC-ADDRESS-NOT-AN-ACCOUNT", path: "m/44'/60'/0'/0/0")
    func privateKeyAccounts(walletID: String) async throws -> [OathPrivateKeyAccount] { [Self.account] }
    func privateKey(walletID: String, accountID: String, digits: [UInt8]) async throws -> OathPrivateKeyExport {
        .init(value: "AUDIT-SNAPSHOT-TEST-NOT-A-PRIVATE-KEY", format: "SYNTHETIC")
    }
    func privateKeyWithBiometrics(walletID: String, accountID: String, reason: String) async throws -> OathPrivateKeyExport {
        .init(value: "AUDIT-SNAPSHOT-TEST-NOT-A-PRIVATE-KEY", format: "SYNTHETIC")
    }
}

struct OathSnapshotProbeHome: View {
    let session: OathWalletSession
    @Environment(\.scenePhase) private var phase
    @State private var model = OathPrivateKeyModel(walletID: OathSnapshotProbe.walletID, reader: OathSnapshotReader())
    @State private var showsKey = false
    @State private var started = false
    var body: some View {
        Text("Synthetic audit fixture")
            .sheet(isPresented: $showsKey) {
                NavigationStack {
                    OathPrivateKeyValuePage(model: model, session: session)
                        .navigationTitle("SYNTHETIC AUDIT FIXTURE")
                        .navigationBarTitleDisplayMode(.inline)
                }
            }
            .task {
                guard !started else { return }; started = true
                await model.load()
                model.select(OathSnapshotReader.account, reason: "Synthetic fixture only")
                for _ in 0..<100 where model.busy { try? await Task.sleep(for: .milliseconds(10)) }
                guard model.phase == .warning else { return }
                model.acknowledge(); showsKey = true
                OathSnapshotProbe.record("ready", session: session, model: model)
            }
            // Same cancellation calls as the production settings owner; the
            // production model decides what happens to an already revealed key.
            .onChange(of: session.isUnlocked) { _, unlocked in
                if !unlocked { model.cancelAuthentication() }
                OathSnapshotProbe.record("unlock_changed", session: session, model: model)
            }
            .onChange(of: phase) { _, value in
                if value == .background { model.cancelAuthentication() }
                OathSnapshotProbe.record(value == .background ? "background" : value == .active ? "active" : "inactive", session: session, model: model)
            }
    }
}
