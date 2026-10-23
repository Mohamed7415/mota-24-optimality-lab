/** Compare visible resource digits in wrapped and observer-free movie runs.
 * Pixels stay local; public evidence contains only region hashes and equality.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium} from 'playwright';
const out=path.resolve(process.env.MOTA_REPLAY_DIR??'generated/M6');
const suffix=JSON.parse(fs.readFileSync(path.join(out,'game-plan.json'))).extension?'final':'MT2';
const regions={level:[95,43,42,38],stats:[81,84,67,117],keys:[100,214,35,96],floor:[45,316,90,25]};
const browser=await chromium.launch({headless:true,executablePath:process.env.MOTA_CHROMIUM_EXECUTABLE});
try{
 const page=await browser.newPage();
 const samples=await page.evaluate(async({a,b,regions})=>{
  async function decode(base64){const image=new Image();image.src='data:image/png;base64,'+base64;await image.decode();const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);return ctx;}
  const ca=await decode(a),cb=await decode(b);
  return Object.entries(regions).map(([name,box])=>({name,box,a:Array.from(ca.getImageData(...box).data),b:Array.from(cb.getImageData(...box).data)}));
 },{a:fs.readFileSync(path.join(out,`native-${suffix}.png`)).toString('base64'),b:fs.readFileSync(path.join(out,`control-${suffix}.png`)).toString('base64'),regions});
 const result=samples.map(({name,box,a,b})=>({name,box,nativeSHA256:crypto.createHash('sha256').update(Buffer.from(a)).digest('hex'),controlSHA256:crypto.createHash('sha256').update(Buffer.from(b)).digest('hex'),equal:Buffer.from(a).equals(Buffer.from(b)),differentChannels:a.reduce((sum,x,i)=>sum+(x!==b[i]),0)}));
 fs.writeFileSync(path.join(out,'hud-comparison.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(result.some(x=>!x.equal))process.exitCode=1;
}finally{await browser.close();}
