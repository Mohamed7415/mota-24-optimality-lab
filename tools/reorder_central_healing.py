"""Reorder real key purchases and side branches to delay the central F22 potion.

Every accepted effect executes reviewed original bytecode; no resource assignment.
The resulting numeric plan needs a complete unchanged-movie replay and separate
record-build/rule comparison. This is a deterministic heuristic, not optimality.
"""
import argparse,json,sys,time,hashlib
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from route_sections import metadata
ap=argparse.ArgumentParser();ap.add_argument('--out',default='generated/LateCentral500Compass');ap.add_argument('--swf',default='generated/private/mhhf.swf');args=ap.parse_args()
source=Path('experiments/full-route-hp28554-proposal.json');raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='abc3fa2f36e64e717a10b36cf4144a98a3ac6614031f681da0660e18f6de3d26';p=json.loads(raw);ev=p['actions'];r=OriginalRoute(args.swf,random_policy='worst-support');done=set();order=[];started=time.perf_counter()

def apply(i):
 if i in done:return
 e=ev[i]
 if e['kind'] in ('floor','fly'):return

 if r.location()[0]!=e['floor']:
  if e['floor']<=20:r.fly(e['floor'])
  elif r.location()[0]<20:r.fly(20)
 try:r.contact_path(e['floor'],e['position'][1]*11+e['position'][0])
 except ValueError:
  if e['floor']<=20:r.fly(e['floor'])
  else:r.fly(20)
 r.replay_action(e);done.add(i);order.append(i)


def defenses(target):
 for j in range(1348,1416):
  e=ev[j]
  if j in done or e['kind']!='shop' or e.get('choice')!=3:continue
  if r.resources()['def']>=target:break
  if e.get('shop')==2 and r.resources()['money']>=100 or e.get('shop')==6 and r.resources()['experience']>=95:apply(j)
 assert r.resources()['def']>=target,('Insufficient affordable defense',target,r.resources())

try:
 for i,e in enumerate(ev[:1293]):r.replay_action(e);done.add(i);order.append(i)
 # Buy the already-budgeted two red and one blue keys before entering F22.
 for i in range(1345,1348):apply(i)
 for i in range(1294,1297):apply(i)
 for i in (1306,1307):apply(i)
 # Right branch before the left branch; no extra door/key expenditure.
 for i in range(1420,1436):apply(i)
 apply(1436)
 for i in (1437,1438,1439,1440,1441):apply(i)
 idx=19;target=int(r.root['boss_man'][idx][1]);defenses(target)
 for i in range(1442,1459):apply(i)
 print('FOUR_RIGHT_SPIRITS_DONE',r.resources(),flush=True)
 # Only now consume the central 500 and obtain the three key boxes.
 for i in range(1297,1305):apply(i)
 # Remaining original consume/shop/dialogue events, preserving their order.
 for i in range(1293,len(ev)):
  if i in done or ev[i]['kind'] in ('floor','fly'):continue
  e=ev[i]
  if e.get('originalTile')==33:
   while True:
    found=False
    for f in range(26):
     try:r.match(f,{11,12})
     except ValueError as ex:
      if not str(ex).startswith('No reachable'):raise
     else:found=True
    if not found:break
  apply(i)
 assert r.resources()==dict(hp=28568,atk=5056,**{'def':5032},level=17,keys=[0,0,0],money=1238,experience=1080),r.resources()
 assert r.grid(26)[3][5]==0 and 'game_over' in r.timeline
 d=Path(args.out);d.mkdir(exist_ok=False);(d/'proposal.json').write_text(json.dumps(dict(scope='Numeric candidate only, not native completion or record proof',randomPolicy=r.random_policy,actions=r.actions,resources=r.resources(),location=r.location(),draws=r.draws,sections=metadata(r.sections),transformation=dict(sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),sourceActionOrder=order,earlyKeyPurchases=[1345,1346,1347],rightBranchBeforeCentralPotion=True,ordinaryDamageAvoidance='Only affordable original future defense purchases, before the actual side-branch boss attack threshold',compassPolicy='Use original compass when changing to a visited floor 1..20; otherwise return via20 if needed'),elapsedSeconds=time.perf_counter()-started),indent=2)+'\n')
 print('SUCCESS',r.resources(),flush=True)
except Exception as e:
 print('FAILED',i,r.location(),r.resources(),str(e),flush=True);raise
