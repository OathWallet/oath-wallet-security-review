# Source checkout recovery

The exact-baseline Electrum job failed while cloning the public repository: Git reported an RPC receive timeout, early EOF and invalid index-pack output. The test step was skipped. This is an infrastructure failure, not an Electrum test failure. [Original job and retained log hashes](../evidence/5.0.1-build103/checkout-recovery/result.json).

The audit checkout helper now downloads into a disposable sibling directory, validates the selected revision and clean source state, then publishes that completed checkout. A failed clone is retried at most three times with a ten-minute timeout per attempt. Invalid revisions and dirty existing checkouts are not retried or overwritten. A destination appearing while the download runs is preserved. Full Git history remains available because before/after audit fixtures use historical objects.

Eight tests use temporary synthetic Git repositories. They verify exact pinning with newer history retained, existing dirty/wrong-revision preservation, partial clone cleanup and fresh retry, bounded repeated timeouts, invalid-pin failure, a concurrent destination and zero attempts. All eight pass. The complete audit helper suite passes 236 tests. These tests do not recreate GitHub's external outage or guarantee future network availability.

The dedicated GitHub checkout/Electrum retest is separate from the retained failed job. It does not rerun the other known baseline application failures or silently replace their evidence. No wallet implementation changed in this repair.
