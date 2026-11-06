# Solana stake review fixtures

Audit-only synthetic credentials. Never fund these accounts.

`generate.cjs` generates ten legacy/version-zero messages using
`@solana/web3.js` 1.98.4. Install the existing exact lockfile in
`fixtures/squads-sdk` into a separate directory with `npm ci --ignore-scripts`,
then point `NODE_PATH` at its `node_modules` and run:

```sh
node fixtures/solana-stake-authority/generate.cjs generated.json
cmp generated.json fixtures/solana-stake-authority/sdk-vectors.json
```

Stake account snapshots follow `StakeStateV2::Initialized` at upstream commit
`e64c0c3c3dfd22f88b9fdea29b4a65b804ae554a` in
[solana-program/stake](https://github.com/solana-program/stake/blob/e64c0c3c3dfd22f88b9fdea29b4a65b804ae554a/interface/src/state.rs).
They are independently specified synthetic account bytes, not a validator result.
The custom-program vectors exercise injected CPI effects; no on-chain custom
program was deployed. Public seeds are deterministic fixture inputs only.

Both independent SDK signatures and production signatures must verify over the
same message. Their signature bytes need not be identical: CryptoKit signing can
randomize them. The initial mistaken equality assertion and its correction are
retained in the checkpoint's exploratory evidence.
