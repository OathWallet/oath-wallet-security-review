# NEAR contract rejection tests: native mock repair

Build 104 checkpoint 9. This repairs an **audit-only native SDK mock boundary**,
not the application or distributed contract. The whole-wallet audit remains
incomplete. The preceding checkpoint's original aborts remain preserved.

## Cause and bounded repair

The pinned contract uses `near-sdk` 4.0.0-pre.4 and `near-sys` 0.1.0. On a
native host, `env::panic_str` calls `near_sys::panic_utf8`; the mock implementation
converts a VM logic error into a Rust panic. Both sides declared the boundary
as `extern "C"`. Modern Rust aborts when a panic escapes that boundary, so
`#[should_panic]` cannot catch the expected contract rejection.

An older compiler would not establish sound behavior: [Rust's 1.71 release
explanation](https://blog.rust-lang.org/2023/07/13/Rust-1.71.0/) explicitly
distinguishes defined `C-unwind` behavior from the formerly undefined unwinding
across `C`. The [Rust FFI documentation](https://doc.rust-lang.org/nomicon/ffi.html#ffi-and-unwinding)
describes the boundary requirements. This replay therefore uses the same
Rust/Cargo 1.96.1 toolchain before and after.

The paired harness verifies the two original `.crate` archive digests against
the upstream lock, extracts fresh local copies, and records every file's hash.
The after copy changes exactly two files:

- `near-sdk/src/environment/mock/mocked_blockchain.rs`: the native-only
  `panic_utf8` mock becomes `extern "C-unwind"`.
- `near-sys/src/lib.rs`: native `panic_utf8` uses a matching `C-unwind`
  declaration; the original `C` declaration remains selected for `wasm32`.

No guard, state transition, receipt action or contract source changes between
the before and after runs. Both use identical appended tests, local SDK path
overrides, and the same pruned 70-package graph. The registry cache, upstream
checkout, app checkout and bundled WASM are untouched. This is not a production
dependency update, nor a proof of WASM execution or rollback.

## Identical-fixture results

The fixture selects 20 methods, each executed alone with networking denied.

- **Before:** nine valid passes, ten SIGABRT blockers, one invalid inherited
  fixture pass.
- **After:** eighteen valid passes, no aborts, two invalid inherited fixture
  passes excluded from the passing count.

The two excluded inherited tests are still present. One constructs an invalid
public key before reaching its purported receiver check. The other uses the
same signer twice and hits the cooldown instead of rejecting a foreign key.
The latter changes from abort to Rust-reported pass after the ABI repair, but
is deliberately classified as invalid rather than counted as a new pass.

Five additional tests require the exact intended rejection message:
adding a key for the wrong receiver with a properly encoded key; deletion by
a genuinely foreign key after the cooldown; request creation by a foreign key;
confirmation of a nonexistent request; and a removed member attempting a new
confirmation. All five are blocked before and pass after the mock repair.
Four meaningful inherited rejection tests also become catchable and pass.
The nine normal source/receipt methods retain their passing results.

An isolated sensitivity mutation replaces the actual contract's member-admission
condition with `true`. Exactly four methods fail: the foreign creation/deletion,
removed-member confirmation, and earlier membership characterization checks.
Fourteen valid controls still pass, and the two invalid fixtures remain excluded.
The mutated contract exists only in scratch evidence; it is never applied to an
application, upstream checkout, deployed contract or registry cache.

[Machine-readable results and hashes](../evidence/5.0.2-build104/near-contract-unwind/manifest.json) ·
[Before, after, mutation and original experiment logs](../evidence/5.0.2-build104/near-contract-unwind/runs.zip).

## Hosted evidence and compiler setup

[Independent multisig run 41611022824](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41611022824)
passed its three methods, 50 bundles, 188 transaction parts and five verifier
controls at audit commit `14efd7264205c1f092dfeda11b9be5f1ff3903e7`.
The downloaded artifact digest, expanded files, case logs, generator, verifier,
SDK lock and overlay hashes are verified. [Durable receipt](../evidence/5.0.2-build104/hosted-near-multisig-vectors/manifest.json).

The first hosted native-contract attempt, run 41613312416, stopped before contract
tests because its runner had Rust/Cargo 1.99.1. The driver correctly required
1.96.1. The workflow now installs that exact toolchain and adds its absolute
binary directory to the path. [Original failed job and cause](../evidence/5.0.2-build104/near-contract-ci-toolchain/manifest.json).
[Follow-up run 41614094759](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41614094759)
completed and its artifact, case logs and executed driver hashes were verified.
It reproduces the original SDK dispositions: nine valid passes, five abort
blockers and one invalid fixture pass. This is successful evidence collection,
not an all-passing contract suite. [Verified receipt](../evidence/5.0.2-build104/hosted-near-contract-native/manifest.json).
The expanded paired ABI replay has a separate workflow run; its hosted result
is not yet verified.

## Reproduce

On macOS, use Python 3.11 or newer and Rust/Cargo 1.96.1. Prepare the public
dependency cache using the checkpoint-8 fetch step, which also preserves the
original unpatched native results:

```sh
git clone https://github.com/near/core-contracts.git near-contract
git -C near-contract checkout --detach 1b0436c96379c63aee7d2429c6d5d24019031ab8
python3 scripts/near_contract_unit.py near-contract scratch/base evidence/local/base \
  --cargo-home scratch/cargo --fetch
python3 scripts/near_contract_unwind.py near-contract scratch/before evidence/local/before scratch/cargo --mode original
python3 scripts/near_contract_unwind.py near-contract scratch/after evidence/local/after scratch/cargo --mode unwind
python3 scripts/near_contract_unwind.py near-contract scratch/mutant evidence/local/mutant scratch/cargo --mode mutant
python3 -m unittest discover -s tests -p test_near_contract_unwind.py
```

All comparison builds are offline and test execution is network-denied. Use
fresh scratch/output directories for each attempt. Crate archive versions,
checksums, all extracted file hashes, the two ABI patches, the one-line mutation,
test identities, exit codes and logs remain in the evidence. Cargo's graph
comparison normalizes only the two verified local copies; all other package
versions, checksums and the complete pruned dependency closure must match.

## Still unresolved

These are native source tests with mock receipts. They do not execute the shipped
WASM, reproduce its binary, validate VM rollback after a panic, execute promises,
or complete the contract/dependency review. The retained vote after an authorized
membership change is still a separately documented policy/impact question.
The full original simulation suite, staged app lifecycle coverage and broader
wallet audit remain open. No source disposition is promoted to complete by
these results. No app code, simulator, physical device, live transaction or
App Store operation changed; no new app build was needed for audit-only files.

Publication validation: 362 audit-helper tests pass. The full-review gate remains open; no passing test is used to promote incomplete source coverage.
