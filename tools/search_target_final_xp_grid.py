"""Bounded final-shop grid on unchanged high-gold real-route parents.
For each level-buy count, spend maximal remaining XP on every integer ATK/DEF
split. Omits submaximal spending and event-order changes: no optimality proof.
"""
import argparse,hashlib,json,resource,sys,time
from pathlib import Path
sys.path[:0]=['src','tools']
from original_route import OriginalRoute
from route_clone import clone_for_search
from avm1 import Unsupported
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--swf',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--out',required=True);p.add_argument('--seconds',type=int,default=1800);a=p.parse_args()
assert 1<=a.seconds<=3600
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9'
assert hashlib.sha256(Path(a.swf).read_bytes()).hexdigest()=='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896'
craw=Path(a.checkpoint).read_bytes();c=json.loads(craw);assert c['nextGroupIndex']==87 and c['sourceProposalSHA256']==sha
x=json.loads(raw)['actions'];out=Path(a.out);out.mkdir(exist_ok=False);start=time.monotonic();rows=[];best=None;done=[];stopped='time limit'
def save():
 r=dict(scope=__doc__,sourceToolSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),parentCheckpointSHA256=hashlib.sha256(craw).hexdigest(),rows=rows,best=best,completedParents=done,stopReason=stopped,elapsedSeconds=time.monotonic()-start,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,recordBreakingRoute=False,actualGameReplayed=False)
 temp=out/'receipt.tmp';temp.write_text(json.dumps(r,indent=2)+'\n');temp.replace(out/'receipt.json')
for index,node in enumerate(c['frontier']):
 assert node['resources']['money']>=6661
 base=OriginalRoute(a.swf,random_policy='worst-support')
 for action in node['actions']:base.replay_action(action)
 assert base.resources()==node['resources']
 effects={}
 for option in (1,2,3):
  probe=clone_for_search(base);probe.touch(x[1616]['floor'],*x[1616]['position'],shop_choice=option)
  effects[option]=base.resources()['experience']-probe.resources()['experience']
 assert effects[1]>0 and effects[2]==effects[3]>0
 remaining_cap=200-node['xpPurchases'];finished=True
 for levels in range(min(remaining_cap,base.resources()['experience']//effects[1])+1):
  stats=min(remaining_cap-levels,(base.resources()['experience']-levels*effects[1])//effects[2])
  for attack in range(stats+1):
   if time.monotonic()-start>a.seconds:finished=False;break
   child=clone_for_search(base);row=dict(parentIndex=index,levelBuys=levels,attackBuys=attack,defenseBuys=stats-attack)
   try:
    for choice,count in ((1,levels),(2,attack),(3,stats-attack)):
     for _ in range(count):
      before=child.resources()['experience'];child.touch(x[1616]['floor'],*x[1616]['position'],shop_choice=choice)
      if before-child.resources()['experience']!=effects[choice]:raise AssertionError('Paid purchase differs from budget')
    for action in x[1667:]:child.replay_action(action)
    row.update(status='complete-model-route',resources=child.resources())
    if best is None or row['resources']['money']>best['resources']['money']:
     best=row.copy();(out/'proposal-best-private.json').write_text(json.dumps({'actions':child.actions,'resources':child.resources()},indent=2)+'\n')
   except Unsupported as e:row.update(status='unsupported',error=str(e))
   except ValueError as e:row.update(status='rejected',error=str(e))
   rows.append(row)
   if len(rows)%25==0:save();print('tested',len(rows),'parent',index,'best',best,flush=True)
   if best:break
  if not finished or best:break
 if finished:done.append(index)
 save()
 if not finished or best:break
else:stopped='all specified maximal-spend splits completed'
if best:stopped='numerical goal candidate requires actual H5 and independent replay'
save();print('STOP',stopped,'tested',len(rows),'best',best,flush=True)
