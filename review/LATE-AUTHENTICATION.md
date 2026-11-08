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
- GitHub replay is pending; these are local host results.
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

The merge receipt records that all non-Website root Git objects match the repair
commit `f857fa9ece0b290e1b9ab9cf5e3cb85ebacc045e`, which has a successful unsigned
generic iOS Release build in checkpoint 38. That build keeps its original commit
identity; no additional merge-commit build is claimed for audit-only changes.
