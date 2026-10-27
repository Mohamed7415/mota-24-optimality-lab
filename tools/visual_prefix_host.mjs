/** Bounded screenshot/ordinary-input host for the experimental visual prefix.
 * Direct unchanged original movie, no SWF observer or game-variable access.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {chromium} from 'playwright';
const out=path.resolve(process.env.MOTA_VISUAL_HOST_DIR??'generated/VisualPrefixHost');
const swf=path.resolve(process.env.MOTA_FLASH_SWF??'generated/private/gdut.swf');
const web=path.resolve(process.env.MOTA_RUFFLE_WEB??'generated/private/ruffle-web');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const originalHash=hash(fs.readFileSync(swf));
if(originalHash!=='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896')throw Error('Visual pilot currently supports the pinned2018 archive only');
const release=JSON.parse(fs.readFileSync('experiments/ruffle-release.json'));
for(const [name,meta] of Object.entries(release.files))if(hash(fs.readFileSync(path.join(web,name)))!==meta.sha256)throw Error('Unpinned player');
fs.mkdirSync(out,{recursive:false});
const args=['--disable-audio-output'];
const html=`<!doctype html><body style="margin:0"><script>window.RufflePlayer={config:{publicPath:'/ruffle/',autoplay:'on',unmuteOverlay:'hidden',logLevel:'error',preferredRenderer:'canvas',openUrlMode:'deny',allowNetworking:'internal'}};</script><script src="/ruffle/ruffle.js"></script><div id="container"></div>`;
let browser,page,ready=false,serial=Promise.resolve(),captureId=0,watchdog;
const inputs=[],errors=[],allowed=new Set(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','2','8']);
function persist(){fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(inputs)+'\n');}
async function command(req,res){
 let body='';for await(const c of req){body+=c;if(body.length>8192)throw Error('Oversized command');}
 const a=body?JSON.parse(body):{};let result;
 if(req.url==='/status')result={ready,inputCount:inputs.length};
 else{
  if(!ready)throw Error('Host initializing');
  if(req.url==='/press'){
   const keys=a.keys??[],gap=a.gap??80,wait=a.wait??180;
   if(!Array.isArray(keys)||keys.length>200||keys.some(k=>!allowed.has(k))||!Number.isFinite(gap)||gap<25||gap>2000||!Number.isFinite(wait)||wait<0||wait>10000)throw Error('Invalid input request');
   for(const key of keys){inputs.push({type:'key',key,unixMilliseconds:Date.now()});await page.keyboard.press(key);await page.waitForTimeout(gap);}
   await page.waitForTimeout(wait);result={sent:keys.length};
  }else if(req.url==='/start'){
   inputs.push({type:'click',x:285,y:230,unixMilliseconds:Date.now()});await page.mouse.click(285,230);await page.waitForTimeout(500);result={clicked:true};
  }else if(req.url==='/capture'){
   const file=path.join(out,`frame-${String(captureId++).padStart(5,'0')}.png`);await page.screenshot({path:file});result={path:file,inputCount:inputs.length};
  }else if(req.url==='/close'){
   clearTimeout(watchdog);persist();await browser.close();server.close();result={closed:true};
  }else throw Error('Unknown operation');
 }
 persist();res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result));
}
const server=http.createServer((req,res)=>{
 if(req.method==='POST'){serial=serial.then(()=>command(req,res)).catch(e=>{res.writeHead(400);res.end(JSON.stringify({error:String(e)}));});return;}
 try{
  const u=new URL(req.url,'http://localhost');if(u.pathname==='/'){res.setHeader('Content-Type','text/html');res.end(html);return;}
  const file=u.pathname==='/game.swf'?swf:u.pathname.startsWith('/ruffle/')?path.join(web,path.basename(u.pathname)):null;
  if(!file){res.writeHead(404).end();return;}
  res.setHeader('Content-Type',file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(fs.readFileSync(file));
 }catch{res.writeHead(404).end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const address=`http://127.0.0.1:${server.address().port}`;
fs.writeFileSync(path.join(out,'endpoint.json'),JSON.stringify({address,maxSessionMinutes:60,observerLoaded:false,gameVariableReads:false,gameVariableWrites:false})+'\n');
try{
 browser=await chromium.launch({headless:true,args,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE});
 watchdog=setTimeout(async()=>{persist();await browser.close();server.close();},60*60*1000);
 const context=await browser.newContext({viewport:{width:600,height:450}});page=await context.newPage();
 page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/*',r=>r.request().url().startsWith(address)?r.continue():r.abort());await page.goto(address);
 await page.evaluate(async()=>{const p=window.RufflePlayer.newest().createPlayer();p.style.width='570px';p.style.height='410px';document.querySelector('#container').append(p);await p.ruffle().load('/game.swf');p.ruffle().resume();});
 fs.writeFileSync(path.join(out,'host.json'),JSON.stringify({originalSWFSHA256:originalHash,player:'Official Ruffle0.7.1 web',browser:browser.version(),browserArguments:args,autoplay:'on',audioOutputDisabled:true,observerLoaded:false,gameVariableReads:false,gameVariableWrites:false,realClock:true,seedControl:false,errors},null,2)+'\n');
 ready=true;console.log(JSON.stringify({ready,address}));
}catch(e){clearTimeout(watchdog);if(browser)await browser.close();server.close();throw e;}
