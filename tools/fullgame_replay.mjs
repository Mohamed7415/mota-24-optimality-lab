/** Whole original movie replay via ordinary DOM input and a read-only parent.
 * Original game bytes are served unchanged. All game functions/UI/audio/timeline
 * run in Ruffle; there is no completion adapter or write to game variables.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {chromium} from 'playwright';
const out=path.resolve(process.env.MOTA_REPLAY_DIR??'generated/FullRoute');
const web=path.resolve(process.env.MOTA_RUFFLE_WEB??'generated/private/ruffle-web');
const swf=path.resolve(process.env.MOTA_FLASH_SWF??'generated/private/mhhf.swf');
const proposalBytes=fs.readFileSync(path.join(out,'proposal.json'));
const plan=JSON.parse(proposalBytes);
fs.writeFileSync(path.join(out,'executed-proposal-'+crypto.createHash('sha256').update(proposalBytes).digest('hex')+'.json'),proposalBytes);
const schema=JSON.parse(fs.readFileSync(path.join(out,'observer-schema.json')));
const release=JSON.parse(fs.readFileSync('experiments/ruffle-release.json'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const [name,meta] of Object.entries(release.files))if(hash(fs.readFileSync(path.join(web,name)))!==meta.sha256)throw Error('Unpinned player');
if(hash(fs.readFileSync(swf))!=='04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9')throw Error('Unpinned original');
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
let browser,page;const inputs=[],checkpoints=[],events=[],errors=[];let lastInput=0,startClickUnixMs;
const dialogs=[1,2,3,4,6,7,8].map(i=>`mtsay_00${i}._currentframe`);
function resources(s){return {hp:s.Now_hp,atk:s.Now_gong,def:s.Now_fang,level:s.Now_life,keys:[s.Now_yellow,s.Now_blue,s.Now_red],money:s.Now_money,experience:s.Now_mp};}
function finished24(s){return s.Now_line===26&&s.Now_hp>0&&s._currentframe>=4348&&s['visibleMap.3']?.[5]===0;}
function idle(s){return s.Now_key_flag===1&&s.Display_lines===0&&s.Display_kill===0&&s.Display_text===0&&s.Display_other===0&&(s.Display_buy===0||s['mt_buy_list._currentframe']==null)&&!dialogs.some(k=>s[k]!=null);}
async function state(){return page.evaluate(()=>window.gameState);}
async function wait(fn,args={},timeout=20000){await page.waitForFunction(fn,args,{timeout});}
async function input(key){const now=Date.now();inputs.push({type:'key',key,delaySincePreviousInputMs:lastInput?now-lastInput:0});lastInput=now;await page.keyboard.press(key);}
function signature(s){return JSON.stringify(s);}
async function change(before){await wait(({before})=>JSON.stringify(window.gameState)!==before,{before:signature(before)});}
async function settle(action){
 let purchased=false;
 // Long zero-damage bosses can legitimately take hundreds of attacks. Keep
 // the bound proportional to the worst-support proposal rather than time out
 // a valid battle after the short UI-only allowance.
 const budget=Math.max(2000,40*(action?.randomDraws?.length??0)+500);
 for(let count=0;count<budget;count++){
  const s=await state();if(finished24(s)||idle(s))return;
  if(s.Now_hp!=null&&s.Now_hp<=0)throw Error('Native hero died');
  if(s.Display_kill===1||s.Display_lines!==0||s.Display_text!==0||s.Open_room===1){await change(s);continue;}
  if(dialogs.some(k=>s[k]!=null)){await input('Space');await change(s);continue;}
  if(s.Display_other===1){await input('Space');await change(s);continue;}
  if(s.Display_buy===1&&s['mt_buy_list._currentframe']!=null){
   if(action?.kind!=='shop')throw Error('Unexpected shop');
   if(s['mt_buy_list._currentframe']===1){await input('Space');await change(s);continue;}
   const target=purchased?4:action.choice;
   if(s['mt_buy_list.now_case_id']!==target){const next=s['mt_buy_list.now_case_id']%4+1;await input('ArrowDown');await wait(({next})=>window.gameState['mt_buy_list.now_case_id']===next,{next});continue;}
   const old=JSON.stringify([s.Now_hp,s.Now_gong,s.Now_fang,s.Now_life,s.Now_yellow,s.Now_blue,s.Now_red,s.Now_money,s.Now_mp]);
   await input('Space');
   if(target===4)await wait(()=>window.gameState.Display_buy===0||window.gameState.Display_buy===2);
   else await wait(({old})=>{const s=window.gameState;return JSON.stringify([s.Now_hp,s.Now_gong,s.Now_fang,s.Now_life,s.Now_yellow,s.Now_blue,s.Now_red,s.Now_money,s.Now_mp])!==old;},{old});
   purchased=true;continue;
  }
  await change(s);
 }
 throw Error('UI settlement limit');
}
function pos(s){return s.Now_xid*11+s.Now_yid;}
function pathToContact(s,target){
 const grid=Array.from({length:11},(_,i)=>s['visibleMap.'+i]);
 const start=pos(s),q=[start],prev=new Map([[start,null]]);let end;
 for(const p of q){
  const ns=[p-11,p+11,p-1,p+1].filter(n=>n>=0&&n<121&&Math.abs(n%11-p%11)+Math.abs(Math.floor(n/11)-Math.floor(p/11))===1);
  if(ns.includes(target)){end=p;break;}
  for(const n of ns)if(!prev.has(n)&&[0,97,98,99].includes(grid[Math.floor(n/11)][n%11])){prev.set(n,p);q.push(n);}
 }
 if(end===undefined)throw Error('No native visible-map path');const path=[];
 while(prev.get(end)!==null){path.push(end);end=prev.get(end);}return path.reverse();
}
async function walk(target){
 const before=await state(),delta=target-pos(before);await input({[-1]:'ArrowLeft',[1]:'ArrowRight',[-11]:'ArrowUp',[11]:'ArrowDown'}[delta]);
 await wait(({target})=>window.gameState.Now_xid*11+window.gameState.Now_yid===target,{target});await settle();
}
try{
 browser=await chromium.launch({headless:true,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE});
 const context=await browser.newContext({viewport:{width:600,height:450}});
 // Use the real clock and native RNG. Worst-support proposals require no seed control.
 page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/*',r=>r.request().url().startsWith(address)?r.continue():r.abort());await page.goto(address);
 await page.evaluate(async fields=>{
  window.traces=[];window.lastTrace=null;window.p=window.RufflePlayer.newest().createPlayer();p.style.width='570px';p.style.height='410px';document.querySelector('#container').append(p);
  await p.ruffle().load('/observer.swf');p.ruffle().traceObserver=m=>{
   if(!m.startsWith('GAME|')||window.lastTrace===m)return;window.lastTrace=m;window.traces.push(m);
   const vs=m.split('|').slice(1);window.gameState=Object.fromEntries(fields.map((k,i)=>[k,vs[i]==='undefined'?null:vs[i]==='true'?true:vs[i]==='false'?false:vs[i].includes(',')?vs[i].split(',').map(Number):Number(vs[i])]));
  };p.ruffle().resume();
 },schema.fields);
 await wait(()=>window.gameState?._currentframe===1449,{},60000);startClickUnixMs=lastInput=Date.now();inputs.push({type:'click',x:285,y:230,delaySincePreviousInputMs:0});await page.mouse.click(285,230);
 await wait(()=>window.gameState._currentframe>1449);await page.waitForTimeout(300);await input('Space');await settle();
 await input('ArrowUp');await wait(()=>window.gameState.Display_say?.[0]===1);await settle();
 for(let n=0;n<15;n++){
  const before=await state();if(before.Now_line===1)break;await input('ArrowUp');await change(before);await settle();
 }
 const opening=await state();if(opening.Now_line!==1||JSON.stringify(resources(opening))!==JSON.stringify({hp:1000,atk:10,def:10,level:1,keys:[0,1,1],money:0,experience:0}))throw Error('Natural opening mismatch');
 checkpoints.push({name:'natural-MT1',state:opening});
 for(const [index,a] of plan.actions.entries()){
  let before=await state();if(before.Now_line!==a.floor)throw Error(`Floor mismatch at${index}`);
  const [x,y]=a.position,target=y*11+x;
  for(const p of pathToContact(before,target))await walk(p);
  before=await state();const tile=before['visibleMap.'+y][x];
  if(a.originalTile!==undefined&&tile!==a.originalTile)throw Error(`Tile mismatch${index}: ${tile} vs${a.originalTile}`);
  const delta=target-pos(before);await input({[-1]:'ArrowLeft',[1]:'ArrowRight',[-11]:'ArrowUp',[11]:'ArrowDown'}[delta]);await change(before);
  await settle(a);const after=await state(),actual=resources(after),expected=a.resourcesAfter;
  if(a.kind==='floor'&&after.Now_line!==a.toFloor)throw Error(`Stair mismatch${index}`);
  if(actual.hp<expected.hp||Object.keys(expected).some(k=>k!=='hp'&&JSON.stringify(actual[k])!==JSON.stringify(expected[k])))throw Error(`Resources mismatch${index}: ${JSON.stringify(actual)} vs${JSON.stringify(expected)}`);
  events.push({index,kind:a.kind,floor:a.floor,position:a.position,originalTile:a.originalTile,before:resources(before),after:actual});
  if(a.kind==='dialogue'||a.kind==='shop'||a.kind==='floor')checkpoints.push({name:`action-${index}`,state:after});
  if(index%25===0)console.log(JSON.stringify({index,total:plan.actions.length,floor:after.Now_line,actual}));
 }
 const final=await state();await page.screenshot({path:path.join(out,'fullroute-native.png')});
 const endObservationUnixMs=Date.now();
 const result={schemaVersion:1,scope:'Native route replay; record comparison and recognition are separate',complete24Floors:finished24(final),recordBreakingRoute:false,originalSWFSHA256:hash(fs.readFileSync(swf)),observerSHA256:schema.sha256,proposalSHA256:hash(proposalBytes),realClock:true,seedControl:false,gameVariableWrites:false,wallClock:{startClickUnixMs,endObservationUnixMs,elapsedMilliseconds:endObservationUnixMs-startClickUnixMs,scope:'Menu start click to final observed state and screenshot; automation elapsed time, not a reviewed human speedrun timing rule'},player:'Ruffle0.7.1 official web',inputs,events,checkpoints,final,errors};
 fs.writeFileSync(path.join(out,'fullroute-native.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(out,'fullroute-traces.json'),JSON.stringify(await page.evaluate(()=>window.traces))+'\n');console.log(JSON.stringify({done:true,actions:events.length,inputs:inputs.length,final:resources(final),floor:final.Now_line,errors}));
}catch(e){if(page){fs.writeFileSync(path.join(out,'fullroute-failure.json'),JSON.stringify({error:String(e),state:await state(),events,inputs,checkpoints,traces:await page.evaluate(()=>window.traces)},null,2));await page.screenshot({path:path.join(out,'fullroute-failure.png')});}throw e;}
finally{if(browser)await browser.close();server.close();}
