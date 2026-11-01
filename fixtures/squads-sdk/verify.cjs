// Regenerate public test vectors in a temporary directory, never in the app tree.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const source = fs.realpathSync(process.argv[2]);
const lock = JSON.parse(fs.readFileSync(path.join(__dirname, 'package-lock.json')));
const versions = {'@sqds/multisig': '2.1.4', '@solana/web3.js': '1.98.4', '@solana/spl-token': '0.4.14'};
for (const [name, version] of Object.entries(versions)) {
  assert.equal(lock.packages[`node_modules/${name}`].version, version);
  assert.equal(JSON.parse(fs.readFileSync(path.join(__dirname, 'node_modules', name, 'package.json'))).version, version);
}
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'oath-squads-proof-'));
const relative = 'Packages/OathAnkr/Tests/OathAnkrTests/Fixtures/SolanaMultisig/sdk-vectors.json';
const generator = path.join(source, 'Tools/GenerateSolanaMultisigVectors.cjs');
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
try {
  const run = spawnSync(process.execPath, [generator], {
    cwd: temp, timeout: 120000, maxBuffer: 1024 * 1024,
    env: {PATH: process.env.PATH, NODE_PATH: path.join(__dirname, 'node_modules')},
    encoding: 'utf8'
  });
  assert.equal(run.error, undefined, 'Generator must finish without timeout');
  assert.equal(run.status, 0, `Generator failed: ${run.stderr}`);
  const expected = fs.readFileSync(path.join(source, relative));
  const actual = fs.readFileSync(path.join(temp, relative));
  // Compare complete files, including every message, signature and account byte.
  assert.equal(sha256(actual), sha256(expected), 'Regenerated fixture differs');
  const vectors = JSON.parse(actual).vectors;
  assert.equal(vectors.length, 76);
  const counts = Object.fromEntries(['setup', 'native', 'spl', 'token2022'].map(kind => [kind, vectors.filter(v => v.kind === kind).length]));
  assert.deepEqual(counts, {setup: 19, native: 19, spl: 19, token2022: 19});
  console.log(JSON.stringify({check: 'squads-sdk-regeneration', status: 'passed', vectors: vectors.length,
    kinds: counts, versions, node: process.version, fixture_sha256: sha256(expected),
    generator_sha256: sha256(fs.readFileSync(generator)),
    dependency_lock_sha256: sha256(fs.readFileSync(path.join(__dirname, 'package-lock.json'))),
    scope: 'Complete deterministic fixture equality; no deployed program or production transaction proof'}, null, 2));
} finally {
  fs.rmSync(temp, {recursive: true, force: true});
}
