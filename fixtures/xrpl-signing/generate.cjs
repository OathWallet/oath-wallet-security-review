// Deterministic PUBLIC test wallets, never funded or sent to a ledger.
const fs=require('fs'),crypto=require('crypto');
const {createRequire}=require('module');
const load=createRequire(process.argv[2]+'/package.json');
const xrpl=load('xrpl'),{decodeAccountID}=load('ripple-address-codec');
const wallet=n=>xrpl.Wallet.fromEntropy(new Uint8Array(16).fill(n),{algorithm:xrpl.ECDSA.secp256k1});
const owner=wallet(71),recipient=wallet(90).address;
const signers=Array.from({length:8},(_,i)=>wallet(80+i)).sort((a,b)=>Buffer.compare(decodeAccountID(a.address),decodeAccountID(b.address)));
const mpt='000000010000000000000000000000000000000000000000';
const issued=['1e-81','1.234567890123456','1e90','9.999999999999999e95'];
const vectors=[];
function add(kind,value,threshold,tag){
 const multi=threshold>0,setup=['signerList','disableMaster'].includes(kind),authorize=['trust','authorize'].includes(kind);
 const ref=['issued','trust','hex'].includes(kind)?(kind==='hex'?'0158415500000000C1F76FF6ECB0BAC600000000':'OAT')+'.'+recipient:['mpt','authorize'].includes(kind)?mpt:'native';
 const amount=ref==='native'?value:ref.includes('.')?{currency:ref.split('.')[0],issuer:recipient,value}:{mpt_issuance_id:mpt,value};
 const fee=kind==='closure'?'200000':String(12*(multi&&!setup?threshold+1:1));
 let tx={TransactionType:'Payment',Flags:2147483648,Account:owner.address,Destination:recipient,Amount:amount,Fee:fee,Sequence:42,LastLedgerSequence:400};
 if(tag!==null)tx.DestinationTag=tag;
 if(ref!=='native')tx.SendMax=amount;
 if(setup){tx={TransactionType:kind==='signerList'?'SignerListSet':'AccountSet',Flags:2147483648,Account:owner.address,Fee:fee,Sequence:42,LastLedgerSequence:400};if(kind==='signerList'){tx.SignerQuorum=threshold;tx.SignerEntries=signers.map(s=>({SignerEntry:{Account:s.address,SignerWeight:1}}));}else tx.SetFlag=4;}
 if(authorize){tx={TransactionType:kind==='trust'?'TrustSet':'MPTokenAuthorize',Flags:kind==='trust'?2147614720:2147483648,Account:owner.address,Fee:fee,Sequence:42,LastLedgerSequence:400};if(kind==='trust')tx.LimitAmount=amount;else tx.MPTokenIssuanceID=mpt;}
 if(kind==='closure'){tx.TransactionType='AccountDelete';delete tx.Amount;}
 let blob=multi&&!setup?xrpl.multisign(signers.slice(0,threshold).map(s=>s.sign({...tx,SigningPubKey:''},true).tx_blob)):owner.sign(tx).tx_blob;
 vectors.push({kind,value,threshold,tag,reference:ref,fee,bytes:blob,hash:xrpl.hashes.hashSignedTx(blob)});
}
for(const tag of [null,0,4294967295]){
 for(const value of ['1','1234567','99999999998999988'])add('native',value,0,tag);
 for(const value of issued)add('issued',value,0,tag);
 add('hex','1.25',0,tag);
 for(const value of ['1','9223372036854775807'])add('mpt',value,0,tag);
 add('closure','800000',0,tag);
}
for(const threshold of [1,2,4,8]){
 for(const kind of ['native','issued','mpt','trust','authorize','signerList','disableMaster'])add(kind,['issued','trust'].includes(kind)?'1.25':kind==='authorize'||kind==='signerList'||kind==='disableMaster'?'0':'123',threshold,null);
}
const hashes=[0,1,31,32,55,56,63,64,65,127,128,129,1024].map(length=>{const bytes=Buffer.from(Array.from({length},(_,i)=>(i*37+length)%256));return{input:bytes.toString('hex'),digest:crypto.createHash('ripemd160').update(bytes).digest('hex')};});
fs.writeFileSync(process.argv[3],JSON.stringify({sdk:'xrpl@5.3.0',source:'PUBLIC repeated-byte entropy; no real credentials',account:owner.address,publicKey:owner.publicKey,key:owner.privateKey.slice(2),signers:signers.map(s=>({account:s.address,key:s.privateKey.slice(2)})),recipient,vectors,hashes},null,2)+'\n');
console.log(`${vectors.length} transaction vectors and ${hashes.length} RIPEMD vectors`);
