const { Interface } = require('ethers');
const abi = new Interface(['function isValidSignature(bytes32 hash, bytes signature) view returns (bytes4)']);
const messageHash = '0x' + 'ab'.repeat(32);
const lengths = [0, 1, 31, 32, 33, 64, 65, 66, 96, 130];
process.stdout.write('// Generated with ethers 6.15.0 Interface.encodeFunctionData. Synthetic bytes only.\n');
process.stdout.write('enum ContractSignatureVectors {\n    static let calldata: [Int: String] = [\n');
for (const length of lengths) {
  const bytes = Uint8Array.from({length}, (_, i) => i % 251);
  const data = abi.encodeFunctionData('isValidSignature', [messageHash, bytes]);
  process.stdout.write(`        ${length}: "${data}",\n`);
}
process.stdout.write('    ]\n}\n');
