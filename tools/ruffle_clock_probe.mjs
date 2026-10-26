/** Finite audio-clock/visible-frame diagnostic, not a route or score verifier.
 * Unchanged pinned movie. Passive Web Audio constructor wrapper retains actual
 * contexts for reading state/currentTime only; no game variables are accessed.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {chromium} from 'playwright';
const out=path.resolve(process.env.MOTA_CLOCK_PROBE_DIR??'generated/RuffleClockProbe');
const web=path.resolve(process.env.MOTA_RUFFLE_WEB??'generated/private/ruffle-web');
const swf=path.resolve(process.env.MOTA_FLASH_SWF??'generated/private/gdut-v112.swf');
const disabled=process.env.MOTA_CONTROL_DISABLE_AUDIO_OUTPUT==='1';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const movieHash=hash(fs.readFileSync(swf));
if(!['40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896','04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9'].includes(movieHash))throw Error('Unpinned movie');
const release=JSON.parse(fs.readFileSync('experiments/ruffle-release.json'));
for(const [name,meta] of Object.entries(release.files))if(hash(fs.readFileSync(path.join(web,name)))!==meta.sha256)throw Error('Unpinned player');
fs.mkdirSync(out,{recursive:false});
const html=`<!doctype html><body style="margin:0"><script>
window.audioClockContexts=[];
const OriginalAudioContext=window.AudioContext;
window.AudioContext=class extends OriginalAudioContext{constructor(...args){super(...args);window.audioClockContexts.push(this);}};
window.RufflePlayer={config:{publicPath:'/ruffle/',autoplay:'on',unmuteOverlay:'hidden',logLevel:'error',preferredRenderer:'canvas',openUrlMode:'deny',allowNetworking:'internal'}};
</script><script src="/ruffle/ruffle.js"></script><div id="container"></div>`;
const server=http.createServer((req,res)=>{try{
 const url=new URL(req.url,'http://localhost');
 if(url.pathname==='/'){res.setHeader('Content-Type','text/html');res.end(html);return;}
 const file=url.pathname==='/game.swf'?swf:url.pathname.startsWith('/ruffle/')?path.join(web,path.basename(url.pathname)):null;
 if(!file){res.writeHead(404).end();return;}
 res.setHeader('Content-Type',file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(fs.readFileSync(file));
}catch{res.writeHead(404).end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const address=`http://127.0.0.1:${server.address().port}`;
const args=['--autoplay-policy=no-user-gesture-required',...(disabled?['--disable-audio-output']:[])];
let browser,watchdog;const samples=[],errors=[];
try{
 browser=await chromium.launch({headless:true,args,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE});
 watchdog=setTimeout(()=>browser.close(),90000);
 const context=await browser.newContext({viewport:{width:600,height:450}});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
 await page.route('**/*',route=>route.request().url().startsWith(address)?route.continue():route.abort());
 await page.goto(address);
 await page.evaluate(async()=>{const p=window.RufflePlayer.newest().createPlayer();p.style.width='570px';p.style.height='410px';document.querySelector('#container').append(p);await p.ruffle().load('/game.swf');p.ruffle().resume();});
 const began=Date.now();
 for(let i=0;i<=8;i++){
  if(i)await page.waitForTimeout(5000);
  const screenshot=await page.screenshot({path:path.join(out,`sample-${i}.png`)});
  const contexts=await page.evaluate(()=>window.audioClockContexts.map(a=>({state:a.state,currentTime:a.currentTime,sampleRate:a.sampleRate})));
  samples.push({elapsedMilliseconds:Date.now()-began,contexts,screenshotSHA256:hash(screenshot)});
  if(i===4)await page.mouse.click(285,230);
 }
 const first=samples[0],last=samples.at(-1),delta=last.contexts[0]?.currentTime-first.contexts[0]?.currentTime;
 if(!Number.isFinite(delta))throw Error('Actual audio clock unavailable');
 const receipt={schemaVersion:1,scope:'Audio clock and visible frame diagnostic only; no gameplay completion or record verification',originalSWFSHA256:movieHash,player:'Official Ruffle0.7.1 web',browser:browser.version(),browserArguments:args,audioOutputDisabled:disabled,passiveAudioContextConstructorWrapper:true,gameVariableReads:false,gameVariableWrites:false,clockWrites:false,seedControl:false,menuClickAfterSample:4,samples,audioDeltaSeconds:delta,audioClockAdvanced:delta>0.8*(last.elapsedMilliseconds-first.elapsedMilliseconds)/1000,errors};
 fs.writeFileSync(path.join(out,'clock-probe.json'),JSON.stringify(receipt,null,2)+'\n');
 console.log(JSON.stringify({directory:out,audioDeltaSeconds:delta,audioClockAdvanced:receipt.audioClockAdvanced,errors}));
}finally{clearTimeout(watchdog);if(browser)await browser.close();server.close();}
