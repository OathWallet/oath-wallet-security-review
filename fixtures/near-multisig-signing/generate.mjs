// Deliberately public synthetic seeds. Never fund these accounts.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash,createPublicKey,verify} from 'node:crypto';
const [sdkRoot,wasmPath,output]=process.argv.slice(2);
const {KeyPair,createTransaction,actions:a,baseEncode,encodeTransaction,Signature,SignedTransaction}=await import(pathToFileURL(path.join(sdkRoot,'node_modules/near-api-js/lib/index.js')).href);
const wasm=fs.readFileSync(wasmPath),wasmHash=createHash('sha256').update(wasm).digest('hex');
if(wasmHash!=='f3f9ee3e5e29d020dc73f581ff1490c03dff875ed01327dfebbe666724930a76')throw Error('Unexpected contract bytes');
const b64=b=>Buffer.from(b).toString('base64');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const args=v=>Buffer.from(JSON.stringify(canonical(v)));
const makeKey=n=>{const seed=Buffer.alloc(32,n),key=KeyPair.fromString('ed25519:'+baseEncode(seed));return {seed,key,pub:Buffer.from(key.getPublicKey().data)};};
const bootstrap=makeKey(99),sender=bootstrap.pub.toString('hex'),block=Buffer.alloc(32,3),max=(1n<<128n)-1n;
function vector(k,nonce,actions){
 const tx=createTransaction(sender,k.key.getPublicKey(),sender,nonce,actions,block),raw=encodeTransaction(tx),hash=createHash('sha256').update(raw).digest(),signature=k.key.sign(hash).signature;
 const pub=createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),k.pub]),format:'der',type:'spki'});
 if(!verify(null,hash,pub,signature))throw Error('SDK signature failed independent verification');
 return {nonce:String(nonce),publicKey:b64(k.pub),raw:b64(raw),signature:b64(signature),signed:b64(new SignedTransaction({transaction:tx,signature:new Signature({keyType:0,data:signature})}).encode()),hash:baseEncode(hash)};
}
const bundles=[];
for(const [required,count] of [[1,2],[2,3],[3,5],[7,10],[10,10]]){
 const keys=Array.from({length:count},(_,i)=>makeKey(i+1)).sort((a,b)=>Buffer.compare(a.pub,b.pub));
 for(const boundary of ['low','high'])for(const mode of ['deploy','secure','native','token','registration']){
  const stage=['deploy','secure'].includes(mode)?mode:'transfer',nonce=boundary==='low'?1n:(1n<<64n)-2n,requestID=boundary==='low'?0:4294967294;
  const amount=stage!=='transfer'?'1':boundary==='low'?'1':String(max-1n),storage=mode==='registration'?'1000':'0';
  const recipient=stage==='transfer'?'recipient.testnet':sender,token=mode==='token'||mode==='registration',parts=[];
  if(stage==='deploy')parts.push(vector(bootstrap,nonce,[a.deployContract(wasm),a.functionCall('new',args({members:keys.map(k=>({public_key:k.key.getPublicKey().toString()})),num_confirmations:required}),100000000000000n,0n)]));
  else if(stage==='secure')parts.push(vector(bootstrap,nonce,[a.deleteKey(bootstrap.key.getPublicKey())]));
  else {
   const actions=[];
   const call=(name,values,gas,deposit)=>({type:'FunctionCall',method_name:name,args:b64(args(values)),gas:String(gas),deposit:String(deposit)});
   if(storage!=='0')actions.push(call('storage_deposit',{account_id:recipient,registration_only:true},30000000000000n,storage));
   actions.push(token?call('ft_transfer',{amount,receiver_id:recipient},50000000000000n,1n):{type:'Transfer',amount});
   parts.push(vector(keys[0],nonce,[a.functionCall('add_request',args({request:{receiver_id:token?'wrap.testnet':recipient,actions}}),30000000000000n,0n)]));
   for(let i=0;i<required;i++)parts.push(vector(keys[i],nonce+(i===0?1n:0n),[a.functionCall('confirm',args({request_id:requestID}),150000000000000n,0n)]));
  }
  bundles.push({id:bundles.length,mode,stage,boundary,required,count,sender,recipient,reference:token?'wrap.testnet':'native',amount,balance:String(max),storage,nonce:String(nonce),requestID,block:baseEncode(block),bootstrap:b64(bootstrap.pub),publicKeys:keys.map(k=>b64(k.pub)),signerSeeds:(stage==='transfer'?keys.slice(0,required):[bootstrap]).map(k=>b64(k.seed)),parts});
 }
}
const partCount=bundles.reduce((n,b)=>n+b.parts.length,0);
if(bundles.length!==50||partCount!==188)throw Error('Unexpected fixture matrix');
fs.writeFileSync(output,JSON.stringify({sdk:'near-api-js@7.3.1',wasmHash,bundles,partCount},null,2)+'\n');
console.log(`Generated ${bundles.length} multisig bundles / ${partCount} independently signed transactions.`);
