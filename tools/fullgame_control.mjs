/** Direct top-level original SWF control: timed ordinary input, no game reads.
 * A screenshot is evidence to inspect, not an automatic completion predicate.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {chromium} from 'playwright';
const reference=path.resolve(process.env.MOTA_REFERENCE_DIR??'generated/GdutNativeHP28554');
const out=path.resolve(process.env.MOTA_CONTROL_DIR??'generated/GdutObserverFreeHP28554');
const swf=path.resolve(process.env.MOTA_FLASH_SWF??'generated/private/gdut-v112.swf');
const web=path.resolve(process.env.MOTA_RUFFLE_WEB??'generated/private/ruffle-web');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=fs.readFileSync(path.join(reference,'fullroute-native.json'));
const native=JSON.parse(raw),release=JSON.parse(fs.readFileSync('experiments/ruffle-release.json'));
const inputLimit=Number(process.env.MOTA_CONTROL_INPUT_LIMIT??native.inputs.length);
const minimumGap=Number(process.env.MOTA_CONTROL_MIN_GAP_MS??0);
const longGapPadding=Number(process.env.MOTA_CONTROL_LONG_GAP_PADDING_MS??0);
const endingWait=Number(process.env.MOTA_CONTROL_END_WAIT_MS??12000);
const disableAudioOutput=process.env.MOTA_CONTROL_DISABLE_AUDIO_OUTPUT==='1';
const browserArguments=disableAudioOutput?['--disable-audio-output']:[];
if(!Number.isFinite(endingWait)||endingWait<0||endingWait>120000)throw Error('Invalid ending wait');
if(!Number.isInteger(inputLimit)||inputLimit<1||inputLimit>native.inputs.length||!Number.isFinite(minimumGap)||minimumGap<0||!Number.isFinite(longGapPadding)||longGapPadding<0)throw Error('Invalid control bounds');
const selectedInputs=native.inputs.slice(0,inputLimit);
if(!native.complete24Floors||!native.realClock||native.seedControl||native.gameVariableWrites||native.errors.length)throw Error('Reference does not meet control preconditions');
if(hash(fs.readFileSync(swf))!==native.originalSWFSHA256)throw Error('Reference/file mismatch');
if(!['04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9','40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896'].includes(native.originalSWFSHA256))throw Error('Unpinned original');
for(const [name,meta] of Object.entries(release.files))if(hash(fs.readFileSync(path.join(web,name)))!==meta.sha256)throw Error('Unpinned player');
for(const i of native.inputs)if(i.type!=='click'&&(i.type!=='key'||!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','j','2','8'].includes(i.key)))throw Error('Unreviewed input');
fs.mkdirSync(out,{recursive:false});
const html=`<!doctype html><body style="margin:0"><script>window.RufflePlayer={config:{publicPath:'/ruffle/',autoplay:'off',unmuteOverlay:'hidden',logLevel:'error',preferredRenderer:'canvas',openUrlMode:'deny',allowNetworking:'internal'}};</script><script src="/ruffle/ruffle.js"></script><div id="container"></div>`;
const server=http.createServer((req,res)=>{try{
 const u=new URL(req.url,'http://localhost');if(u.pathname==='/'){res.setHeader('Content-Type','text/html');res.end(html);return;}
 const file=u.pathname.startsWith('/ruffle/')?path.join(web,path.basename(u.pathname)):u.pathname==='/game.swf'?swf:null;
 if(!file){res.writeHead(404).end();return;}res.setHeader('Content-Type',file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(fs.readFileSync(file));
}catch(e){res.writeHead(404).end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const address=`http://127.0.0.1:${server.address().port}`;
let browser,page;const errors=[],commands=[];let began;
try{
 browser=await chromium.launch({headless:true,args:browserArguments,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE});
 const context=await browser.newContext({viewport:{width:600,height:450}});page=await context.newPage();
 page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/*',r=>r.request().url().startsWith(address)?r.continue():r.abort());await page.goto(address);
 await page.evaluate(async()=>{const p=window.RufflePlayer.newest().createPlayer();p.style.width='570px';p.style.height='410px';document.querySelector('#container').append(p);await p.ruffle().load('/game.swf');p.ruffle().resume();});
 await page.waitForTimeout(18000);await page.screenshot({path:path.join(out,'menu.png')});
 began=Date.now();let cumulativeGap=0;
 for(const [index,command] of selectedInputs.entries()){
  const gap=command.delaySincePreviousInputMs;
  cumulativeGap+=index?Math.max(minimumGap,gap)+(gap>=300?longGapPadding:0):gap;
  const remaining=began+cumulativeGap-Date.now();if(remaining>0)await page.waitForTimeout(remaining);
  if(index===selectedInputs.length-1){await page.screenshot({path:path.join(out,'before-last-input.png')});}
  commands.push({index,atMilliseconds:Date.now()-began,command});
  if(command.type==='click')await page.mouse.click(command.x,command.y);else await page.keyboard.press(command.key);
  if(index%1000===0){fs.writeFileSync(path.join(out,'progress.json'),JSON.stringify({index,total:native.inputs.length,elapsedMilliseconds:Date.now()-began}));console.log(JSON.stringify({index,total:native.inputs.length,elapsedMilliseconds:Date.now()-began}));}
 }
 await page.waitForTimeout(endingWait);await page.screenshot({path:path.join(out,'after-ending.png')});
 const receipt={schemaVersion:1,scope:'Observer-free timed input control. Screenshots require independent visual inspection; no automatic completion or score claim.',originalSWFSHA256:native.originalSWFSHA256,referenceNativeSHA256:hash(raw),referenceProposalSHA256:native.proposalSHA256,observerLoaded:false,gameVariableReads:false,gameVariableWrites:false,realClock:true,seedControl:false,inputOrderPreserved:true,inputCount:commands.length,referenceInputCount:native.inputs.length,fullInputSequenceExecuted:commands.length===native.inputs.length,minimumGapMilliseconds:minimumGap,longGapPaddingMilliseconds:longGapPadding,inputSequenceSHA256:hash(JSON.stringify(selectedInputs.map(({type,key,x,y})=>({type,key,x,y})))),timingPolicy:'Ordinary DOM input in recorded order, absolute targets from cumulative recorded gaps, optional declared minimum/padding, unmodified real clock; awaited browser commands can delay targets.',initialMenuWaitMilliseconds:18000,endingObservationWaitMilliseconds:endingWait,elapsedMilliseconds:Date.now()-began,browser:browser.version(),player:'Ruffle0.7.1 official web',errors,complete24Floors:false,recordBreakingRoute:false,visualReviewPending:true};
 receipt.browserArguments=browserArguments;
 receipt.audioOutputDisabled=disableAudioOutput;
 fs.writeFileSync(path.join(out,'control-replay.json'),JSON.stringify(receipt,null,2)+'\n');fs.writeFileSync(path.join(out,'executed-inputs.json'),JSON.stringify(commands)+'\n');console.log(JSON.stringify(receipt));
}catch(e){if(page)await page.screenshot({path:path.join(out,'control-failure.png')});fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:String(e),executedInputCount:commands.length,errors}));throw e;}
finally{if(browser)await browser.close();server.close();}
