# Backup presentation callback replay

The final production-model fixture and host build helper are committed in the
public Oath repository at `a904515793b087289140e4411924f030b3fe61ff`:
`Tools/CheckBackupPresentation.swift` and `Tools/CheckBackupPresentation.py`.
The helper extracts the class unchanged from `OathAllWalletBackupPage.swift` and
omits only its SwiftUI view. The model is not reimplemented in the test.

From a clean review checkout on macOS with Xcode 27/Swift 6.4:

```sh
git clone --no-checkout https://github.com/devdasx/oath-wallet.git /tmp/backup-wallet
python3 scripts/backup-presentation.py /tmp/backup-wallet /tmp/backup-results
```

The replay pins previous public main `00d26c005fbc3f811615b23b865bb50ef7b6619f`
and repair `a904515793b087289140e4411924f030b3fe61ff`. Both run the same fixture
and build helper. Every named result, completion summary and exit code must match:
12 passes/3 failures before, 15 passes/0 failures after. Production source hashes,
fixture hashes, durations and original/sanitized log hashes are recorded.

Database, service, diagnostics and vault are synthetic boundaries. Continuations
hold a database read; cancellation/new creation happens only after the old read
has entered. The old read then completes with success or failure. A completion
barrier proves the production callback returned before assertions, without sleeps.
Controls cover old successful reads and legitimate current failures. The final
binary runs with network access denied and uses no credentials, iCloud, UIKit,
simulator or device. Compilation is not a full application runtime test.

`Exploratory.swift` is the initial 12-case discovery fixture, whose uncaught final
failure produced a Swift trap. Its nine passes/three failures and raw log are
preserved; the final fifteen-case fixture adds three current-failure controls and
uses a normal nonzero exit. The final replay, not the exploratory trap, defines
regression acceptance. No backup encryption or storage implementation is substituted
and then claimed tested: those layers are explicitly outside this model check.
