// Independent ABI implementation checks the Python-generated public fixtures.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {AbiCoder, Interface, version} = require('ethers');
assert.equal(version, '6.15.0');
const rows = JSON.parse(fs.readFileSync(path.join(process.argv[2],
  'Packages/OathAnkr/Tests/OathAnkrTests/Fixtures/WalletConnect/approval-operations.json')));
const abi = AbiCoder.defaultAbiCoder();
const router = new Interface(['function execute(bytes,bytes[])']);
const expected = {
  'swap-only': '0x00', 'swap-transfer-2': '0x0002', 'swap-transfer-4': '0x0004',
  'swap-transfer-5': '0x0005', 'transfer-before-swap': '0x0200',
  'nested-optional-transfer': '0x00a1', 'swap-balance-check': '0x000e',
  'swap-other-recipient': '0x0002', 'swap-other-amount': '0x0002', 'swap-unknown': '0x003f'
};
assert.deepEqual(rows.map(x => x.name).sort(), Object.keys(expected).sort());
for (const row of rows) {
  const [commands, inputs] = router.decodeFunctionData('execute', row.data);
  assert.equal(commands, expected[row.name]);
  assert.equal(router.encodeFunctionData('execute', [commands, inputs]), row.data);
  const swap = inputs[row.name === 'transfer-before-swap' ? 1 : 0];
  const fields = abi.decode(['address','uint256','uint256','bytes','bool'], swap);
  assert.equal(fields[0], '0x0000000000000000000000000000000000000001');
  assert.equal(fields[1], 123456789n); assert.equal(fields[2], 100000000n);
  assert.equal(fields[3], '0x' + '11'.repeat(20) + '000bb8' + '33'.repeat(20));
  assert.equal(fields[4], true);
  if (row.name === 'swap-only' || row.name === 'swap-unknown') continue;
  let payload = inputs[row.name === 'transfer-before-swap' ? 0 : 1];
  if (row.name === 'nested-optional-transfer') {
    const [commands, inputs] = abi.decode(['bytes','bytes[]'], payload);
    assert.equal(commands, '0x02'); assert.equal(inputs.length, 1); payload = inputs[0];
  }
  const fields2 = abi.decode(['address','address','uint256'], payload);
  const balance = row.name === 'swap-balance-check';
  assert.equal(fields2[0], '0x' + (balance ? '66' : '55').repeat(20));
  assert.equal(fields2[1], '0x' + (balance ? '55' : row.name === 'swap-other-recipient' ? '77' : '66').repeat(20));
  assert.equal(fields2[2], row.name === 'swap-other-amount' ? 987654322n : 987654321n);
}
console.log(`ethers ${version}: ${rows.length} canonical ABI and semantic fixture cross-checks passed`);
