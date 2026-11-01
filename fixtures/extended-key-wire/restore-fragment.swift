        // Executed inside the public host restoration harness using generated public fixtures.
        struct WireOracle: Decodable { let script: String, legacy: String, canonical: String }
        let oracles = try JSONDecoder().decode([String:WireOracle].self, from: Data(contentsOf: URL(fileURLWithPath: ProcessInfo.processInfo.environment["OATH_REVIEW_RECOVERY_VECTORS"]!)))
        let scalar = Data([0x79,0xbe,0x66,0x7e,0xf9,0xdc,0xbb,0xac,0x55,0xa0,0x62,0x95,0xce,0x87,0x0b,0x07,0x02,0x9b,0xfc,0xdb,0x2d,0xce,0x28,0xd9,0x59,0xf2,0x81,0x5b,0x16,0xf8,0x17,0x98])
        var completed = 0
        for network in [UTXONetwork.bitcoin,.litecoin,.dogecoin,.bitcoincash] {
            let oracle = oracles[network.rawValue]!
            func recovered(_ bytes: Data) throws -> OathRestoredWallet {
                let key = BackupWallet.ImportedPrivateKey(bytes:bytes,networks:[network.rawValue],compressed:true,
                    bitcoinExtendedKey: network == .bitcoin ? oracle.legacy : nil,
                    dogecoinExtendedKey: network == .dogecoin ? oracle.legacy : nil,
                    litecoinExtendedKey: network == .litecoin ? oracle.legacy : nil,
                    bitcoinCashExtendedKey: network == .bitcoincash ? oracle.legacy : nil)
                let backup = BackupWallet(id:UUID(), name:"Synthetic recovery", mnemonic:"", language:"", createdAt:Date(timeIntervalSince1970:1234),
                    accounts:[.init(network:network.rawValue,derivationPath:"imported",index:0)],privateKey:key)
                let document = try BackupDocument.seal(backup,password:"fixture-wallet-password")
                return try OathRestoredWallet(backup:BackupDocument.open(document,password:"fixture-wallet-password"))
            }
            let restored = try recovered(scalar)
            guard let material=restored.secret.privateKey, let chain=OathImportChain(rawValue:network.rawValue) else { preconditionFailure("Missing restored key") }
            let canonical=try material.extendedKey(for:network)
            check(canonical == oracle.canonical,"Restore lost version, scope or chain code")
            let descriptor=try material.bitcoinDescriptor()
            let branch=descriptor.branches.first { $0.type == .legacy && $0.change == 0 }!
            let address=try BitcoinKeys.addresses(branch:branch,range:0..<1)[0]
            check(address.script==oracle.script,"Restored payment script differs from independent oracle")
            var clean=OathImportedPrivateKey(bytes:scalar,networks:[chain],compressed:true)
            switch network {
            case .bitcoin:clean.bitcoinExtendedKey=canonical
            case .bitcoincash:clean.bitcoinCashExtendedKey=canonical
            case .dogecoin:clean.dogecoinExtendedKey=canonical
            case .litecoin:clean.litecoinExtendedKey=canonical
            }
            check(material.hasSameIdentity(as:clean) && clean.hasSameIdentity(as:material),"Legacy and canonical wallet identities differ")
            // Restore to isolated storage, close, reopen and generate another encrypted backup.
            let localDB=try await OathDatabase.open(at:folder.appendingPathComponent("old-"+network.rawValue+".sqlite"))
            try await OathDataEnvironment.seed(localDB)
            let store=WalletMemory(), bio=MemoryBiometrics()
            let writer=OathWalletVault(storage:store,biometricStore:bio,database:localDB)
            try await OathRestoredWalletSetupStore(vault:writer,restoration:restored).save(pin)
            let reader=OathWalletVault(storage:store,biometricStore:bio,database:localDB)
            let session=OathWalletSession(vault:reader);await session.load()
            check(session.isLocked,"Restored vault must lock on cold launch")
            await session.unlock(pin)
            check(session.isUnlocked,"Restored vault failed to reopen")
            let again=try await reader.encryptedCloudBackup(walletID:restored.secret.id.uuidString,password:"fixture-wallet-password")
            let repeated=try OathRestoredWallet(backup:BackupDocument.open(again,password:"fixture-wallet-password"))
            guard let second=repeated.secret.privateKey else { preconditionFailure("Reopened backup lacks private material") }
            check(try second.extendedKey(for:network)==canonical,"Round trip changed HD identity")
            do {
                let invalid=try recovered(Data(repeating:1,count:32))
                _ = try invalid.secret.privateKey!.bitcoinDescriptor()
                preconditionFailure("Unmatched stored scalar accepted")
            } catch { check(true,"Mismatched scalar rejected") }
            completed += 1
        }
        precondition(completed==4)
        print("Four encrypted extended-key restorations retained their original scripts across cold reopen and re-backup.")
