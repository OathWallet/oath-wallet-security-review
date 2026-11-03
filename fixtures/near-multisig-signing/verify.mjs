import fs from 'node:fs';
import {createHash,createPublicKey,verify} from 'node:crypto';
const [fixturePath,resultPath]=process.argv.slice(2),fixture=JSON.parse(fs.readFileSync(fixturePath)),results=JSON.parse(fs.readFileSync(resultPath));
if(fixture.bundles.length!==50||results.length!==50)throw Error('Incomplete bundle results');
let total=0;
for(let i=0;i<50;i++){
 const expected=fixture.bundles[i],actual=results[i];
 if(actual.id!==i||actual.parts.length!==expected.parts.length)throw Error('Missing or reordered bundle');
 for(let j=0;j<expected.parts.length;j++){
  const v=expected.parts[j],raw=Buffer.from(v.raw,'base64'),signed=Buffer.from(actual.parts[j],'base64');
  if(signed.length!==raw.length+65||!signed.subarray(0,raw.length).equals(raw)||signed[raw.length]!==0)throw Error('Changed transaction bytes');
  const key=createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),Buffer.from(v.publicKey,'base64')]),format:'der',type:'spki'});
  if(!verify(null,createHash('sha256').update(raw).digest(),key,signed.subarray(raw.length+1)))throw Error('Invalid production signature');
  total++;
 }
}
if(total!==188)throw Error('Missing signatures');
console.log(`Independently verified ${total} production multisig signatures over exact SDK transaction bytes.`);
