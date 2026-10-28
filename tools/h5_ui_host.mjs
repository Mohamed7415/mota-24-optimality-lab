/** Normal official H5 page with ordinary inputs and explicit read-only snapshots.
 * No engine function calls, variable writes, loader patches or explicit score API calls.
 * Private screenshots/maps stay in generated/. A snapshot is not visual proof.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const out=path.resolve(process.env.MOTA_H5_HOST_DIR??'generated/H5UIHost');
fs.mkdirSync(out,{recursive:false});
const profile=path.resolve(process.env.MOTA_H5_BROWSER_PROFILE??'generated/private/h5-browser-profile');
const inputs=[],errors=[],networkErrors=[],downloads=[],responseFingerprints=[];
const allowed=new Set(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter','Escape','Space','s','d','j','g','x','r','c','1','2','3','4','5','6']);
let context,page,ready=false,sequence=0,serial=Promise.resolve(),watchdog,pendingFileChooser;
function persist(){fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(inputs,null,2)+'\n');}
async function snapshot(){return page.evaluate(()=>{
 const c=window.core,s=c?.status,h=s?.hero,e=s?.event;
 return {projectVersion:c?.firstData?.version,cacheVersion:window.main?.version,played:s?.played,floorId:s?.floorId,lockControl:s?.lockControl,
 hero:h?{hp:h.hp,atk:h.atk,def:h.def,money:h.money,exp:h.exp,lv:h.lv,loc:h.loc,items:h.items,flags:Object.fromEntries(['开启暴击','战斗动画','回合间隔','限时'].map(k=>[k,h.flags?.[k]??null]))}:null,
 event:e?{id:e.id,type:e.data?.type,selection:e.selection,text:e.ui?.text,choices:e.ui?.choices?.map(x=>typeof x==='string'?x:x.text)}:null,
 replay:s?.replay?{replaying:s.replay.replaying,pausing:s.replay.pausing,speed:s.replay.speed,failed:s.replay.failed,steps:s.replay.steps,remaining:s.replay.toReplay?.length,total:s.replay.totalList?.length}:null,
 map:s?.floorId?s.maps?.[s.floorId]?.map:null,route:s?.route};
});}
async function command(req,res){
 let body='';for await(const part of req){body+=part;if(body.length>8192)throw Error('Oversized request');}
 const data=body?JSON.parse(body):{};let result;
 if(req.url==='/status')result={ready,ordinaryInputs:inputs.length};
 else if(!ready)throw Error('Official game still loading');
 else if(['/start','/load','/replay'].includes(req.url)){
  const selector={'/start':'#playGame','/load':'#loadGame','/replay':'#replayGame'}[req.url];
  if(!await page.locator(selector).isVisible())throw Error('Requested menu button not visible');
  inputs.push({type:'click',selector,at:Date.now()});await page.locator(selector).click();await page.waitForTimeout(500);result=await snapshot();
 }else if(req.url==='/press'){
  const keys=data.keys??[],wait=data.wait??200;
  if(!Array.isArray(keys)||keys.length>100||keys.some(k=>!allowed.has(k))||!Number.isFinite(wait)||wait<0||wait>15000)throw Error('Invalid ordinary key input');
  for(const key of keys){inputs.push({type:'key',key,at:Date.now()});await page.keyboard.press(key);await page.waitForTimeout(100);}
  await page.waitForTimeout(wait);result=await snapshot();
 }else if(req.url==='/upload-replay'){
  const filename=path.resolve(data.path??'');
  if(!filename.startsWith(path.resolve('generated')+path.sep)||!filename.endsWith('.h5route'))throw Error('Only a private generated .h5route replay is accepted');
  const file=page.locator('input[type=file]');
  if(!pendingFileChooser&&await file.count()!==1)throw Error('Open the normal replay file picker first');
  inputs.push({type:'normal-file-picker',path:filename,sha256:crypto.createHash('sha256').update(fs.readFileSync(filename)).digest('hex'),at:Date.now()});
  if(pendingFileChooser){await pendingFileChooser.setFiles(filename);pendingFileChooser=null;}else await file.setInputFiles(filename);
  await page.waitForTimeout(600);result=await snapshot();
 }else if(req.url==='/state')result=await snapshot();
 else if(req.url==='/capture'){
  const name=`frame-${String(sequence++).padStart(5,'0')}.png`;const filename=path.join(out,name);await page.screenshot({path:filename});result={path:filename,state:await snapshot()};
  fs.writeFileSync(path.join(out,name.replace('.png','.json')),JSON.stringify(result.state,null,2)+'\n');
 }else if(req.url==='/close'){
  clearTimeout(watchdog);persist();result={closed:true};await context.close();server.close();
 }else throw Error('Unknown operation');
 persist();res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result));
}
const server=http.createServer((req,res)=>{
 if(req.method!=='POST'){res.writeHead(405);res.end();return;}
 serial=serial.then(()=>command(req,res)).catch(error=>{res.writeHead(400);res.end(JSON.stringify({error:String(error)}));});
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
fs.writeFileSync(path.join(out,'endpoint.json'),JSON.stringify({address:`http://127.0.0.1:${server.address().port}`,gameVariableReads:true,gameVariableWrites:false,maxSessionMinutes:120})+'\n');
try{
 context=await chromium.launchPersistentContext(profile,{headless:true,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE,viewport:{width:1000,height:850},args:['--disable-audio-output','--disable-http2']});
 watchdog=setTimeout(async()=>{persist();await context.close();server.close();},120*60*1000);
 page=context.pages()[0];page.on('filechooser',chooser=>{pendingFileChooser=chooser;});
 page.on('download',async download=>{
  try{const filename=path.basename(download.suggestedFilename());if(!filename.endsWith('.h5route'))throw Error('Unexpected download type');const destination=path.join(out,filename);await download.saveAs(destination);downloads.push({filename,sha256:crypto.createHash('sha256').update(fs.readFileSync(destination)).digest('hex')});fs.writeFileSync(path.join(out,'downloads.json'),JSON.stringify(downloads,null,2)+'\n');}catch(error){errors.push(String(error));}
 });
 page.on('response',async response=>{if(/^https:\/\/h5mota\.com\/games\/24\/(?:main\.js|project\/(?:project|floors)\.min\.js|libs\/libs\.min\.js)(?:\?|$)/.test(response.url())){try{const bytes=await response.body();responseFingerprints.push({url:response.url(),bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});fs.writeFileSync(path.join(out,'response-fingerprints.json'),JSON.stringify(responseFingerprints,null,2)+'\n');}catch(error){errors.push(String(error));}}});
 page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)networkErrors.push({url:r.url(),status:r.status()});});
 await page.goto('https://h5mota.com/games/24/',{waitUntil:'domcontentloaded',timeout:60000});
 await page.locator('#playGame').waitFor({state:'visible',timeout:300000});ready=true;
 fs.writeFileSync(path.join(out,'host.json'),JSON.stringify({url:page.url(),hostSourceSHA256:crypto.createHash('sha256').update(fs.readFileSync(fileURLToPath(import.meta.url))).digest('hex'),browser:context.browser()?.version(),browserArguments:['--disable-audio-output','--disable-http2'],gameVariableReads:true,gameVariableWrites:false,seedControl:false,realClock:true,errors,networkErrors},null,2)+'\n');
 console.log(JSON.stringify({ready}));
}catch(error){clearTimeout(watchdog);if(context)await context.close();server.close();throw error;}
