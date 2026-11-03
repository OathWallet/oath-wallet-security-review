import fs from 'node:fs';
import {createHash,createPublicKey,verify} from 'node:crypto';
const [vectorsPath,resultsPath] = process.argv.slice(2);
const fixture=JSON.parse(fs.readFileSync(vectorsPath)),results=JSON.parse(fs.readFileSync(resultsPath));
const vectors=[...fixture.plans,...fixture.actions];
if(results.length!==82||vectors.length!==82)throw Error('Missing signature cases');
for(let i=0;i<vectors.length;i++) {
 const v=vectors[i],r=results[i],raw=Buffer.from(v.raw,'base64'),bytes=Buffer.from(r.signed,'base64');
 if(r.index!==i||bytes.length!==raw.length+65||!bytes.subarray(0,raw.length).equals(raw)||bytes[raw.length]!==0)throw Error('Changed signed bytes');
 const key=createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),Buffer.from(v.publicKey,'base64')]),format:'der',type:'spki'});
 if(!verify(null,createHash('sha256').update(raw).digest(),key,bytes.subarray(raw.length+1)))throw Error('Invalid application signature');
}
console.log('Independently verified all 82 production WalletConnect signatures over exact SDK bytes.');
