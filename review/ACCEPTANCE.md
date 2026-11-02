# Acceptance checklist — in progress

Baseline 4.1.15 (100), `c7cdbde5e9f136b595500e92fbc904b107dcd8ee`. Current public application commit `7ecfa2c163704d363ebe6dc16b60151dc8a7cd78`. [Release evidence](../evidence/native-inputs/manifest.json).

- The 4,846 application-repository files retain 314 reviewed, 768 partially reviewed and 3,713 outstanding file dispositions before category exclusions. Across application, dependency and validation ledgers there are 17,116 open entries. The 823 newly inventoried native registry files account for the change in scope.
- 38 passing exact-target check records are published. 68 required checks lack a passing record for the current revision. Previous-commit results remain attributed to their exact sources.
- The distributed BDK arm64 iOS static archive is now independently reproduced by full bytes. The C/assembly trace, historical aezeed limitations, other binary slices, source coverage and App Store binary identity remain distinct.
- OW-2026-001 and OW-2026-003 through OW-2026-036 have public repairs and retest evidence. OW-2026-002 remains an open historical provenance limitation. No App Store upload is part of this work.
