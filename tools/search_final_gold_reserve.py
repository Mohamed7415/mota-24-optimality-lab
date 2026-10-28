"""Bounded actual-bytecode late gold savings grid; never actual-game proof."""
import argparse,hashlib,json,sys,time,resource
from pathlib import Path
sys.path[:0]=['src','tools']
from original_route import OriginalRoute
from route_clone import clone_for_search
from avm1 import Unsupported
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--swf',required=True);p.add_argument('--out',required=True);p.add_argument('--seconds',type=int,default=600);a=p.parse_args()
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9'
assert hashlib.sha256(Path(a.swf).read_bytes()).hexdigest()=='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896'
out=Path(a.out);out.mkdir(exist_ok=False);start=time.monotonic();x=json.loads(raw)['actions'];base=OriginalRoute(a.swf,random_policy='worst-support')
for action in x[:1555]:base.replay_action(action)
rows=[];best=None
for gold_def in (0,1,2,3,4,5,60):
 parent=clone_for_search(base)
 for _ in range(gold_def):parent.touch(x[1555]['floor'],*x[1555]['position'],shop_choice=3)
 for action in x[1615:1616]:parent.replay_action(action)
 for xp_atk in range(0,63,2):
  if time.monotonic()-start>a.seconds:break
  child=clone_for_search(parent);row={'goldDefenseBuys':gold_def,'requestedXpAttackContacts':xp_atk,'requestedXpDefenseContacts':62-xp_atk}
  try:
   paid={2:0,3:0}
   for choice,count in ((2,xp_atk),(3,62-xp_atk)):
    for _ in range(count):
     before=child.resources()['experience'];child.touch(x[1616]['floor'],*x[1616]['position'],shop_choice=choice)
     paid[choice]+=child.resources()['experience']<before
   row['actualXpAttackBuys']=paid[2]
   row['actualXpDefenseBuys']=paid[3]
   for action in x[1667:]:child.replay_action(action)
   row.update(status='complete-model-route',resources=child.resources())
   if best is None or child.resources()['money']>best['resources']['money']:
    best=row.copy();(out/'proposal-best-private.json').write_text(json.dumps({'actions':child.actions,'resources':child.resources()},indent=2))
  except Unsupported as exc:row.update(status='unsupported',error=str(exc))
  except ValueError as exc:row.update(status='rejected',error=str(exc))
  rows.append(row);print(json.dumps(row),flush=True)
 if time.monotonic()-start>a.seconds:break
receipt=dict(scope='Fixed original prefix1555, late gold DEF0..5 or60 and 62 attempted final XP contacts (actual accepted buys separately counted) with even ATK splits; not exhaustive, actual-game proof or record',sourceToolSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,best=best,elapsedSeconds=time.monotonic()-start,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,actualGameReplayed=False,recordBreakingRoute=False)
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
