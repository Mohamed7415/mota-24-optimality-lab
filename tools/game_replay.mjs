/** Whole original movie replay via ordinary DOM input and a read-only parent.
 * Original game bytes are served unchanged. All game functions/UI/audio/timeline
 * run in Ruffle; there is no completion adapter or write to game variables.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {chromium} from 'playwright';
const out=path.resolve(process.env.MOTA_REPLAY_DIR??'generated/M6');
const web=path.resolve(process.env.MOTA_RUFFLE_WEB??'generated/private/ruffle-web');
const swf=path.resolve(process.env.MOTA_FLASH_SWF??'generated/private/mhhf.swf');
const plan=JSON.parse(fs.readFileSync(path.join(out,'game-plan.json')));
const schema=JSON.parse(fs.readFileSync(path.join(out,'observer-schema.json')));
const release=JSON.parse(fs.readFileSync('experiments/ruffle-release.json'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const [name,meta] of Object.entries(release.files))if(hash(fs.readFileSync(path.join(web,name)))!==meta.sha256)throw Error('Unpinned player');
if(hash(fs.readFileSync(swf))!==plan.sourceSWFSHA256)throw Error('Unpinned original');
if(hash(fs.readFileSync(path.join(out,'observer.swf')))!==schema.sha256)throw Error('Observer hash mismatch');
const html=`<!doctype html><body style="margin:0"><script>window.RufflePlayer={config:{publicPath:'/ruffle/',autoplay:'off',unmuteOverlay:'hidden',logLevel:'error',preferredRenderer:'canvas',openUrlMode:'deny',allowNetworking:'internal'}};</script><script src="/ruffle/ruffle.js"></script><div id="container"></div>`;
const server=http.createServer((req,res)=>{try{
 const u=new URL(req.url,'http://localhost');
 if(u.pathname==='/'){res.setHeader('Content-Type','text/html');res.end(html);return;}
 let file;
 if(u.pathname.startsWith('/ruffle/'))file=path.join(web,path.basename(u.pathname));
 else if(u.pathname==='/game.swf')file=swf;
 else if(u.pathname==='/observer.swf')file=path.join(out,'observer.swf');
 else{res.writeHead(404).end();return;}
 res.setHeader('Content-Type',file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(fs.readFileSync(file));
}catch(e){res.writeHead(404).end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const address=`http://127.0.0.1:${server.address().port}`;
const control=process.argv.includes('--control');
let browser,page;const errors=[],inputs=[],checkpoints=[],events=[];
async function state(){return page.evaluate(()=>window.gameState);}
async function wait(test,args={},timeout=15000){await page.waitForFunction(test,args,{timeout});}
async function ready(){await wait(()=>window.gameState?.Now_key_flag===1&&window.gameState.Display_lines===0&&window.gameState.Display_kill===0&&window.gameState.Display_text===0);}
let lastInput=0;
async function input(key){const now=Date.now();inputs.push({type:'key',key,delaySincePreviousInputMs:lastInput?now-lastInput:0});lastInput=now;await page.keyboard.press(key);}
async function point(name){const s=await state();checkpoints.push({name,state:s});return s;}
function pos(s){return s.Now_xid*11+s.Now_yid;}
function resources(s){return {hp:s.Now_hp,atk:s.Now_gong,def:s.Now_fang,keys:[s.Now_yellow,s.Now_blue,s.Now_red],money:s.Now_money,experience:s.Now_mp};}
async function walkStep(target){
 const before=await state();const p=pos(before);const delta=target-p;
 const key={[-1]:'ArrowLeft',[1]:'ArrowRight',[-11]:'ArrowUp',[11]:'ArrowDown'}[delta];
 if(!key)throw Error('Nonadjacent movement');await input(key);
 await wait(({target})=>window.gameState.Now_xid*11+window.gameState.Now_yid===target,{target});await ready();
}
function pathToContact(start,target,grid){
 const queue=[start],prev=new Map([[start,null]]);let end;
 for(let i=0;i<queue.length;i++){
  const p=queue[i],x=p%11,y=Math.floor(p/11);
  const neighbors=[p-11,p+11,p-1,p+1].filter(q=>q>=0&&q<121&&Math.abs(q%11-x)+Math.abs(Math.floor(q/11)-y)===1);
  if(neighbors.includes(target)){end=p;break;}
  for(const q of neighbors)if(!prev.has(q)&&[0,97,98,99].includes(grid[Math.floor(q/11)][q%11])){prev.set(q,p);queue.push(q);}
 }
 if(end===undefined)throw Error('Target unreachable');const result=[];
 while(prev.get(end)!==null){result.push(end);end=prev.get(end);}return result.reverse();
}
try{
 browser=await chromium.launch({headless:true,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE});
 const context=await browser.newContext({viewport:{width:600,height:450}});
 await context.addInitScript(({time})=>{const D=Date;globalThis.Date=class extends D{constructor(...a){super(...(a.length?a:[time]));}static now(){return time;}};},{time:plan.clockMilliseconds});
 page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/*',r=>r.request().url().startsWith(address)?r.continue():r.abort());await page.goto(address);
 if(control){
  const reference=JSON.parse(fs.readFileSync(path.join(out,'native-replay.json')));
  await page.evaluate(async()=>{window.p=window.RufflePlayer.newest().createPlayer();p.style.width='570px';p.style.height='410px';document.querySelector('#container').append(p);await p.ruffle().load('/game.swf');p.ruffle().resume();});
  const initialMenuWaitMilliseconds=Math.max(18000,(reference.menuWaitMilliseconds??15000)+5000);
  await page.waitForTimeout(initialMenuWaitMilliseconds);
  for(const command of reference.inputs){
   if(command.delaySincePreviousInputMs)await page.waitForTimeout(Math.max(100,command.delaySincePreviousInputMs)+100);
   if(command.type==='click')await page.mouse.click(command.x,command.y);else await page.keyboard.press(command.key);
  }
  await page.waitForTimeout(1000);await page.screenshot({path:path.join(out,`control-${plan.extension?'final':'MT2'}.png`)});
  fs.writeFileSync(path.join(out,'control-replay.json'),JSON.stringify({schemaVersion:1,originalSWFSHA256:plan.sourceSWFSHA256,observerLoaded:false,gameVariableReads:false,gameVariableWrites:false,clockMilliseconds:plan.clockMilliseconds,browser:browser.version(),inputCount:reference.inputs.length,initialMenuWaitMilliseconds,settlePolicy:'same input order; each recorded nonzero gap padded to max(100ms,gap)+100ms',inputSequenceSHA256:hash(JSON.stringify(reference.inputs.map(({type,key,x,y})=>({type,key,x,y})))),errors},null,2)+'\n');
  console.log(JSON.stringify({control:true,inputCount:reference.inputs.length,errors}));
 }else{
 await page.evaluate(async fields=>{
  window.traces=[];window.p=window.RufflePlayer.newest().createPlayer();p.style.width='570px';p.style.height='410px';document.querySelector('#container').append(p);
  await p.ruffle().load('/observer.swf');p.ruffle().traceObserver=m=>{
   if(!m.startsWith('GAME|'))return;window.traces.push(m);const values=m.split('|').slice(1);
   window.gameState=Object.fromEntries(fields.map((k,i)=>[k,values[i]==='undefined'?null:values[i]==='true'?true:values[i]==='false'?false:values[i].includes(',')?values[i].split(',').map(Number):Number(values[i])]));
  };p.ruffle().resume();
 },schema.fields);
 const menuWaitStart=Date.now();await wait(()=>window.gameState?._currentframe===1449,{},60000);const menuWaitMilliseconds=Date.now()-menuWaitStart;await point('menu');
 inputs.push({type:'click',x:285,y:230,delaySincePreviousInputMs:0});lastInput=Date.now();await page.mouse.click(285,230);
 await wait(()=>window.gameState._currentframe>1449);await page.waitForTimeout(300);await input('Space');
 await ready();await point('native-MT0-start');
 await input('ArrowUp');await wait(()=>window.gameState.Display_say?.[0]===1&&window.gameState['mtsay_001._currentframe']===1);
 for(let frame=2;frame<=32;frame++){
  await input('Space');
  await wait(({frame})=>window.gameState['mtsay_001._currentframe']===frame||window.gameState.Now_yellow===1,{frame});
 }
 await ready();const opening=await point('opening-reward');
 if(JSON.stringify(resources(opening).keys)!=='[1,1,1]')throw Error('Opening reward mismatch');
 for(let i=0;i<12;i++){
  const s=await state();if(s.Now_line===1)break;
  const previous=JSON.stringify([s.Now_xid,s.Now_yid,s.Now_yellow,s.Now_line]);await input('ArrowUp');
  await wait(({previous})=>JSON.stringify([window.gameState.Now_xid,window.gameState.Now_yid,window.gameState.Now_yellow,window.gameState.Now_line])!==previous,{previous});await ready();
 }
 const arrival=await point('natural-MT1-arrival');
 if(arrival.Now_line!==1||pos(arrival)!==104||JSON.stringify(resources(arrival))!==JSON.stringify({hp:1000,atk:10,def:10,keys:[0,1,1],money:0,experience:0}))throw Error('Natural arrival mismatch');
 const grid=structuredClone(plan.grid);
 for(const action of plan.seedSearch.route){
  const [x,y]=action.position,target=y*11+x;
  for(const step of pathToContact(pos(await state()),target,grid))await walkStep(step);
  const before=await state(),delta=target-pos(before),key={[-1]:'ArrowLeft',[1]:'ArrowRight',[-11]:'ArrowUp',[11]:'ArrowDown'}[delta];
  await input(key);
  await wait(({expected})=>JSON.stringify({hp:window.gameState.Now_hp,atk:window.gameState.Now_gong,def:window.gameState.Now_fang,keys:[window.gameState.Now_yellow,window.gameState.Now_blue,window.gameState.Now_red],money:window.gameState.Now_money,experience:window.gameState.Now_mp})===JSON.stringify(expected),{expected:action.resourcesAfter},20000);
  await ready();grid[y][x]=0;events.push({position:[x,y],originalTile:action.originalTile,resources:resources(await state())});
 }
 const exit=grid.flat().indexOf(13);
 for(const step of pathToContact(pos(await state()),exit,grid))await walkStep(step);
 const delta=exit-pos(await state());await input({[-1]:'ArrowLeft',[1]:'ArrowRight',[-11]:'ArrowUp',[11]:'ArrowDown'}[delta]);
 await wait(()=>window.gameState.Now_line===2);await ready();await point('native-MT2-arrival');
 if(plan.extension){
  const maps=structuredClone(plan.extension.grids);
  async function expectResources(expected){await wait(({expected})=>JSON.stringify({hp:window.gameState.Now_hp,atk:window.gameState.Now_gong,def:window.gameState.Now_fang,keys:[window.gameState.Now_yellow,window.gameState.Now_blue,window.gameState.Now_red],money:window.gameState.Now_money,experience:window.gameState.Now_mp})===JSON.stringify(expected),{expected},20000);}
  for(const action of plan.extension.actions){
   const current=await state();if(current.Now_line!==action.floor)throw Error('Extension floor mismatch');
   const [x,y]=action.position,target=y*11+x,map=maps[String(action.floor)];
   for(const step of pathToContact(pos(await state()),target,map))await walkStep(step);
   const delta=target-pos(await state());await input({[-1]:'ArrowLeft',[1]:'ArrowRight',[-11]:'ArrowUp',[11]:'ArrowDown'}[delta]);
   if(action.kind==='floor'){
    await wait(({to})=>window.gameState.Now_line===to,{to:action.toFloor});await ready();await expectResources(action.resourcesAfter);
   }else if(action.kind==='shop'){
    await wait(()=>window.gameState.Display_buy===1);await input('Space');
    await wait(()=>window.gameState['mt_buy_list.now_case_id']===1&&window.gameState['mt_buy_list._currentframe']===2);
    await input('Space');await expectResources(action.resourcesAfter);await point('M7-shop-purchase');
    for(let choice=2;choice<=4;choice++){await input('ArrowDown');await wait(({choice})=>window.gameState['mt_buy_list.now_case_id']===choice,{choice});}
    await input('Space');await ready();
   }else{
    await expectResources(action.resourcesAfter);await ready();map[y][x]=0;
   }
   events.push({phase:'M7',kind:action.kind,floor:action.floor,position:[x,y],originalTile:action.originalTile,resources:resources(await state())});
   if(action.kind==='floor')await point('M7-floor-'+action.toFloor+'-visit-'+checkpoints.length);
  }
  await point('M7-final-return-MT1');
 }
 await page.screenshot({path:path.join(out,`native-${plan.extension?'final':'MT2'}.png`)});
 const traces=await page.evaluate(()=>window.traces);
 const result={schemaVersion:1,originalSWFSHA256:plan.sourceSWFSHA256,observerSHA256:schema.sha256,player:'Ruffle 0.7.1 official web',browser:browser.version(),clockMilliseconds:plan.clockMilliseconds,menuWaitMilliseconds,inputs,checkpoints,events,traceRecords:traces.length,errors};
 fs.writeFileSync(path.join(out,'native-replay.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(out,'native-traces.json'),JSON.stringify(traces)+'\n');
 console.log(JSON.stringify({complete:true,final:resources(await state()),inputCount:inputs.length,eventCount:events.length,errors}));
 }
}catch(e){
 if(page&&!control){fs.writeFileSync(path.join(out,'native-failure.json'),JSON.stringify({error:String(e),state:await state(),inputs,checkpoints,events,traces:await page.evaluate(()=>window.traces),errors},null,2));await page.screenshot({path:path.join(out,'native-failure.png')});}throw e;
}finally{if(browser)await browser.close();server.close();}
