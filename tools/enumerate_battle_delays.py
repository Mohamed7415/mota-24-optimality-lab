"""Enumerate a bounded delayed-battle neighborhood on baseline map snapshots.

A cloned grid permits all reachable potion pickups and ignores resource gates.
Stop at an inaccessible mandatory event or a new dialogue; no plot-map transition
is invented. This is conservative heuristic pruning, not complete order search.
"""
import argparse,hashlib
import collections,json,sys,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
ap=argparse.ArgumentParser();ap.add_argument('--out',default='generated/battle-delay-mutations.json');ap.add_argument('--span',type=int,default=160);args=ap.parse_args()
raw=Path('experiments/full-route-ending-10088-proposal.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='6ea34628fa4d8bd6eaa732ae0674951ccec90e5c1ce577852fe1bf1d2c921f4a'
p=json.loads(raw);ev=p['actions'];end=next(i for i,a in enumerate(ev) if a['floor']==13 and a.get('originalTile')==55);ev=ev[:end+1]
r=OriginalRoute('generated/private/mhhf.swf',random_policy='worst-support');pairs=[];start=time.perf_counter()
def enumerate_at(index):
 grids=[[list(row) for row in r.grid(f)] for f in range(27)]
 links={(f,y*11+x):r.floor_edge(f,y*11+x) for f in range(14) for y,row in enumerate(grids[f]) for x,t in enumerate(row) if t in (13,14)}
 pos=r.location();out=[]
 def contact(f,target):
  queue=[pos];seen=set(queue)
  for floor,p in queue:
   if floor==f and target in r.neighbors(p):return floor,p
   for n in r.neighbors(p):
    t=grids[floor][n//11][n%11];dest=(floor,n) if t in (0,97,98,99) else links.get((floor,n))
    if dest is not None and dest not in seen:seen.add(dest);queue.append(dest)
  return None
 for j in range(index+1,min(index+args.span+1,end)):
  a=ev[j]
  if a['kind']=='floor':continue
  if a.get('shop') in (1,2,5):continue
  # A later mandatory event is a candidate insertion point, even if it cannot be
  # reached without the delayed enemy: restoring that enemy before it may work.
  out.append((index,j))
  f=a['floor'];x,y=a['position'];at=contact(f,y*11+x)
  if at is None:
   if a.get('originalTile') in (11,12):continue
   break
  pos=at
  if a['kind']=='dialogue':break # Do not approximate new plot-map transitions.
  if a['kind']=='shop':continue
  grids[f][y][x]=0;pos=(f,y*11+x)
 return out
for i,a in enumerate(ev):
 if a.get('hpCost',0)>0 and a.get('originalTile') not in (50,53):pairs.extend(enumerate_at(i))
 r.replay_action(a)
target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
with target.open('x') as handle:handle.write(json.dumps(pairs)+'\n')
print(json.dumps(dict(cases=len(pairs),seconds=time.perf_counter()-start)),flush=True)
