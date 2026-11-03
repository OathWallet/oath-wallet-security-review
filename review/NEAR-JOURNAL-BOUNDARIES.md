# NEAR access grants, durable journals and removal boundaries

Read and tested application source: `0614556b993f85808b13e3a69984ce36050a8dfe`.
The four fully read files are byte-identical at the build-104 baseline and
PR81's merge. [Hashes and exact read ranges](../evidence/5.0.2-build104/near-journal-boundaries/source-binding.json)
bind these observations to source, not to a released App Store binary.

## Source observations

- `WalletConnectNearAccess.swift` accepts only the supported sign-in/out
  methods, exact parameter fields, one to eight distinct public keys and the
  selected account. Sign-in builds restricted FunctionCall keys with a fixed
  gas allowance, receiver and method list; it does not build FullAccess keys.
  Empty method lists allow every method on that receiver. Own-key replacement
  is rejected. Sign-out requires both a session-scoped local grant and matching
  provider-reported receiver/method permissions. Validation reconstructs the
  exact expected transaction bytes; signature verification binds those bytes,
  public key and transaction hash. Recovery replays the original signed bytes.
- `WalletConnectNearJournal.swift` validates serialized access, review and
  signature records before recovery. New writes require an active matching
  wallet/account, exclude multisignature accounts, reserve the sender across
  pending work, and bind duplicates to the original wallet, account, topic and
  signed payload. Grant insertion/removal and submission settlement share one
  database transaction. Terminal results are immutable. Reset triggers reject
  late writes, and foreign keys remove dependent records with their wallet.
- `WalletRemovalReservation.swift` reserves removal inside one writer
  transaction after checking pending transactions. INSERT/UPDATE triggers stop
  new pending journal work for that wallet. Cleanup uses captured reservation
  tokens; an older cleanup cannot release a newer reservation.
- `OathWalletConnectNearViews.swift` renders account, network, maximum fee,
  recipient and parsed action descriptions. Printable UTF-8 arguments may be
  displayed instead of base64. Completion distinguishes pending, confirmed and
  failed results. This was a source read, not a visual or accessibility test.

Supporting service excerpts were traced through preparation, renewed review,
signing, journal insertion and recovery. The service checks operation identity
around signing, and recovery submits already-signed journal records. Only the
listed excerpts were read here; this is not a whole-file service review.

## Tests actually executed

Eight existing production database XCTest methods passed, zero failures or
skips, on the pinned source. Each method ran in a separate process with network
access denied. The three NEAR journal methods cover restart recovery, duplicate
requests, session-scoped grants, cross-wallet reuse, tampered signatures,
conflicting ordinary sends, reset and grant cleanup. Five removal methods cover
pending versus terminal states, legacy cleanup and late reset writes.

The multi-chain removal matrix inserts synthetic schema rows; it is **not** a
signature test for every chain. Its XRP fixture uses real journal validation.
These are pre-existing tests replayed against this source, not eight newly
discovered defects or independently generated protocol vectors. The separate
Swift Testing selection has zero methods and is not counted as a pass.

```sh
python3 scripts/near-journal-boundaries.py /path/to/wallet /path/to/scratch /path/to/evidence
```

The driver requires a clean exact revision, clears inherited provider/live-test
flags, verifies all eight method identities and rejects skipped, duplicate,
missing or failing results. Compilation can resolve public dependencies before
the denied-network execution phase. [Receipts and logs](../evidence/5.0.2-build104/near-journal-boundaries/manifest.json).

## Remaining scope

No new application defect was confirmed by this source read and replay. All
four new dispositions remain partial: provider-state authenticity, independent
NEAR serialization vectors, malformed persisted Codable combinations, UI
presentation, every cancellation/removal interleaving, relay integration and
upstream implementations are not closed. A local grant records authorization;
it is not proof that the chain's current permissions remain unchanged.

The reservation trigger insertion/update matrix was source-read here, but its
separate `WalletRemovalReservationTests` suite was not part of the eight-method
selection. Earlier reservation evidence remains separately documented.
No application source, simulator, physical device, live chain or App Store
operation changed in this checkpoint.


## Hosted replay

Run [41605014923](https://github.com/devdasx/oath-wallet-security-review/actions/runs/41605014923)
passed all eight methods. Downloaded archive, receipt and case-log hashes are
verified in the [durable manifest](../evidence/5.0.2-build104/hosted-near-journal/manifest.json).
Independent serialization work and its separate reader repair are now recorded
in [the NEAR signing checkpoint](NEAR-SIGNING-VECTORS.md); the other limitations
above remain open.
