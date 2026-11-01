# Preserve raw advisories; validate the exact compiled source selection

Historical run [41257431422](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41257431422)
completed with 41 successful jobs and one failed scanner job. Its application
target was `f7441b85d5216b702dde490eb027aece1a6cfb5a`, **not** the current target.
The scanner's exit 1 corresponds to 40 raw advisory occurrences. The same run's
selected-source analysis reports zero unresolved advisory dispositions for the
three bridge targets. Neither result should be discarded or called a clean raw
scan. Standard-library, binary and whole-wallet assurance have broader scope.

The workflow previously made the raw module scan the final gate even when its
advisories affected packages excluded from the three actual build graphs. The
repair preserves the raw exit code and JSON, then runs an explicit dependent
gate using the scanner and selected-source artifacts from **the same run**.
It verifies the application commit and `go.mod`/`go.sum` hashes before applying
the existing conservative package/advisory classification.

Scanner execution errors, malformed output, report/exit inconsistencies, wrong
source/lock hashes, missing target graphs, compiled affected packages and
unresolved advisories fail. A raw exit 1 is not rewritten to zero in the saved
evidence. Clean scan output still requires all three nonempty target graphs.
No blanket advisory allowlist or severity suppression was introduced.

Ten new helper tests exercise these cases; the full helper suite passes 72
tests. A replay against the completed historical run preserves raw exit 1 and
all 40 occurrences while reporting zero unresolved selected-source dispositions.
That replay is for the historical `f7441b8` target only. It is not a current-target
GitHub pass, and does not retrospectively change the failed run's conclusion.

See [the gate](../scripts/advisory_gate.py), [its tests](../tests/test_advisory_gate.py)
and [retained replay and original job logs](../evidence/advisory-gate).
The workflow adds a separate required `advisory-gate` check. Its new execution
must be checked independently after publication. No production credential or
deployment job is involved.
