# Oath Wallet security review — in progress

This is a **maintainer-commissioned, Codex-led security review** of the public
Oath Wallet application. It is not independent certification, a guarantee of
zero vulnerabilities, or a comparison with the installed App Store binary.

Baseline: [4.1.15 (100)](https://github.com/devdasx/oath-wallet/tree/c7cdbde5e9f136b595500e92fbc904b107dcd8ee).
The exact baseline and current target are in [scope/source.json](scope/source.json).

**The whole-wallet review is not complete.** Test success does not turn
outstanding source into reviewed source. Consult the [report](review/REPORT.md),
[coverage ledger](scope/inventory.json), [findings](findings), and
[Actions runs](https://github.com/devdasx/oath-wallet-security-review/actions) and
[acceptance checklist](review/ACCEPTANCE.md) together.

## Reproduce

Use an isolated machine with Xcode 27.1, Swift 6.4 and Python 3.14.7.
Local exploratory runs used Xcode 27.0; each run records its actual toolchain.
Package downloads require network access; opt-in live-chain tests are not enabled.
No signing certificate, provider credential, real wallet or App Store access is needed.

```sh
python3 scripts/checkout.py
python3 scripts/inventory.py .work/source --output scope/inventory.json
python3 -m unittest discover -s tests -p 'test_*.py'
sh scripts/parser-check.sh .work/source .work/parser
python3 scripts/run.py .work/source OathCloudBackup
python3 scripts/run.py .work/source OathDiagnostics
python3 scripts/run.py .work/source OathDatabase
python3 scripts/run.py .work/source OathBitcoin
python3 scripts/run.py .work/source OathAnkr
python3 scripts/run.py .work/source OathAezeed
python3 scripts/run.py .work/source OathWalletHandoff
python3 scripts/relay-envelope-check.py .work/source --output /tmp/relay-evidence
python3 scripts/response-topic-check.py .work/source --output /tmp/topic-evidence
python3 scripts/run.py .work/source walletconnect-sdk
python3 scripts/run.py .work/source walletconnect-verify
python3 scripts/run.py .work/source security
python3 scripts/run.py .work/source build
```

`scripts/run.py --help` lists the additional authorization harnesses. Those
harnesses replace hardware, networking and some derivation adapters with
fixtures: their outcomes do not establish end-to-end iOS signing behavior.
Read the original harness headers and the report before interpreting a pass.

For the baseline parser reproduction, check out the baseline commit separately
and run `parser-check.sh` against it. The object-limit assertion must fail there;
it must pass on the repaired revision. The parser harness compiles the actual
production files, without rewriting them.

## Evidence and claims

Findings retain the original defect, reproduction and fix; they are not deleted
to create a clean-looking report. Results record exit status and skipped-test
summaries. A passing command may include explicitly skipped live/runtime tests.
Local logs are sanitized for paths before publication. GitHub artifacts are
retained for 90 days; release bundles preserve selected evidence longer.

No workflow deploys the app, uses production secrets or runs on a self-hosted
runner. Public PR checks use disposable GitHub-hosted machines and read-only
tokens. Changes after a reviewed commit require another review.

## Responsible use

All test credentials are public synthetic fixtures. Never fund them or supply
real credentials to these tests. Report newly discovered exploitable issues
through the application's [private reporting channel](https://github.com/devdasx/oath-wallet/security/advisories/new).
Technical details should accompany tested fixes; a public source fix is not
proof that App Store users have received it.

## Progress evidence release

The [latest progress snapshot](https://github.com/devdasx/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress5)
is a prerelease, not a completed audit. It identifies the original baseline and
fixed source target and attaches sanitized logs, result records and SHA-256
checksums. Failed attempts remain included. Workflow runs after the snapshot
are additional evidence; they do not retroactively change its coverage claims.

Package runs isolate each XCTest case in its own host process and retain its
actual skipped/passed/failed output. Swift Testing runs separately. Earlier
Swift parallel xUnit files remain in evidence, but their missing skip markers
must not be read as zero skipped tests; see the reporting correction in
`review/READ-NOTES.md`. No passing command converts an opt-in skip into evidence.


## Aezeed dependency reproduction

The workflow pins Go 1.26.5. From the audit root after checkout:

```sh
reviewed=$(python3 -c "import json; print(json.load(open('scope/source.json'))['reviewed_commit'])")
python3 scripts/go-source-inventory.py .work/source "$reviewed" .work/aezeed-source-inputs.json
python3 scripts/go_advisory_triage.py evidence/bridge/osv-go.json .work/aezeed-source-inputs.json .work/advisory-triage.json
cd .work/source/Tools/AezeedBridge
GOWORK=off GOFLAGS=-mod=readonly go run ../../../../tests/GoDependencyVectors.go
GOWORK=off GOFLAGS=-mod=readonly go test -race -count=1 github.com/Yawning/aez github.com/kkdai/bstream golang.org/x/crypto/scrypt golang.org/x/crypto/pbkdf2 golang.org/x/crypto/blake2b
```

The committed OSV snapshot makes that classification replayable; CI also obtains
and preserves a fresh snapshot. Any new unresolved affected import fails triage.
For wordlist comparison, clone the pinned Wallet Core revision in
`scope/upstream-wallet-core.json`, then run
`python3 scripts/compare-aezeed-wordlists.py .work/source <WALLET_CORE> .work/wordlists.json`
from the audit root. The module inventory does not establish historical archive
identity or manually-reviewed coverage.
