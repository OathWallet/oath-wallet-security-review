# Solana transaction buffer-origin review

This maintainer-commissioned, Codex-led checkpoint concerns collection indexing
in three production Solana transaction boundaries. It is not independent
certification or a complete wallet audit.

## Source and repair

- Baseline: `ce9d27baf5e6d81452b46d5a2b5688da2fcd93d7`, public 5.0.3 (105).
- Repair: `4b29aa2d73582c7b0c037723726a7a9972c7700a`.
- [Merged PR #97](https://github.com/OathWallet/oath-wallet/pull/97):
  `02ec5362c188134c42632c555ed5401218d653cb`. Repair and merge share tree
  `709013fe464096792193a77bf640825a6e0c9bf0`.
- Finding: [OW-2026-074](../findings/OW-2026-074.md).
- [Partial source coverage](../evidence/5.0.3-build105/solana-buffer/source-binding.json).

The parser's array offsets were applied to a `Data` slice whose starting index
could be nonzero. This could extract the wrong message, reject a valid signature,
or trap. Signature comparison and submission had the same origin assumption.
The fix rebases input without changing its bytes. Normal base64-decoded requests
were not shown to trigger the defect; exploitability through ordinary dApp input
remains unproven. No funded account or network transaction is involved.

## Reproduce

Use a compatible macOS/Xcode toolchain and Python 3.14. Clone both public
repositories, check out the exact repair above, and use fresh scratch/output
paths. From the audit repository:

```sh
python3 scripts/solana-buffer-review.py ../wallet ../buffer-build ../buffer-results
python3 -m unittest discover -s tests -p test_solana_buffer_review.py
```

The driver archives the production packages at both immutable commits and
injects the identical public fixture. Each stage uses its own fresh build
folder and constrained dependency lock. It records toolchain, source archive,
fixture, lockfile, executable and individual log hashes. SwiftPM may download
public dependencies during compilation; every XCTest process denies networking.
The submission tests use an injected transport and cannot broadcast a transaction.

Before repair, the driver requires both controls to pass, the two signed-slice
methods to fail specifically with signature-validation errors, and the unsigned
slice method to reproduce incorrect origin/message assertions followed by
SIGTRAP. Compilation failures or unrelated failures do not qualify. After repair,
all selected methods must pass with no skips. The process limit is four, and each
method runs separately so the baseline trap cannot hide other outcomes.

## Validation status

The clean-snapshot paired driver completed in 243.611 seconds. Before repair,
two control methods passed and three slice methods failed in the required way
(one SIGTRAP and two signature-validation errors). After repair, all 41 selected
Solana methods passed with zero failures or skips, including the identical five
regression methods. Each test process denied networking.

The separate diagnostics suite passed 119 methods and skipped two. One skip
requires a fresh process and `OATH_TRACE_OUTBOX_TEST=1`; that method was rerun
separately with networking denied and passed without a skip. The remaining
optional live-provider check was not run. The original suite log retains both
skips. Diagnostics coverage passed for 722 catch sites. Public-source boundary
validation, direct secret scanning and diff checks passed.

An unsigned generic iOS **Release** build succeeded on Xcode 27.2 (27B52),
Swift 6.4.2. The compiled product reports 5.0.3 (105); the build receipt records
its executable hash and the exact tested source. Compilation is not a runtime
test or proof of an installed App Store binary.

[Manifest](../evidence/5.0.3-build105/solana-buffer/manifest.json),
[paired logs](../evidence/5.0.3-build105/solana-buffer/runs.zip),
[build, diagnostics and exploratory evidence](../evidence/5.0.3-build105/solana-buffer/validation.zip),
[build receipt](../evidence/5.0.3-build105/solana-buffer/build-receipt.json) and
[merge receipt](../evidence/5.0.3-build105/solana-buffer/pr.json)
preserve results and checksums. The earlier exploratory failures are retained;
the headline paired counts come only from the final clean-snapshot run.
The hosted replay completed successfully; its original downloaded artifact
matches GitHub's checksum and every recorded file/case hash. The initial delayed
workflow status and later completed receipt are both retained.
The replay took 677.962 seconds and reproduced two passing controls and three
expected failures before repair, then 41 passes without skips afterward.
[Run](https://github.com/OathWallet/oath-wallet-security-review/actions/runs/42200304981) ·
[Download verification](../evidence/5.0.3-build105/hosted-solana-buffer/verification.json).

## Scope limits

The source ledger records only the constructor, signature verification and
submission ranges inspected for this finding. The frozen inventory remains
unchanged; passing methods do not turn entire files into reviewed components.
Tests use existing public SDK vectors and synthetic transport responses. They do
not prove provider honesty, all instruction semantics, runtime UI behavior,
validator acceptance, or App Store binary equivalence. No simulator or physical
device was used, and no Apple upload or release-tag movement is included.
