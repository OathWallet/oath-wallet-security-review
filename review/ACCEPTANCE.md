# Acceptance checklist — in progress

Active release: **5.0.1 (103)**, `c7acd23bb139864a40273f405d18b479589d2b20`. [Release-specific findings and exact-target checks](RELEASE-5.0.1-103.md). The completion gate reads the active commit from [the scope](../scope/source.json).

Checkpoint 9 retains 16,599 open ledger items, including 1,526 outstanding direct compiler inputs and 111 partial inputs. The completed baseline workflow failed five jobs; 104 of 115 required checks have passing exact-baseline records across the evidence ledger. Later source fixes and test-harness repairs have separate commit-specific receipts. The whole-wallet acceptance criteria remain unmet.

Checkpoint 10 reduces the combined gate to 16,595 open items: direct compiler inputs now include 244 reviewed, 118 partial, 1,515 outstanding, 460 generated-and-verified and 20 generated inputs needing trace. The new source reads and limited synthetic runtime result do not change the full-review acceptance status.

## Historical acceptance snapshot

Original 4.1.15 (100) baseline `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. Reviewed app `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`.

The Electrum two-factor repair restored both independently calculated Bitcoin addresses, and the encrypted-wallet run passed 205 checks. Full package runs passed 305 Bitcoin and 708 database cases, with 60 and 71 explicit skips respectively. Unsigned iOS Release compilation passed. Three isolated Bitcoin Cash Node chains confirmed 20 ordinary spends and 121 threshold-policy spends. The node rejected modified signatures, changed payments and spends missing a required multisignature. The CashTokens prefix reader matched all 22,960 expected outcomes.

Two additional planner issues were reproduced at this source and repaired afterward in [PR 53](https://github.com/devdasx/oath-wallet/pull/53). The identical named tests passed on that later source. At the reviewed source, two protected-startup assertions missed expected asynchronous diagnostics (25 of 27 assertions passed). This failed run is included in the validation evidence. OW-2026-002 remains open for historical archive provenance.

28 passing check records target this revision. 87 required checks lack a passing exact-revision record. There are 17,124 open entries across the inventories, findings and validation ledger. The combined source and App Store binary equivalence have separate evidence requirements. [Manifest](../evidence/two-factor-and-bch/manifest.json).
