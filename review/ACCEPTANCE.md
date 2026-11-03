# Acceptance checklist — in progress

Active release: **5.0.1 (103)**, `c7acd23bb139864a40273f405d18b479589d2b20`. [Release-specific findings and exact-target checks](RELEASE-5.0.1-103.md). The completion gate reads the active commit from [the scope](../scope/source.json).

Checkpoint 9 retains 16,599 open ledger items, including 1,526 outstanding direct compiler inputs and 111 partial inputs. The completed baseline workflow failed five jobs; 104 of 115 required checks have passing exact-baseline records across the evidence ledger. Later source fixes and test-harness repairs have separate commit-specific receipts. The whole-wallet acceptance criteria remain unmet.

Checkpoint 10 reduces the combined gate to 16,595 open items: direct compiler inputs now include 244 reviewed, 118 partial, 1,515 outstanding, 460 generated-and-verified and 20 generated inputs needing trace. The new source reads and limited synthetic runtime result do not change the full-review acceptance status.

Checkpoint 11 records 105 of 116 passing required exact-baseline checks and 250 passing audit helper tests. Direct compiler inputs include 244 reviewed, 120 partial and 1,513 outstanding; generated counts and the 16,595 combined open-item count remain unchanged. Private-key snapshot behavior and the application export adapter runtime coverage remain open. [Private-key evidence limits](PRIVATE-KEY-DISCLOSURE.md).

Checkpoint 12 resolves the specific retained-key snapshot hypothesis as OW-2026-058 and publishes its tested source repair. The historical baseline still contains that defect; fixes after the reviewed commit remain separate in the gate. Runtime evidence uses one synthetic production-component fixture, not a complete export UI or every OS. No existing outstanding source/dependency entry is promoted merely because this test passed. The whole-wallet review remains in progress.

Checkpoint 14 verifies two hosted before/after repair replays and adds 22 passing local restore-model cases with a three-failure mutation control. Four further partial dispositions leave 244 reviewed, 128 partial and 1,505 outstanding direct inputs, with generated counts unchanged. The gate remains at 16,597 open items. 273 audit-helper tests pass; live cloud, full restore persistence and UI coverage remain open. [Restore review](CLOUD-RESTORE-LIFECYCLE.md).

Checkpoint 13 records OW-2026-059's tested source repair and fifteen controlled model cases (three expected failures before, none after). Four new partial dispositions leave 244 reviewed, 124 partial and 1,509 outstanding direct inputs, with generated counts unchanged. The gate retains 16,597 open items, and 266 audit-helper checks pass. Model tests do not complete UIKit, live-cloud or cryptographic coverage. [Backup review](BACKUP-PRESENTATION.md).

Checkpoint 15 adds the verified public-source repair OW-2026-060 and 4,900 paired arithmetic cases. Four partial dispositions leave 244 reviewed, 132 partial and 1,501 outstanding direct compiler inputs; generated counts are unchanged. The combined gate retains 16,598 entries. The complete signing/serialization paths, dependency provenance and full-wallet coverage remain open. [XRP arithmetic scope](XRPL-AMOUNT-ARITHMETIC.md).

Checkpoint 16 adds 61 independent signed-transaction vectors, 13 RIPEMD vectors and negative signature/plan tests. Five more partial file dispositions leave 244 reviewed, 135 partial and 1,498 outstanding direct inputs. Generated counts and the 16,598-entry completion gate are unchanged. Provider-response hypotheses and all full-review acceptance gaps remain open. [Signing matrix](XRPL-SIGNING-MATRIX.md).

## Historical acceptance snapshot

Original 4.1.15 (100) baseline `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. Reviewed app `8c4e1d5d3a14bec0b9ea3a1fd01c7611ea4dd707`.

The Electrum two-factor repair restored both independently calculated Bitcoin addresses, and the encrypted-wallet run passed 205 checks. Full package runs passed 305 Bitcoin and 708 database cases, with 60 and 71 explicit skips respectively. Unsigned iOS Release compilation passed. Three isolated Bitcoin Cash Node chains confirmed 20 ordinary spends and 121 threshold-policy spends. The node rejected modified signatures, changed payments and spends missing a required multisignature. The CashTokens prefix reader matched all 22,960 expected outcomes.

Two additional planner issues were reproduced at this source and repaired afterward in [PR 53](https://github.com/devdasx/oath-wallet/pull/53). The identical named tests passed on that later source. At the reviewed source, two protected-startup assertions missed expected asynchronous diagnostics (25 of 27 assertions passed). This failed run is included in the validation evidence. OW-2026-002 remains open for historical archive provenance.

28 passing check records target this revision. 87 required checks lack a passing exact-revision record. There are 17,124 open entries across the inventories, findings and validation ledger. The combined source and App Store binary equivalence have separate evidence requirements. [Manifest](../evidence/two-factor-and-bch/manifest.json).

Checkpoint 12 audit-helper validation: **262 tests passed**. The combined gate
retains **16,596 open items**; the extra finding remains counted against the
unchanged historical baseline despite its later public repair. Direct compiler
coverage counts are unchanged. These counts are not counts of vulnerabilities.

Checkpoint 17: OW-2026-061 has a verified later-source repair and paired replay.
The unchanged baseline keeps it counted in the gate: **16,599 open entries**.
Direct compiler coverage remains 244 reviewed, 135 partial, 1,498 outstanding,
460 generated-and-verified and 20 needing trace. These are coverage/validation
entries, not vulnerability counts. No App Store availability claim is made.

Checkpoint 18: byte-identical XRP codec reproduction closes its generated-asset
trace. Adding its previously unenumerated upstream closure increases the combined
gate to **16,768 open entries**. The 170 upstream input files remain outstanding.
Direct compiler inputs: 244 reviewed, 137 partial, 1,496 outstanding,
460 generated-and-verified and 20 needing trace. JavaScript assets are outside
that direct Swift/C compiler trace. No overall completion claim is made.

Checkpoint 20 adds 38 passing production-vault/EVM imported-key host checks and
a two-failure deliberate stale-envelope control. Three partial file dispositions
leave 244 reviewed, 140 partial, 1,493 outstanding direct compiler inputs; generated
counts are unchanged. The combined gate remains 16,769 open entries. Signing-to-
journal/removal atomicity and the full review remain incomplete.
