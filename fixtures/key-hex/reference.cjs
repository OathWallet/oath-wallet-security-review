const c = require('node:crypto');
// Synthetic private bytes and the RFC 7748 public base point; no wallet data.
const privateBytes = Buffer.alloc(32, 0x42);
const publicBytes = Buffer.concat([Buffer.from([9]), Buffer.alloc(31)]);
const privateKey = c.createPrivateKey({key: Buffer.concat([Buffer.from('302e020100300506032b656e04220420', 'hex'), privateBytes]), format: 'der', type: 'pkcs8'});
const publicKey = c.createPublicKey({key: Buffer.concat([Buffer.from('302a300506032b656e032100', 'hex'), publicBytes]), format: 'der', type: 'spki'});
const secret = c.diffieHellman({privateKey, publicKey});
const derived = Buffer.from(c.hkdfSync('sha256', secret, Buffer.alloc(0), Buffer.alloc(0), 32));
console.log(JSON.stringify({node: process.version, openssl: process.versions.openssl, privateInput: '32 bytes of 0x42, synthetic only', publicInput: 'RFC 7748 base point 9', hkdf: {algorithm: 'sha256', salt: '', info: '', length: 32}, expected: Array.from(derived)}, null, 2));
