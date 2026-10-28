/** Data-only packaging of our observed native route. No game functions run.
 * Parenthesized literal entries are supported by the pinned native decodeRoute.
 * The natural seed is copied unchanged from our independently verified prefix.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import LZString from 'lz-string';
const args=Object.fromEntries(process.argv.slice(2).reduce((rows,arg,i,all)=>i%2===0?[...rows,[arg,all[i+1]]]:rows,[]));
for(const k of ['--prefix-replay','--prefix-state','--snapshot','--out'])if(!args[k])throw Error(`Missing ${k}`);
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const prefixBytes=fs.readFileSync(args['--prefix-replay']);
const metadata=JSON.parse(LZString.decompressFromBase64(prefixBytes.toString()));
if(metadata.name!=='24'||!Number.isSafeInteger(metadata.seed)||typeof metadata.hard!=='string')throw Error('Unexpected own-prefix metadata');
const prior=JSON.parse(fs.readFileSync(args['--prefix-state']));
const prefix=prior.finalState?.route;
const snapshotBytes=fs.readFileSync(args['--snapshot']);
const snapshot=JSON.parse(snapshotBytes),state=snapshot.state??snapshot,route=state.route;
if(!Array.isArray(route)||!Array.isArray(prefix)||!prefix.length||route.length<prefix.length)throw Error('Missing observed native routes');
if(!prefix.every((entry,i)=>entry===route[i]))throw Error('Full route does not extend the independently replayed prefix');
if(route.some(entry=>typeof entry!=='string'||/[()\r\n\0]/.test(entry)))throw Error('Literal route entry cannot be represented safely');
const encoded=route.map(entry=>`(${entry})`).join('');
const tape=LZString.compressToBase64(JSON.stringify({...metadata,route:encoded}));
const out=path.resolve(args['--out']);if(fs.existsSync(out))throw Error('Output already exists');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'own-full-route.h5route'),tape);
fs.writeFileSync(path.join(out,'packaging-receipt.json'),JSON.stringify({schemaVersion:1,scope:'Data-only repack of our observed native H5 inputs, not a normal full-tape menu export; requires fresh native replay.',ownPrefixReplaySHA256:hash(prefixBytes),ownSnapshotSHA256:hash(snapshotBytes),ownSnapshotFloor:state.floorId,prefixEntriesMatched:prefix.length,nativeRouteEntries:route.length,nativeRouteSHA256:hash(JSON.stringify(route)),replaySHA256:hash(tape),replayBytes:Buffer.byteLength(tape),naturalSeedCopiedUnchanged:true,seed:metadata.seed,gameVariableWrites:false,gameFunctionsCalled:false,complete24FloorsIndependentlyVerified:false,recordBreakingRoute:false},null,2)+'\n');
console.log(JSON.stringify({nativeRouteEntries:route.length,matchedPrefixEntries:prefix.length,replaySHA256:hash(tape),out}));
