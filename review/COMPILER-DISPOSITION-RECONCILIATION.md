# Preserve scoped compiler review evidence

Regenerating build 104's compiler coverage exposed a reporting inconsistency:
16 existing partial dispositions had been carried forward in the compiler
ledger, but were absent from the canonical application inventory. The join
therefore reported them as outstanding again.

Each of these entries is now also recorded in the canonical inventory and
review dispositions. Its source digest matches both the historical build-103
compiler ledger and the build-104 compiler trace. The original compiler ledger
is unchanged. This is an evidence reconciliation, not 16 new source reviews:
every entry remains **partially reviewed**, with additional review required.

The [exact paths and hashes](../evidence/5.0.2-build104/chain-wallet-adapters/compiler-reconciliation.json)
link to the preserved historical ledger. Existing read scopes include
[backup presentation](BACKUP-PRESENTATION.md),
[restore lifecycle](CLOUD-RESTORE-LIFECYCLE.md),
[XRP signing](XRPL-SIGNING-MATRIX.md), and
[XRP request boundaries](XRPL-CODEC-BOUNDARIES.md). Large session and connection
files retain only their previously scoped partial coverage, not whole-file
completion. No historical test result is relabeled as a build-104 execution.

The first regenerated-ledger helper run also detected that the generator put
the nested input-manifest hash in the field named `trace_manifest_sha256`.
It now hashes the actual trace file, matching the existing verification contract.
The failing run is preserved alongside the retest; this was a reporting-tool
defect, not an application vulnerability.

Separately, four newly read wallet adapters receive partial dispositions in
[the adapter review](CHAIN-WALLET-ADAPTERS.md). The regenerated compiler ledger
therefore has four more partial entries than the previous published ledger;
the reconciliation itself adds no new coverage. All partial entries stay open
in the completion gate. No application or deployment code changes here.
