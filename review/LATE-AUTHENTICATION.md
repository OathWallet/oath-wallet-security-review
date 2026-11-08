# Delayed authentication replies — checkpoint 40

Maintainer-commissioned, Codex-led review of public application commit
`a9c062a3a1d492799b9f6e9d083630c7006183ea`, version 5.0.3 (105).
This is not independent certification. The whole-wallet review remains incomplete.

## Hypothesis and production trace

A connected request could remain suspended while authentication is in progress.
If its delayed credential were accepted after a lock/reopen, cancellation or a
revocation, it could return a signature outside the intended authorization session.
A related request could substitute another wallet's account or follow the globally
selected wallet instead of the explicitly requested wallet.

The production vault captures a session generation and a wallet-specific removal
generation. It checks cancellation and generation after asynchronous boundaries
and before returning a signature. Biometric opening rereads the stored envelope
and validates the released key against that envelope. The imported EVM adapter
binds account ownership, chain, key scope, derivation mode and signing address.
The selected wallet does not replace the immutable wallet/account request.

Changing an enabled PIN intentionally preserves the payload key and Face ID
enrollment. A valid Face ID reply therefore remains valid after a PIN change;
the old PIN must stop opening the newly wrapped key. Disabling the PIN rotates
the data key and disables biometric access. Disabling Face ID writes its disabled
flag before attempting credential cleanup. These are distinct operations.

## Executed scope

The fixture uses two public synthetic imported EVM keys and a new isolated SQLite
database per scenario. Its biometric double captures the credential **before**
suspending and deliberately ignores cancellation, so clearing/replacing enrollment
cannot conceal a stale-credential acceptance bug in the test double.

Both personal-message and EIP-712 paths exercise: unchanged authentication,
lock followed by reopening, PIN replacement, biometric disable, PIN disable,
request cancellation, selected-wallet switching and cross-wallet account substitution.
Initial and subsequent valid signing controls verify continued wallet usability.
The PIN replacement also checks rejection of the old PIN.

The complete production vault and encrypted-envelope implementations are compiled,
not extracted methods. The inherited host harness supplies memory credential stores
and substitutes HD/OS/UI/network adapters. The imported-key signing branch,
production signing packages and GRDB queries execute. HD derivation, real Face ID,
Keychain access controls, rendered consent, relay delivery and other chains are
**not** exercised by this fixture. Every generated host source is included in the
archive so these substitutions can be inspected. Dependency resolution must exactly
match the application's pinned database package lock before execution. Runtime
network access is denied.

## Results

- Production: **66 passed, zero failed, zero skipped**, 346.18 seconds including build.
- Deliberate generation mutation: **64 passed, two expected failures**, 350.96 seconds including build. Both failures are the lock/reopen delayed-result assertion, one per signing path.
- [GitHub replay](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42458592481): **66 passed, zero failed, zero skipped**, 562.88 seconds including build. Its deliberate mutation records **64 passed and two expected failures**, 553.89 seconds. Artifact size, SHA-256, source/fixture/driver hashes, all generated host inputs, dependency pins and every assertion match the local evidence.
- Hosted toolchain: Xcode 27.1 (27A9275), Swift 6.4, Python 3.14.7. [Terminal run, artifact and verification receipts](../evidence/5.0.3-build105/hosted-late-authentication/verification.json). The original local manifest retains its historical pending status; this receipt supersedes that status.
- No new high, critical or lower-severity production defect was confirmed by this matrix.

Per-assertion logs, generated sources, dependency lock, tool versions and executable
hashes are in `evidence/5.0.3-build105/late-authentication/runs.zip`. The two runs
compile identical generated source inputs except for the deliberately changed vault.

## Sensitivity control and preserved attempts

The negative control removes only the central session-generation comparison and
the post-biometric-read comparison in a disposable source copy. It does not modify
application source in the public repository. The lock/reopen assertion must fail
for each signing path while the remaining assertions retain their expected results.
This deliberate mutation is not a discovered production vulnerability.

The initial fixture produced 54 passes and two failures because it incorrectly
expected PIN replacement to revoke a preserved Face ID credential. Source inspection
identified the documented compatibility behavior; the corrected fixture verifies
that behavior and adds PIN-disable and old-PIN rejection checks. The initial mutant
setup also stopped before compilation because its match included a separate creation
guard. The mutation was narrowed to the biometric-opening context. Original fixture,
driver and logs remain in `initial-attempts.zip`. Neither attempt is counted as a
passing test or a confirmed app defect.

