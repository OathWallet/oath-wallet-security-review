# Acceptance checklist — in progress

Progress 49 tests public source `0e50b16ae1ced7934d57dba42d3e6e69ccf6cfc8`. The original release was 4.1.15 (100), `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. The [public source repair](https://github.com/devdasx/oath-wallet/pull/46) and [test evidence](../evidence/provider-response/manifest.json) concern that source tree. App Store binary equivalence remains unverified.

- 4,842 repository files inventoried, 308 reviewed, 759 partially reviewed, and 3,724 outstanding before category exclusions. 13,838 entries remain across application, dependency and validation ledgers. These entries include development files awaiting reachability classification.
- OW-2026-001 and OW-2026-003 through OW-2026-034 have verified source fixes. OW-2026-002 retains a historical binary-provenance limitation.
- 16 exact-source checks passed locally. Fifteen before/after transfer tests and five independent-wire Stellar tests are distinct from the broader host package runs. 81 required validations lack a passing record at this exact revision. Current GitHub matrix completion is separate.
- The release compiler ledger and seven newly examined Stellar source files narrow specific boundaries. The remaining SDK, Wallet Core, BDK, Rust and other source and binary implementation gaps remain open. See [Stellar](STELLAR-XDR-BOUNDARIES.md), [network boundaries](HTTP-RESPONSE-BOUNDARIES.md) and [prior dependency inventory](BITCOIN-SIGNER-AND-CORE.md).
