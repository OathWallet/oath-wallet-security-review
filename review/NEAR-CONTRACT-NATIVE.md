# NEAR contract native-source replay

This is checkpoint 8 of the **5.0.2 (104) prerelease** review. The whole-wallet
review remains incomplete. No application code or bundled contract changed.

Application repair source: `5d91d1e4dfd36c56031c7a8fb1ee305446dc54de`.
Contract source: `near/core-contracts` at
`1b0436c96379c63aee7d2429c6d5d24019031ab8`, `multisig2/src/lib.rs`, SHA-256
`65bc055731f6c5a9344ba3155b9685f95ebdfafe83d938cf3c5bdd10ad458046`.
The earlier byte-identity comparison binds this source and its distributed WASM
to the copies in the application. It does not prove that the WASM was built
from this source.

## Why the earlier tests could not run

The original upstream manifest pulls in `near-sdk-sim` and RocksDB/Wasmer even
for library unit tests. Those dependencies failed to compile on this ARM host;
the original failures remain in checkpoint 6. This replay removes only the two
development dependencies from an isolated manifest. It leaves the upstream
Rust source and its existing tests unchanged, then appends the audit test module.
Nothing is edited in the application or upstream checkout.

The adapted lock graph has 70 packages instead of 335. Every retained package's
version, source and checksum matches the original lock. Resolved edges are also
checked: the root loses its two development dependencies, and `indexmap` loses
the optional `serde` edge enabled by the larger graph. There are no new or
retargeted edges. The full reachable pruned closure must match, preventing
missing or extra packages from being silently accepted.

The first lock comparison was too strict about Cargo's dependency-name
disambiguation. After resolving names to exact package identities, a second
attempt exposed the `indexmap` feature-edge pruning. The initial overlay gate
failure, intermediate runs and final result are retained. This is a documented
unit-harness adaptation, not a dependency upgrade or a full upstream build.

## Results actually observed

With Rust/Cargo 1.96.1 on the macOS host, compilation succeeds. Each test runs
in its own process with network access denied. Of 15 selected methods:

- Five ordinary inherited tests pass.
- Four new source tests pass. They inspect actual SDK mock receipts: no transfer
  before quorum, exact receiver/amount after quorum, exact function-call bytes,
  deposit and gas, cleanup counters, and membership-change behavior.
- Five inherited rejection tests reach their named contract guards, then abort
  with SIGABRT because the old SDK mock lets a panic cross a non-unwinding ABI
  boundary on this Rust version. They are **blocked**, not passing tests.
- One inherited `should_panic` test is reported as passing by Rust, but the
  source and captured output show it panics constructing an invalid public key
  before invoking the receiver guard. It is an **invalid fixture pass**, excluded
  from the nine passing methods.

The inherited `test_delete_request_panic_wrong_key` also uses the same signer
twice and fails on the deletion cooldown. Its name does not establish wrong-key
coverage. No original test was renamed, suppressed or relabeled as a valid
authorization regression.

The harness exits successfully only when the complete, explicit disposition
matches these observations. That exit means evidence collection succeeded;
`all_contract_tests_passed`, `wasm_execution_verified` and
`source_to_binary_rebuild_verified` all remain **false** in the machine record.
Mock receipts schedule actions; they neither transfer funds nor execute a NEAR VM.

## Membership-change question: behavior reproduced, impact still open

The new characterization starts with three members and a two-member quorum.
Member 3 creates a payment; member 1 confirms it. Members 2 and 3 then authorize
removing member 1. The removed member is no longer admitted by `current_member`,
but their existing confirmation remains on member 3's pending payment. Member 2
can provide its second confirmation and schedule the payment.

This confirms the source trace at `delete_member`/`confirm`: removal deletes
requests created by the removed member, but not their votes on other members'
requests. The reproduction requires a legitimate quorum-authorized membership
change. It is not proof of an outsider bypass, a forged vote or an app-exposed
attack. Oath's supported transfer path checks the configured membership and
does not expose contract membership changes. Policy semantics, direct-contract
use and the shipped-WASM behavior remain open review questions. This observation
must not be converted into either a confirmed app exploit or a safety verdict.

## GitHub evidence verified separately

[Run 41609444047](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41609444047)
completed successfully at audit commit
`32e7607cbb37237e5b5d354f6cd015147de1d047`. All ten existing application multisig
methods passed. The downloaded artifact digest, every method log, both executed
driver hashes and the four upstream copies were verified. Generated inventory
hashes are compared separately from later manual review annotations.

[Hosted manifest](../evidence/5.0.2-build104/hosted-near-multisig/manifest.json) ·
[Native replay manifest](../evidence/5.0.2-build104/near-contract-unit/manifest.json) ·
[Complete preserved native logs and inputs](../evidence/5.0.2-build104/near-contract-unit/runs.zip).

## Reproduce from a clean checkout

Use macOS with Python 3.11 or newer and Rust/Cargo **1.96.1**. Missing or different
toolchains are blockers; the driver does not silently skip the test. The fetch
step accesses public dependency registries, then compilation is offline and
test execution is network-denied. Fresh output directories preserve older runs.

```sh
git clone https://github.com/near/core-contracts.git near-contract
git -C near-contract checkout --detach 1b0436c96379c63aee7d2429c6d5d24019031ab8
python3 scripts/near_contract_unit.py near-contract scratch/native evidence/local/native \
  --cargo-home scratch/cargo-cache --fetch
python3 -m unittest discover -s tests -p test_near_contract_unit.py
```

The audit-only workflow records the same dispositions. It has read-only repository
permissions, no deployment credentials, and no pull-request execution trigger.
Its hosted result is separate from the completed local result above.

## Remaining work

The full original suite, a compatible rejection-test runtime, independently
executed WASM behavior, deterministic source-to-WASM rebuilding, reachable
dependency implementation review, membership-change implications and staged
app submission/restart/cancellation coverage remain incomplete. No coverage
entry is promoted to complete by this replay. No new application defect or
production fix is claimed. No new iOS build was run for these audit-only files;
earlier build evidence retains its original source pin. No simulator, physical
device, live transaction or App Store operation occurred.

Publication checks passed 358 audit-helper tests. The secret scan of changed
files and expanded evidence archives reported eight matches, all verified as
SHA-256 digests of archived test logs whose filenames contain `key`. The raw
redacted results and per-match checks are preserved; no general exclusion or
suppression was added. No credential finding remains unresolved in that scan.