An overbroad scan of the entire historical audit directory reported 3,953 pattern matches (not confirmed exposures);
it was not reconciled as a whole-repository secret assessment. New publication files
and expanded evidence are checked separately. No clean-scan claim for all historical
material is made here.

## Reproduce

```sh
git clone https://github.com/OathWallet/oath-wallet.git wallet
git -C wallet checkout --detach a9c062a3a1d492799b9f6e9d083630c7006183ea
python3 scripts/late-authentication-review.py wallet .work/auth-production evidence/replay/auth-production
python3 scripts/late-authentication-review.py wallet .work/auth-mutation evidence/replay/auth-mutation --mutate-generation
python3 -m unittest discover -s tests -p test_late_authentication_review.py
```

Use fresh build/output directories and the recorded toolchains. Tests require no
private credentials. Dependency retrieval occurs at build time; fixture execution
cannot access the network. Failures, crashes, timeouts and missing assertions are
rejected by the result parser.

## Coverage limits

Three source/range dispositions are partial and pinned to the merge commit. The
frozen inventory is unchanged. This does not validate every vault method, all
lifecycle interleavings, the OS prompt or downstream WalletConnect UI cancellation.
The earlier hosted file-backup-exclusion failure remains unresolved. No simulator,
physical device, App Store operation or new application edit is part of this increment.

## Additional source trace: cancellation before journal commit

The EVM submission service awaits a final multisig network check after signing and
before calling the transaction journal. A missing explicit cancellation check
between those two calls initially looked like a possible late-commit path.
Following the actual asynchronous database call resolves that particular source
hypothesis: `journalEVMSignature` uses GRDB's async `write`, which forwards through
`DatabasePool` to `SerializedDatabase.execute`. The pinned implementation checks
task cancellation before invoking the write closure and installs a cancellation
handler around it. The UI model's `cancel()` cancels the submission task.

This is **manual source tracing, not a new passing runtime test or a confirmed
finding**. A held final-preflight integration test, lock-callback behavior and
every commit/cancellation interleaving remain unverified. Once signed bytes have
committed successfully, the durable worker intentionally retains their ownership.
Seven additional file/range dispositions are partial; frozen inventory counts
are unchanged. The exact application and pinned GRDB inputs are preserved in the
[trace ledger](../evidence/5.0.3-build105/late-authentication/cancellation-trace.json)
and its adjacent source archive.

The current Solana request, snapshot-review and permission implementation was also
read again, together with part of the consent view. Four additional dispositions
are recorded in the [follow-up ledger](../evidence/5.0.3-build105/late-authentication/solana-followup.json).
These are source reads with zero new Solana runtime methods. Program-specific
authority semantics beyond the token/delegation and stake guards, Token-2022
extensions, provider honesty and rendered consent remain outstanding. The existing
PR #117 results keep their original source pin and bounded stake-review scope.

The merge receipt records that all non-Website root Git objects match the repair
commit `f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e`, which has a successful unsigned
generic iOS Release build in checkpoint 38. That build keeps its original commit
identity; no additional merge-commit build is claimed for audit-only changes.

## Additional source read: swap summaries and deposit recognition

Two further partial dispositions cover the router summary and THORChain EVM
deposit-review files. The summary retains decoded execution operations alongside
compact routes and distinguishes input limits from outputs. Deposit recognition
checks the request chain, current router/vault identities, pause flags and pool
selection before presenting THORChain details. These are observed source guards,
not proof of protocol or provider correctness. The
[swap ledger](../evidence/5.0.3-build105/late-authentication/swap-followup.json)
and adjacent source archive record the exact inputs. No new swap runtime test,
whole-file completion disposition or confirmed finding is claimed.

Together this increment records three authentication, seven cancellation/GRDB,
four Solana and two swap partial source/range dispositions. The frozen inventory
and its outstanding validation count remain unchanged. Later public-main website
changes have matching non-Website root Git objects in the
[source-status receipt](../evidence/5.0.3-build105/late-authentication/publication-source-status.json);
tests retain their original source identity rather than claiming a new replay.

## Publication validation

All **538 audit-helper tests pass**, with no skips (13.924 seconds). These validate
evidence identities, parsers and audit tooling; they are separate from the 66
production-vault assertions. The scoped publication scan, including expanded
archives, reports no matches across 5,888,880 bytes. It does not supersede the
unreconciled historical scan. Logs and exact results are preserved with the
[hosted verification receipt](../evidence/5.0.3-build105/hosted-late-authentication/verification.json).
