from pathlib import Path
import hashlib, json

work = Path(__file__).resolve().parent
root = work / 'source'
changes = []

def replace(path, old, new, count=1):
    file = root / path
    text = file.read_text()
    assert text.count(old) == count, (path, text.count(old))
    before = hashlib.sha256(file.read_bytes()).hexdigest()
    file.write_text(text.replace(old, new))
    changes.append({'path': path, 'before': before, 'after': hashlib.sha256(file.read_bytes()).hexdigest(),
                    'old': old, 'new': new})

replace('OathApp/OathSceneDelegate.swift',
        'async let wallet: Void = session.load()',
        'async let wallet: Void = session.prepareSnapshotProbe()')
scene = root/'OathApp/OathSceneDelegate.swift'
scene.write_text(scene.read_text() + (work/'Fixture.swift').read_text())
session = root/'OathAtmosphere/Wallet/OathWalletSession.swift'
session.write_text(session.read_text() + '''

// Audit-only synthetic initial session. Runtime lock logic is unchanged.
extension OathWalletSession {
    func prepareSnapshotProbe() async {
        let profile = OathWalletProfile(id: UUID(uuidString: OathSnapshotProbe.walletID)!, addresses: [], createdAt: Date(timeIntervalSince1970: 0), backedUp: true)
        displayedProfile = profile
        state = .home(profile)
    }
}
''')
replace('OathApp/OathAtmosphereApp.swift',
'''                OathHomeScreen(profile: session.displayedProfile, session: session, settings: settings,
                               lockCoverHidden: !showsInitialLock && !lockIsVisible)''',
'''                Group {
                    if OathSnapshotProbe.enabled {
                        OathSnapshotProbeHome(session: session)
                    } else {
                        OathHomeScreen(profile: session.displayedProfile, session: session, settings: settings,
                                       lockCoverHidden: !showsInitialLock && !lockIsVisible)
                    }
                }''')
replace('OathApp/OathAtmosphereApp.swift',
        'guard session.allowsBackgroundWalletWork else { return }',
        'guard !OathSnapshotProbe.enabled, session.allowsBackgroundWalletWork else { return }', 2)
# Change only the application target, retaining package framework identities.
replace("OathAtmosphere.xcodeproj/project.pbxproj", "PRODUCT_BUNDLE_IDENTIFIER = com.aperture.wallet;", "PRODUCT_BUNDLE_IDENTIFIER = org.oath.audit.snapshotprobe;", 2)
manifest = {'baseline': 'c7acd23bb139864a40273f405d18b479589d2b20',
            'purpose': 'Synthetic disclosure view inside production root and scene lifecycle; not a full export flow or real key',
            'substitutions': ['Initial session setup instead of encrypted wallet load', 'Synthetic export reader',
                              'Home content replaced by presented production private-key value page',
                              'Root cloud/rate resume tasks disabled; production root lock and scene privacy rules retained'],
            'replacements': changes,
            'modified_files': {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
                ['OathAtmosphere.xcodeproj/project.pbxproj', 'OathApp/OathSceneDelegate.swift', 'OathApp/OathAtmosphereApp.swift', 'OathAtmosphere/Wallet/OathWalletSession.swift']}}
(work/'source-injection.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('Prepared synthetic disclosure, retaining production root and scene lock behavior')
