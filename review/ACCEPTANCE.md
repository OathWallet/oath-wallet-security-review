# Acceptance checklist — in progress

Progress 50 uses initial release 4.1.15 (100), `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`, and current tested public source `a13a88cb67fe9fa73c1a0bbb222a474b195e25eb`. [Merged source](https://github.com/devdasx/oath-wallet/pull/47) · [evidence manifest](../evidence/typed-keys/manifest.json).

- 4,845 files inventoried in the application repository, 313 reviewed, 766 partial, 3,715 outstanding before category exclusions. 16,301 open ledger entries across source, dependencies and validation. The larger denominator explicitly includes 2,348 additional Rust registry files and two further complete crate archives. Not all entries are code that executes on iOS.
- OW-2026-001 and OW-2026-003 through OW-2026-035 have verified public source repairs. OW-2026-002 has an unresolved historical binary provenance limitation. Later App Store availability has not been established.
- 30 current source checks have passing local records; 74 other required checks lack a passing record on this commit. Four previously stored synthetic wallet formats retained their original scripts through encrypted cold reopen and re-backup. Host tests, local generic unsigned compilation and the separate hosted Rust reconstruction are distinct.
- BDK device archive equality, other binary provenance, substantive file review, and further exact-source validations remain open. See the [BDK and importer trace](EXTENDED-KEY-IMPORT.md) and [public Actions history](https://github.com/devdasx/oath-wallet-security-review/actions).

The exact reviewed target initially failed two provider test assertions. The separately identified test-only revision `5f92dc2a87334c0b4942dea1f6a47ad92770f4a3` corrects their arrival-order assumptions and passes the complete provider suite. This outcome is recorded separately from the exact-target passing checks above.
