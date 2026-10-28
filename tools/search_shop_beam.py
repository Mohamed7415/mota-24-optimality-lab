"""Bounded heuristic beam over real-route GOLD/XP shop allocations.
Every retained transition executes pinned original AVM1. Linear shop summaries
only rank branches; replayed resource totals must agree before acceptance.
Fixed mandatory event order, finite beam and coarse allocations: no global proof.
"""
import argparse,copy,hashlib,itertools,json,math,resource,sys,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--swf',required=True);p.add_argument('--out',required=True);p.add_argument('--xp-cap',type=int,default=48);p.add_argument('--beam',type=int,default=12);p.add_argument('--branches',type=int,default=36);p.add_argument('--seconds',type=int,default=600);p.add_argument('--resume')
a=p.parse_args()
if not(1<=a.xp_cap<=100 and 1<=a.beam<=64 and 1<=a.branches<=256 and 1<=a.seconds<=3600):raise ValueError('Invalid finite limits')
source=Path('experiments/full-route-hp28568-proposal.json').read_bytes();digest=hashlib.sha256(source).hexdigest()
if digest!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Proposal mismatch')
if hashlib.sha256(Path(a.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('SWF mismatch')
x=json.loads(source)['actions'];out=Path(a.out);out.mkdir(exist_ok=False);started=time.perf_counter();deadline=started+a.seconds
FIELDS=('hp','atk','def','level','money','experience')
def decision(v):return v.get('shop')in(1,2,5,6) and v.get('choice')in(1,2,3)
groups=[];i=0
while i<len(x):
 if not decision(x[i]):i+=1;continue
 j=i+1
 while j<len(x) and decision(x[j]) and x[j]['shop']==x[i]['shop']:j+=1
 groups.append((i,j));i=j
stats=dict(expandedTransitions=0,rejectedTransitions=0,acceptedTransitions=0,linearSummaryDisagreements=0,modelInstructions=0);stages=[]
def quality(r):return .2*math.log1p(r['hp'])+math.log1p(r['atk'])+math.log1p(r['def'])
def select(rows,n,resource,spent):
 if len(rows)<=n:return rows
 rankings=[sorted(rows,key=lambda z:(spent(z),-quality(resource(z)))),sorted(rows,key=lambda z:(-quality(resource(z)),spent(z))),sorted(rows,key=lambda z:(-resource(z)['atk'],-resource(z)['def'],spent(z))),sorted(rows,key=lambda z:(-resource(z)['def'],-resource(z)['atk'],spent(z))),sorted(rows,key=lambda z:(-resource(z)['hp'],spent(z))),sorted(rows,key=lambda z:(-resource(z)['experience'],spent(z)))]
 result=[];seen=set()
 for rank in range(max(map(len,rankings))):
  for ordered in rankings:
   row=ordered[rank];key=id(row)
   if key not in seen:seen.add(key);result.append(row)
   if len(result)>=n:return result
 return result
start_group=0;frontier=[]
if a.resume:
 prior=json.load(open(a.resume))
 if prior['sourceProposalSHA256']!=digest or prior['xpPurchaseCap']!=a.xp_cap:raise ValueError('Resume scope mismatch')
 start_group=prior['nextGroupIndex']
 for row in prior['frontier']:
  r=OriginalRoute(a.swf,random_policy='worst-support')
  for action in row['actions']:r.replay_action(action)
  if r.resources()!=row['resources']:raise ValueError('Rebuilt checkpoint differs')
  frontier.append((r,row['xpPurchases']))
else:
 r=OriginalRoute(a.swf,random_policy='worst-support')
 for v in x[:groups[0][0]]:r.replay_action(v)
 stats['modelInstructions']+=r.instructions;frontier=[(r,0)]
next_group=start_group;stopped='time limit';best=None

def checkpoint():
 data=dict(schemaVersion=1,scope='Heuristic shop-allocation beam over fixed real-map event order; not global optimality or actual-game proof',sourceProposalSHA256=digest,xpPurchaseCap=a.xp_cap,beamWidth=a.beam,branchesPerParent=a.branches,nextGroupIndex=next_group,totalGroups=len(groups),frontier=[dict(actions=r.actions,resources=r.resources(),xpPurchases=n)for r,n in frontier],stages=stages,stats=stats,stopReason=stopped,completeNumericalCandidate=best,actualGameReplayed=False,clockDeadlineSimulated=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
 temp=out/'checkpoint.tmp';temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(out/'checkpoint.json')
 report={k:v for k,v in data.items()if k!='frontier'};report['frontierStates']=len(frontier);(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')

for gi in range(start_group,len(groups)):
 if time.perf_counter()>deadline:break
 lo,hi=groups[gi];end=groups[gi+1][0]if gi+1<len(groups)else len(x);shop=x[lo];is_xp=shop['shop']in(5,6);survivors=[];timed_out=False
 for parent,used in frontier:
  original=parent.resources();effects={}
  for option in (1,2,3):
   probe=copy.deepcopy(parent)
   try:probe.touch(shop['floor'],*shop['position'],shop_choice=option)
   except ValueError:continue
   stats['modelInstructions']+=probe.instructions-parent.instructions;after=probe.resources();delta={k:after[k]-original[k]for k in FIELDS}
   if delta['experience'if is_xp else'money']<0:effects[option]=delta
  candidates=[];seen=set()
  if is_xp:
   cost_level=-effects[1]['experience']if 1 in effects else None;cost_stat=-effects[2]['experience']if 2 in effects else None
   maxlevel=min(a.xp_cap-used,original['experience']//cost_level)if cost_level else 0
   for nl in range(maxlevel+1):
    budget=original['experience']-nl*(cost_level or 0);maxstats=min(a.xp_cap-used-nl,budget//cost_stat)if cost_stat else 0
    for ns in range(maxstats+1):
     splits=range(ns+1)if ns<=4 else sorted({0,ns//4,ns//2,3*ns//4,ns})
     for na in splits:
      counts=(nl,na,ns-na)
      if any(count and option not in effects for option,count in enumerate(counts,1)):continue
      predicted={k:original[k]+sum(count*effects[option][k]for option,count in enumerate(counts,1)if count)for k in FIELDS};predicted['keys']=original['keys']
      candidates.append(dict(counts=counts,predicted=predicted,used=used+sum(counts)))
  else:
   n=hi-lo
   for nh in sorted({0,n//4,n//2,3*n//4,n}):
    rest=n-nh
    for na in sorted({0,rest//4,rest//2,3*rest//4,rest}):
     counts=(nh,na,rest-na)
     if any(count and option not in effects for option,count in enumerate(counts,1)):continue
     predicted={k:original[k]+sum(count*effects[option][k]for option,count in enumerate(counts,1)if count)for k in FIELDS};predicted['keys']=original['keys']
     if predicted['money']<0:continue
     candidates.append(dict(counts=counts,predicted=predicted,used=used))
  candidates=select(candidates,a.branches,lambda z:z['predicted'],lambda z:z['used'])
  for candidate in candidates:
   if time.perf_counter()>deadline:timed_out=True;break
   stats['expandedTransitions']+=1;child=copy.deepcopy(parent);before_steps=child.instructions
   try:
    for option,count in enumerate(candidate['counts'],1):
     for _ in range(count):child.touch(shop['floor'],*shop['position'],shop_choice=option)
    if child.resources()!=candidate['predicted']:
     stats['linearSummaryDisagreements']+=1;raise ValueError('Shop summary mismatch; reject')
    for v in x[hi:end]:child.replay_action(v)
    survivors.append((child,candidate['used']));stats['acceptedTransitions']+=1
   except ValueError:stats['rejectedTransitions']+=1
   finally:stats['modelInstructions']+=child.instructions-before_steps
  if timed_out:break
 if timed_out:break
 distinct={}
 for r,n in survivors:
  res=r.resources();key=(tuple(res[k]for k in FIELDS),tuple(res['keys']),r.location(),n)
  distinct.setdefault(key,(r,n))
 kept=select(list(distinct.values()),a.beam,lambda z:z[0].resources(),lambda z:z[1])
 stages.append(dict(groupIndex=gi,sourceRange=[lo,hi],shop=shop['shop'],nextSourceIndex=end,acceptedChildren=len(survivors),distinctResourceStates=len(distinct),retainedStates=len(kept)))
 frontier=kept;next_group=gi+1
 if not frontier:stopped='frontier empty under this heuristic';checkpoint();break
 if end==len(x):
  r,n=min(frontier,key=lambda z:(z[1],-z[0].resources()['hp']));best=dict(xpPurchases=n,resources=r.resources(),sourceActionsFinished=len(x),generatedActions=len(r.actions));(out/'proposal-best-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources(),'xpPurchases':n},indent=2));stopped='complete numerical candidate requires actual H5 replay';checkpoint();print('NUMERICAL_CANDIDATE',json.dumps(best),flush=True);break
 checkpoint();print(json.dumps({'completedGroups':next_group,'nextSourceIndex':end,'frontier':len(frontier),'stats':stats,'elapsedSeconds':time.perf_counter()-started}),flush=True)
else:stopped='all groups completed'
checkpoint();print('STOP',stopped,'groups',next_group,'of',len(groups),flush=True)
