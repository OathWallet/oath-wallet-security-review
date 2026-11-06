// Audit-only synthetic fixtures. Public deterministic seeds; never fund these accounts.
const fs=require('node:fs'), assert=require('node:assert/strict');
const w=require('@solana/web3.js');
const owner=w.Keypair.fromSeed(Buffer.alloc(32,61)), stake=w.Keypair.fromSeed(Buffer.alloc(32,62)).publicKey;
const other=w.Keypair.fromSeed(Buffer.alloc(32,63)).publicKey, wrapper=w.Keypair.fromSeed(Buffer.alloc(32,64)).publicKey;
const blockhash=w.Keypair.fromSeed(Buffer.alloc(32,65)).publicKey.toBase58();
assert.equal(require('@solana/web3.js/package.json').version,'1.98.4');
const vectors=[];
for(const version of ['legacy','v0']) for(const kind of ['withdraw-authority','stake-authority','noop-authority','withdraw','cpi']){
 let instructions;
 if(kind==='cpi') instructions=[new w.TransactionInstruction({programId:wrapper,keys:[{pubkey:owner.publicKey,isSigner:true,isWritable:true},{pubkey:stake,isSigner:false,isWritable:true}],data:Buffer.from([1])})];
 else if(kind==='withdraw')instructions=w.StakeProgram.withdraw({stakePubkey:stake,authorizedPubkey:owner.publicKey,toPubkey:other,lamports:10_000_000_000}).instructions;
 else instructions=w.StakeProgram.authorize({stakePubkey:stake,authorizedPubkey:owner.publicKey,newAuthorizedPubkey:kind==='noop-authority'?owner.publicKey:other,stakeAuthorizationType:kind==='stake-authority'?w.StakeAuthorizationLayout.Staker:w.StakeAuthorizationLayout.Withdrawer}).instructions;
 const tm=new w.TransactionMessage({payerKey:owner.publicKey,recentBlockhash:blockhash,instructions});
 const message=version==='legacy'?tm.compileToLegacyMessage():tm.compileToV0Message();
 const tx=new w.VersionedTransaction(message); const unsigned=Buffer.from(tx.serialize()).toString('base64'); tx.sign([owner]);
 vectors.push({version,kind,unsigned,signed:Buffer.from(tx.serialize()).toString('base64'),message:Buffer.from(message.serialize()).toString('base64')});
}
// StakeStateV2::Initialized: u32 discriminant + Meta, padded to 200 bytes.
const before=Buffer.alloc(200);before.writeUInt32LE(1,0);before.writeBigUInt64LE(2_282_880n,4);owner.publicKey.toBuffer().copy(before,12);owner.publicKey.toBuffer().copy(before,44);
const after=Buffer.from(before);other.toBuffer().copy(after,44);
const result={sdk:'@solana/web3.js 1.98.4',synthetic:true,owner:owner.publicKey.toBase58(),seed:Buffer.alloc(32,61).toString('base64'),stake:stake.toBase58(),attacker:other.toBase58(),program:w.StakeProgram.programId.toBase58(),before:before.toString('base64'),after:after.toString('base64'),vectors};
fs.writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');console.log('Generated 10 synthetic official-SDK stake wires; account layout is independently specified from pinned StakeStateV2.');
