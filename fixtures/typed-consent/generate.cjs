// Independent, deterministic EIP-712 expectations. Synthetic 0x01...01 key only.
'use strict';
const fs = require('node:fs');
const {Wallet, TypedDataEncoder, version} = require('ethers');
if(version !== '6.15.0') throw Error('Unexpected reference version');
const wallet = new Wallet('0x' + '01'.repeat(32));
const contract = '0x1111111111111111111111111111111111111111';
const spender = '0x2222222222222222222222222222222222222222';
const domain = {name:'Synthetic review', version:'1', chainId:'1', verifyingContract:contract};
const F = (name,type) => ({name,type});
const domainTypes = {name:'string',version:'string',chainId:'uint256',verifyingContract:'address',salt:'bytes32'};
const vectors = [], invalid = [];
function request(types,message,d=domain) {
  return {types:{EIP712Domain:Object.keys(d).map(n=>F(n,domainTypes[n])),...types},
    primaryType:TypedDataEncoder.from(types).primaryType,domain:d,message};
}
async function add(name,types,message,d=domain,raw=false) {
  let json=JSON.stringify(request(types,message,d));
  if(raw) json=json.replace('"value":'+JSON.stringify(message.value),'"value":'+message.value);
  vectors.push({name,json,chainId:d.chainId||'1',account:wallet.address,
    domainHash:TypedDataEncoder.hashDomain(d),messageHash:TypedDataEncoder.from(types).hash(message),
    digest:TypedDataEncoder.hash(d,types,message),signature:await wallet.signTypedData(d,types,message)});
}
function reject(name,type,value) {
  invalid.push({name,json:JSON.stringify(request({Value:[F('value',type)]},{value}))});
}
(async()=>{
  for(let width=8;width<=256;width+=8) {
    const n=BigInt(width), u=(1n<<n)-1n, top=(1n<<(n-1n));
    for(const v of [0n,1n,top-1n,top,u]) {
      await add(`uint${width}-${v}`,{Value:[F('value',`uint${width}`)]},{value:v.toString()});
      await add(`uint${width}-hex-${v}`,{Value:[F('value',`uint${width}`)]},{value:'0x'+v.toString(16)});
    }
    for(const v of [-top,-top+1n,-1n,0n,top-1n])
      await add(`int${width}-${v}`,{Value:[F('value',`int${width}`)]},{value:v.toString()});
    await add(`literal${width}`,{Value:[F('value',`uint${width}`)]},{value:u.toString()},domain,true);
    reject(`uint${width}-overflow`,`uint${width}`,(u+1n).toString());
    reject(`uint${width}-negative`,`uint${width}`,'-1');
    reject(`int${width}-above`,`int${width}`,top.toString());
    reject(`int${width}-below`,`int${width}`,(-top-1n).toString());
  }
  for(let n=1;n<=32;n++) {
    await add(`bytes${n}`,{Value:[F('value',`bytes${n}`)]},{value:'0x'+'81'.repeat(n)});
    reject(`bytes${n}-short`,`bytes${n}`,'0x'+'81'.repeat(n-1));
    reject(`bytes${n}-long`,`bytes${n}`,'0x'+'81'.repeat(n+1));
  }
  for(const [i,text] of ['', 'ASCII', 'العربية', '中文', 'e\u0301', '\u00e9', '🌍', 'a\u202eb', 'a\u200bb', 'a\0b', 'a\nb'].entries())
    await add(`string-${i}`,{Value:[F('value','string')]},{value:text});
  const allDomain={...domain,salt:'0x'+'ab'.repeat(32)};
  for(let mask=0;mask<32;mask++) {
    const d=Object.fromEntries(Object.entries(allDomain).filter((_,i)=>mask&(1<<i)));
    await add(`domain-subset-${mask}`,{Value:[F('value','uint256')]},{value:'123'},d);
  }
  for(const chain of ['1','56','9007199254740991','9007199254740992','9007199254740993','18446744073709551615'])
    await add(`chain-${chain}`,{Value:[F('value','uint256')]},{value:'42'},{...domain,chainId:chain});
  for(let n=0;n<=8;n++) {
    const types={Leaf:[F('amount','uint256'),F('who','address'),F('note','string')],
      Branch:[F('leaves','Leaf[]'),F('grid','int256[2][]'),F('raw','bytes[]'),F('ok','bool')]};
    const message={leaves:Array.from({length:n},(_,i)=>({amount:((1n<<200n)+BigInt(i)).toString(),who:spender,note:'leaf'+i})),
      grid:Array.from({length:n},(_,i)=>['-'+(1n<<255n).toString(),i.toString()]),raw:['0x','0x00','0xabcd'],ok:n%2===0};
    await add(`nested-${n}`,types,message);
  }
  const permit={Permit:[F('owner','address'),F('spender','address'),F('value','uint256'),F('nonce','uint256'),F('deadline','uint256')]};
  const m={owner:wallet.address,spender,value:'123',nonce:'7',deadline:'2000000000'};
  await add('binding-base',permit,m);
  for(const [key,val] of Object.entries({name:'Different',version:'2',chainId:'56',verifyingContract:spender}))
    await add('binding-domain-'+key,permit,m,{...domain,[key]:val});
  for(const [key,val] of Object.entries({spender:contract,value:'124',nonce:'8',deadline:'2000000001'}))
    await add('binding-message-'+key,permit,{...m,[key]:val});
  for(const value of ['0',((1n<<256n)-1n).toString()]) await add('permit-limit-'+value,permit,{...m,value});
  const p2={name:'Permit2',chainId:'1',verifyingContract:'0x000000000022D473030F116dDEE9F6B43aC78BA3'};
  const allowance={PermitDetails:[F('token','address'),F('amount','uint160'),F('expiration','uint48'),F('nonce','uint48')],
    PermitSingle:[F('details','PermitDetails'),F('spender','address'),F('sigDeadline','uint256')]};
  for(const amount of ['0','1',((1n<<160n)-1n).toString()])
    await add('permit2-limit-'+amount,allowance,{details:{token:contract,amount,expiration:'2000000100',nonce:'7'},spender,sigDeadline:'2000000000'},p2);
  fs.writeFileSync(process.argv[2],JSON.stringify({reference:'ethers@'+version,syntheticKey:'32 bytes of 0x01',vectors,invalid},null,2)+'\n');
  console.log(JSON.stringify({vectors:vectors.length,invalid:invalid.length}));
})().catch(e=>{console.error(e);process.exit(1)});
