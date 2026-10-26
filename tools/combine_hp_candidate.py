"""Combine verified F13 allocation prefix and delayed-health suffix.

Omit the now-unaffordable duplicate early cheap purchase, retaining the later
purchase. Collect all reachable remaining healing before holy water. Every action
runs the original-bytecode adapter; no hero, map or currency state is assigned.
"""
import argparse,json,sys,hashlib,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from route_sections import metadata
ap=argparse.ArgumentParser();ap.add_argument('--prefix',default='generated/PrefixAllocation31-0/proposal.json');ap.add_argument('--tail',default='generated/LateHPGreedy/proposal.json');ap.add_argument('--directory',default='generated/CombinedHP');ap.add_argument('--expected-hp',type=int,default=28376);args=ap.parse_args()
prefix=Path(args.prefix);tail=Path(args.tail);p=json.loads(prefix.read_bytes());q=json.loads(tail.read_bytes());ev=q['actions'];captain=next(i for i,e in enumerate(ev) if e['floor']==13 and e.get('originalTile')==55);cheap=next(i for i,e in enumerate(ev) if i>captain and e.get('shop')==5)
r=OriginalRoute('generated/private/mhhf.swf',random_policy='worst-support');began=time.perf_counter()
try:
 for e in p['actions']:r.replay_action(e)
 for i,e in enumerate(ev[captain+1:],captain+1):
  if i==cheap:continue
  if e.get('originalTile')==33:
   while True:
    found=False
    for f in range(26):
     try:r.match(f,{11,12})
     except ValueError as ex:
      if not str(ex).startswith('No reachable'):raise
     else:found=True
    if not found:break
  before=r.resources();r.replay_action(e)
  if e['kind']=='shop' and e.get('choice') in (1,2,3) and before==r.resources():raise ValueError('Purchase failed')
 assert r.resources()=={'hp':args.expected_hp,'atk':5056,'def':5032,'level':17,'keys':[0,0,0],'money':1238,'experience':1080}
 assert r.grid(26)[3][5]==0 and 'game_over' in r.timeline
 print('SUCCESS',r.resources(),flush=True)
 d=Path(args.directory);d.mkdir(exist_ok=True)
 out=dict(scope='Numeric candidate only, not native completion or record proof',randomPolicy=r.random_policy,actions=r.actions,resources=r.resources(),location=r.location(),draws=r.draws,sections=metadata(r.sections),transformation=dict(prefixSHA256=hashlib.sha256(prefix.read_bytes()).hexdigest(),suffixSHA256=hashlib.sha256(tail.read_bytes()).hexdigest(),suffixAfterSourceIndex=captain,omittedCheapIndex=cheap,allReachableHealthBeforeHoly=True),elapsedSeconds=time.perf_counter()-began)
 (d/'proposal.json').write_text(json.dumps(out,indent=2)+'\n')
except Exception as ex:
 print('FAILED',i,e,r.resources(),str(ex),flush=True);raise
