# NEAR multisig staged submission and recovery boundaries

Build 104 checkpoint 10. Application source is pinned to
`5d91d1e4dfd36c56031c7a8fb1ee305446dc54de` (identical-tree public merge
`0b35c607bc531e2f08c4815dfa36683f806d9eb4`). No new application defect was
confirmed and no application code changed in this checkpoint. The full audit
remains incomplete.

## Production path exercised

The test overlay runs the real `NearSendCrypto.sign`, `NearSendClient.submit`,
`status`, `multisigSubmit`, `multisigState`, RPC validation and receipt parser.
Only the provider transport is synthetic. It checks requested transaction
identities and bytes and supplies coherent block-pinned state, final receipt
graphs, pending responses, failures and controlled delayed responses. The
synthetic private seeds are public test fixtures; they are not funded accounts.

The isolated copy adds one test file. The source checkout remains clean and
its exact commit is checked before and after. Each selected XCTest method runs
in its own macOS host process with network access denied. Xcode 27.0 and Swift
6.4 versions are recorded in the local evidence. No simulator is used.

## Six passing methods

1. **Staged transfer and cold client recovery.** Quorums 1, 2, 5 and 10, for both
   native and token transfers, progress through proposal and confirmations. Each
   reconciliation uses a new client with an empty cache and JSON-decoded plan
   and signed bundle. Every broadcast must equal the next original signed part;
   the final status must aggregate all part fees and preserve the bundle hash.
2. **Read-only status and terminal failures.** At each part index, `status` sends
   nothing. A final failure stops subsequent parts and includes the accumulated
   fees. No broadcast occurs after these terminal responses.
3. **Proposal identity and payload binding.** A fully parsed successful proposal
   receipt with the wrong request ID terminates without confirmation. A changed
   on-chain request payload is rejected before any confirmation is broadcast.
4. **Expiry evidence.** For each partial progress position, an expired bundle is
   classified expired only when the next part's nonce is demonstrably unused.
   A consumed nonce remains unknown. Neither branch broadcasts.
5. **Cancellation-resistant transport.** A transaction-status reply is held at a
   deterministic continuation. The task is cancelled before the transport is
   released; the production cancellation check rejects the late reply and no
   next part is broadcast. There is no timing/sleep assertion.
6. **Concurrent replay.** Two submissions may resend the same proposal while its
   status remains unknown; both must contain the identical authorized bytes.
   This tests byte preservation, not real-chain deduplication or exactly-once
   transport delivery.

The first successful exploratory compile is not counted as runtime evidence.
The published results come from the subsequent reproducible driver with the
final overlay, separate fresh control and mutation builds, and six exact methods
in each run. [Results and hashes](../evidence/5.0.2-build104/near-multisig-lifecycle/manifest.json).

## Sensitivity control

A separate scratch copy replaces only the production request-payload equality
guard with a no-op. The payload-binding method fails (including the assertion
that no confirmation was broadcast); the other five methods pass. The mutation
patch and failed log are retained. It is never applied to public application
source or a deployed wallet. This verifies detection of the deliberately removed
guard; it does not establish coverage of every possible mutation.

## Hosted native-contract follow-up

The preceding checkpoint's paired ABI workflow now has verified hosted evidence:
[run 41615849636](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41615849636)
at audit commit `142024f63a7a5ba894017f6744b6096dce6ba80e` reproduced the identical
20-method before/after fixture and the member-admission mutation. Counts remain
9 valid passes/10 abort blockers/1 invalid fixture before; 18 valid passes/2
excluded invalid fixture passes after; 14 valid passes/4 expected failures/2
excluded invalid fixture passes for the mutation. The original artifact digest,
all expanded files, executed driver/overlay hashes and case logs were checked.
[Durable hosted receipt](../evidence/5.0.2-build104/hosted-near-contract-unwind/manifest.json).
The earlier release's pending-at-publication status is preserved as historical.
This is native mock execution, not shipped-WASM execution.

## Reproduce

Use a clean public checkout at the application pin, macOS/Xcode with Swift 6.4,
and Python 3.11 or newer. The driver records tool versions. Public package
resolution is permitted during compilation; runtime network access is denied.
Use fresh scratch and output paths:

```sh
python3 scripts/near-multisig-lifecycle.py wallet scratch/control evidence/local/control
python3 scripts/near-multisig-lifecycle.py wallet scratch/mutant evidence/local/mutant --mutant
python3 -m unittest discover -s tests -p test_near_multisig_lifecycle.py
```

The audit-only GitHub workflow pins actions, Python and the app commit, checks
its Xcode/Swift toolchain, uses read-only permissions and no secrets, and preserves
failure logs. Its lifecycle replay is separate from the already verified hosted
native-contract run above; no hosted lifecycle pass is claimed at publication.

## Remaining scope

JSON reconstruction and empty client caches are **not a full application or
persistent database restart**. Journal integration, deployment/bootstrap-key
removal transitions, all cancellation boundaries, provider execution semantics,
shipped-WASM behavior, source-to-binary reproduction and full dependencies remain
open. Source coverage is not promoted by these tests. No live provider, funded
transaction, app UI, simulator, physical device or App Store operation occurred.

Publication validation: 364 audit-helper tests passed; changed-source and expanded
evidence secret scanning found no leaks. The completion gate retains 16,918
outstanding review/validation entries, not a vulnerability count.
