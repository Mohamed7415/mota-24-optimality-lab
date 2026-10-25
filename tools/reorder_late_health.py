"""Delay optional late HP pickups and feathers; use legal original grid paths.

This deterministic heuristic only reorders the published route's actions.
At F24 prefer reachable enemies/doors before healing; original gates and bytecode
reject illegal transitions. Output is numeric, not a native play certificate.
"""
import json,sys,hashlib,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from route_sections import metadata
from flash_model import gate
src=Path('experiments/full-route-ending-10088-proposal.json');old=json.loads(src.read_bytes());ev=old['actions']
start=next(i for i,e in enumerate(ev) if e['floor']==24 and e.get('originalTile')==3 and e['position']==[1,2])
end=max(i for i,e in enumerate(ev) if e['floor']==24 and e.get('originalTile')==31)
selected=[i for i,e in enumerate(ev) if 1200<i<start and e['floor'] in (23,25) and e.get('originalTile') in (11,12,30,31)]
r=OriginalRoute('generated/private/mhhf.swf',random_policy='worst-support');began=time.perf_counter();order=[]
def apply(i):
 e=ev[i]
 if e['kind']=='fly':r.fly(e['toFloor'])
 elif e['kind']=='floor':r.take_stair(e['floor'],*e['position'])
 else:
  assert r.grid(e['floor'])[e['position'][1]][e['position'][0]]==e['originalTile'],i
  r.touch(e['floor'],*e['position'],shop_choice=e.get('choice'))
 order.append(i)
try:
 for i in range(start):
  if i not in selected:apply(i)
 pending=list(range(start,end+1));deferred=[]
 while pending:
  candidates=[];s=r.resources()
  for i in pending:
   e=ev[i];t=e.get('originalTile')
   if e['kind']=='floor':raise ValueError('unexpected stair')
   try:path=r.contact_path(e['floor'],e['position'][1]*11+e['position'][0])
   except ValueError:continue
   if 40<=t<=70 and not gate(r.root['boss_man'][t-40],s['hp'],s['atk'],s['def'],t-40):continue
   health={11:200,12:500,30:1000,31:3000}.get(t,0)
   candidates.append((bool(health),health,t!=57,len(path),i))
  if not candidates:raise ValueError('No reachable next event')
  _,health,_,_,i=min(candidates)
  if health and not any(ev[j].get('originalTile')==57 for j in pending):break
  apply(i);pending.remove(i)
  print('REGION',i,r.resources(),flush=True)
 for i in selected+pending:apply(i)
 for i in range(end+1,len(ev)):apply(i)
 print('SUCCESS',r.resources(),flush=True)
 d=Path('generated/LateHPGreedy');d.mkdir(exist_ok=True)
 out=dict(scope='Numeric candidate only, not native completion or record proof',randomPolicy=r.random_policy,actions=r.actions,resources=r.resources(),location=r.location(),draws=r.draws,sections=metadata(r.sections),transformation=dict(parentSHA256=hashlib.sha256(src.read_bytes()).hexdigest(),sourceActionOrder=order,scope='Reorders original source actions only; all movement and effects reexecuted in pinned original bytecode.'),elapsedSeconds=time.perf_counter()-began)
 (d/'proposal.json').write_text(json.dumps(out,indent=2)+'\n')
except Exception as ex:
 print('FAILED',i,r.resources(),str(ex),flush=True);raise
