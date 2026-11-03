// Public deterministic synthetic keys only. Never fund these accounts.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash, createPublicKey, verify} from 'node:crypto';
const [sdkRoot, output] = process.argv.slice(2);
const sdk = await import(pathToFileURL(path.join(sdkRoot, 'node_modules/near-api-js/lib/index.js')).href);
const {KeyPair, createTransaction, actions:a, baseEncode, encodeTransaction, Signature, SignedTransaction} = sdk;
const max = (1n << 128n)-1n, block = Buffer.alloc(32,3), plans=[], extra=[];
const b64 = data => Buffer.from(data).toString('base64');
function vector(key, sender, receiver, nonce, actions) {
  const transaction=createTransaction(sender,key.getPublicKey(),receiver,nonce,actions,block);
  const raw=encodeTransaction(transaction), digest=createHash('sha256').update(raw).digest();
  const sig=key.sign(digest).signature;
  const publicKey=Buffer.from(key.getPublicKey().data);
  const nativeKey=createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),publicKey]),format:'der',type:'spki'});
  if (!verify(null,digest,nativeKey,sig)) throw Error('Independent signature validation failed');
  return {sender,receiver,nonce:String(nonce),publicKey:b64(publicKey),raw:b64(raw),signature:b64(sig),signed:b64(new SignedTransaction({transaction,signature:new Signature({keyType:0,data:sig})}).encode()),hash:baseEncode(digest),block:baseEncode(block)};
}
for(let keyIndex=0;keyIndex<2;keyIndex++) {
  const seed=Buffer.from(Array.from({length:32},(_,i)=>(i+keyIndex*32)%256));
  const key=KeyPair.fromString('ed25519:'+baseEncode(seed));
  const sender=keyIndex ? Buffer.from(key.getPublicKey().data).toString('hex') : 'sender.testnet';
  const recipient='recipient.testnet';
  for(const amount of [1n,1n<<32n,1n<<64n,max-1n]) for(const nonce of [1n,9007199254740993n,(1n<<64n)-1n]) for(const mode of ['native','token','registration']) {
    const token=mode!=='native', storage=mode==='registration' ? 1000n:0n;
    const actions=[];
    if(storage) actions.push(a.functionCall('storage_deposit',Buffer.from(JSON.stringify({account_id:recipient,registration_only:true})),30000000000000n,storage));
    actions.push(token ? a.functionCall('ft_transfer',Buffer.from(JSON.stringify({amount:String(amount),receiver_id:recipient})),50000000000000n,1n) : a.transfer(amount));
    plans.push({...vector(key,sender,token?'wrap.testnet':recipient,nonce,actions),seed:b64(seed),recipient,mode,amount:String(amount),balance:String(max),storage:String(storage)});
  }
}
const seed=Buffer.from(Array.from({length:32},(_,i)=>i));
const key=KeyPair.fromString('ed25519:'+baseEncode(seed));
const delegate=KeyPair.fromString('ed25519:'+baseEncode(Buffer.alloc(32,9))).getPublicKey();
const actions=[a.createAccount(),a.deployContract(Buffer.from([0,97,115,109,1,0,0,0])),a.functionCall('method',Buffer.from('{"hello":"world"}'),1000000000000n,42n),a.transfer(max),a.stake(123n,delegate),a.addFullAccessKey(delegate),a.addFunctionCallAccessKey(delegate,'wrap.testnet',['ft_transfer'],250000000000000000000000n),a.addFunctionCallAccessKey(delegate,'wrap.testnet',[]),a.deleteKey(delegate),a.deleteAccount('beneficiary.testnet')];
for(let i=0;i<actions.length;i++) extra.push({...vector(key,'sender.testnet','sender.testnet',BigInt(i+1),[actions[i]]),seed:b64(seed),kind:[0,1,2,3,4,5,5,5,6,7][i]});
fs.writeFileSync(output,JSON.stringify({sdk:'near-api-js@7.3.1',plans,actions:extra},null,2)+'\n');
console.log(`Generated ${plans.length} plan vectors and ${extra.length} action vectors; SDK signatures verified by Node crypto.`);
