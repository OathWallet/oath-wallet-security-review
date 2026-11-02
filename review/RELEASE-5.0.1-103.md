# Security review of Oath Wallet 5.0.1 (103)

The active release under review is [v5.0.1-build103](https://github.com/devdasx/oath-wallet/releases/tag/v5.0.1-build103), source commit `c7acd23bb139864a40273f405d18b479589d2b20`. The maintainer's App Store Connect screen showed iOS version 5.0.1 Waiting for Review on 2 November 2026. The screen establishes the version status. The source tag establishes the GitHub build number. The [release verification receipt](../evidence/5.0.1-build103/release-verification.json) records the checks performed when the source release was created.

The 4.1.15 series is [historical](https://github.com/devdasx/oath-wallet-security-review/releases/tag/review-4.1.15-build100-progress57). Earlier before/after tests keep their source revisions. We compared the new tag against the prior inventory, retained 1,129 identical file dispositions, and returned 47 changed or removed entries for reassessment. The new inventory covers 4,839 tracked files. The primary Xcode dependency lock matches the recorded lock hash. [Transition and Git ancestry for each recorded fix](../evidence/5.0.1-build103/transition.json).

## Findings by release

- The two Bitcoin planner fixes in [PR 53](https://github.com/devdasx/oath-wallet/pull/53) are included in the 5.0.1 tag. Both regressions passed in the tagged release's [Bitcoin suite](../evidence/5.0.1-build103/checks/OathBitcoin/OathBitcoin.xml).
- The duplicate provider lookup repair in [PR 55](https://github.com/devdasx/oath-wallet/pull/55) and the payment recovery and interrupted reset repairs in [PR 56](https://github.com/devdasx/oath-wallet/pull/56) were merged after the build 103 tag. All three [interrupted-reset upgrade cases](../evidence/5.0.1-build103/interrupted-reset/result.json) failed on the exact release tag with SQLite’s reset write fence. The same three cases passed on the subsequent repaired tree. Later changes to main cannot modify that tag or a submitted build.
- The Swift path dependency repairs have [tested source patches](CORE-SWIFT-PATH-VALUES.md). The tag selects the earlier framework. Historical archive provenance is tracked in [OW-2026-002](../findings/OW-2026-002.md).

## Checks on this tag

The full Bitcoin host package passed 314 tests and skipped 60. Diagnostics passed 119 and skipped two. The wallet-security harness passed 158 assertions. The clipboard harness passed 33. The public source scan and diagnostics coverage check also passed. These fresh runs used the tagged source. A fresh [unsigned generic iOS Release build](../evidence/5.0.1-build103/checks/build/result.json) also passed. The resulting app declares version 5.0.1 and build 103. [Per-check results and logs](../evidence/5.0.1-build103/checks).

Application and dependency review continues. Historical results do not count as fresh results on build 103. This checkpoint makes no comparison to an Apple-distributed binary.
