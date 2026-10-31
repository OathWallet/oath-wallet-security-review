# Method and threat model

The commissioner is the wallet maintainer. The reviewer is Codex, an automated
coding agent. This is not an independent third-party engagement. A reproducible
test is evidence for its assertions, not for every surrounding security property.

Assets: recovery material, private keys, passphrases, authorization capabilities,
backup decryption keys, signing intent, destination/amount/network binding, and
local wallet identities. Attack surfaces include malicious dApps, QR/deep-link
input, imported files, compromised RPC/provider responses, hostile metadata,
stale sessions, interrupted persistence and unauthorized access to an unlocked
device. OS compromise and all side-channel resistance remain separate concerns.

For each source component, trace inputs to authorization, secret retrieval,
serialization, signing, persistence, output and cleanup. Inspect both successful
and exceptional paths. Check cross-wallet binding, stale capabilities, cancellation,
decimal exactness, length bounds, network/replay binding, allowlists, and privacy.
Trace dependencies rather than assuming a wrapper validates upstream behavior.

Coverage rules:

- `reviewed` means the specified complete file was read by Codex for the stated
  questions. It does not mean a human auditor reviewed it or that it has no bugs.
- Partial reads remain `partially-reviewed`, with the outstanding portions visible.
- Scanner-derived candidates remain outstanding until traced. Tests never change
  this status automatically.
- Assets/localizations may be classified as non-security content only with a
  reason. Parsers, URLs, entitlements, build scripts and dependencies are not
  dismissed based on filename.
- Every recorded disposition carries a file hash. A change invalidates it.

Severity is based on demonstrated prerequisites and impact. Suspicions are not
promoted to exploitable vulnerabilities without a safe reproduction. Fixtures
must be public/synthetic; public-network signing, funded accounts and production
wallet data are excluded. No physical device or simulator was used in this phase.

The harnesses compiled by `Tools/CheckMultiWallet.py` use production vault and
signing adapters but substitute parts of key derivation, biometrics, storage and
network services. Read those substitutions before interpreting the results.
Package tests use production modules; some opt-in integration tests can skip.
An unsigned generic-iOS build validates compilation/linkage, not iOS runtime
behavior or the identity of Apple's distributed executable.

CI runs with read-only repository tokens on disposable hosted runners. It has no
deployment environment, signing key, App Store task, `pull_request_target` event,
or self-hosted runner. New outside contributors require workflow approval.
Vulnerability-database answers are timestamped observations and can change.

Release evidence is bundled with checksums. A progress release is not an audit
completion release. A final verdict requires resolved coverage, findings,
required tests and compilation on the exact final commit.
