# Acceptance checklist — in progress

Original 4.1.15 (100) baseline `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. Reviewed app `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`.

The Electrum two-factor repair restored both independently calculated Bitcoin addresses, and the encrypted-wallet run passed 205 checks. Full package runs passed 305 Bitcoin and 708 database cases, with 60 and 71 explicit skips respectively. Unsigned iOS Release compilation passed. Three isolated Bitcoin Cash Node chains confirmed 20 ordinary spends and 121 threshold-policy spends. The node rejected modified signatures, changed payments and spends missing a required multisignature. The CashTokens prefix reader matched all 22,960 expected outcomes.

Two additional planner issues were reproduced at this source and repaired afterward in [PR 53](https://github.com/devdasx/oath-wallet/pull/53). The identical named tests passed on that later source. At the reviewed source, two protected-startup assertions missed expected asynchronous diagnostics (25 of 27 assertions passed). This failed run is included in the validation evidence. OW-2026-002 remains open for historical archive provenance.

28 passing check records target this revision. 87 required checks lack a passing exact-revision record. There are 17,124 open entries across the inventories, findings and validation ledger. The combined source and App Store binary equivalence have separate evidence requirements. [Manifest](../evidence/two-factor-and-bch/manifest.json).
