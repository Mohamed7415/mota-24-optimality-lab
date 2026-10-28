"""Bounded heuristic beam over real-route GOLD/XP shop allocations.
Every retained transition executes pinned original AVM1. Linear shop summaries
only rank branches; replayed resource totals must agree before acceptance.
Fixed mandatory event order, finite beam and coarse allocations: no global proof.
"""
import argparse,copy,gc,hashlib,itertools,json,math,resource,shutil,sys,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from shop_frontier import prune as prune_projection
from route_clone import clone_for_search
from shop_diversity import select_diverse
from avm1 import Unsupported
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--swf',required=True);p.add_argument('--out',required=True);p.add_argument('--xp-cap',type=int,default=48);p.add_argument('--beam',type=int,default=12);p.add_argument('--branches',type=int,default=36);p.add_argument('--seconds',type=int,default=600);p.add_argument('--resume');p.add_argument('--anchor-original-prefix',action='store_true');p.add_argument('--resource-projection-pruning',action='store_true');p.add_argument('--lean-clone',action='store_true');p.add_argument('--objective',choices=('xp-purchases','remaining-xp','remaining-gold'),default='xp-purchases');p.add_argument('--allow-relaxed-cap',action='store_true');p.add_argument('--min-final-xp',type=int,default=0);p.add_argument('--diverse-selection',action='store_true');p.add_argument('--min-final-gold',type=int,default=6661)
a=p.parse_args()
if not(1<=a.xp_cap<=200 and 1<=a.beam<=64 and 1<=a.branches<=256 and 1<=a.seconds<=3600):raise ValueError('Invalid finite limits')
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
stats=dict(expandedTransitions=0,rejectedTransitions=0,acceptedTransitions=0,linearSummaryDisagreements=0,modelInstructions=0,resourceProjectionRemoved=0,unsupportedTransitions=0);stages=[]
def fork_route(route):
 return clone_for_search(route) if a.lean_clone else copy.deepcopy(route)

def quality(r):return .2*math.log1p(r['hp'])+math.log1p(r['atk'])+math.log1p(r['def'])
def select(rows,n,resource,spent):
 if len(rows)<=n:return rows
 if a.objective=='remaining-xp':spent=lambda row:-resource(row)['experience']
 if a.objective=='remaining-gold':spent=lambda row:-resource(row)['money']
 if a.diverse_selection:return select_diverse(rows,n,resource,spent)
 rankings=[sorted(rows,key=lambda z:(spent(z),-quality(resource(z)))),sorted(rows,key=lambda z:(-quality(resource(z)),spent(z))),sorted(rows,key=lambda z:(-resource(z)['atk'],-resource(z)['def'],spent(z))),sorted(rows,key=lambda z:(-resource(z)['def'],-resource(z)['atk'],spent(z))),sorted(rows,key=lambda z:(-resource(z)['hp'],spent(z))),sorted(rows,key=lambda z:(-resource(z)['experience'],spent(z)))]
 result=[];seen=set()
 for rank in range(max(map(len,rankings))):
  for ordered in rankings:
   row=ordered[rank];key=id(row)
   if key not in seen:seen.add(key);result.append(row)
   if len(result)>=n:return result
 return result
def prune_nodes(nodes):
 if not a.resource_projection_pruning:return nodes
 rows=[dict(actions=r.actions,resources=r.resources(),xpPurchases=n,node=(r,n))for r,n in nodes]
 kept,removed=prune_projection(rows);stats['resourceProjectionRemoved']+=len(removed)
 return [row['node']for row in kept]
start_group=0;frontier=[]
if a.resume:
 prior=json.load(open(a.resume))
 if prior['sourceProposalSHA256']!=digest:raise ValueError('Resume proposal mismatch')
 if prior['xpPurchaseCap']!=a.xp_cap and not(a.allow_relaxed_cap and prior['xpPurchaseCap']<=a.xp_cap):raise ValueError('Resume purchase cap mismatch')
 start_group=prior['nextGroupIndex']
 resume_rows=prior['frontier']
 if a.resource_projection_pruning:
  resume_rows,removed=prune_projection(resume_rows);stats['resourceProjectionRemoved']+=len(removed)
 for row in resume_rows:
  r=OriginalRoute(a.swf,random_policy='worst-support')
  for action in row['actions']:r.replay_action(action)
  if r.resources()!=row['resources']:raise ValueError('Rebuilt checkpoint differs')
  stats['modelInstructions']+=r.instructions
  frontier.append((r,row['xpPurchases']))
else:
 r=OriginalRoute(a.swf,random_policy='worst-support')
 for v in x[:groups[0][0]]:r.replay_action(v)
 stats['modelInstructions']+=r.instructions;frontier=[(r,0)]
baseline=None;baseline_index=groups[start_group][0] if start_group<len(groups) else len(x);baseline_used=0
if a.anchor_original_prefix:
 if a.resume:
  baseline=OriginalRoute(a.swf,random_policy='worst-support')
  for action in x[:baseline_index]:baseline.replay_action(action)
  stats['modelInstructions']+=baseline.instructions
 else:baseline=fork_route(frontier[0][0])
 baseline_used=sum(v.get('shop')in(5,6) and v.get('choice')in(1,2,3) for v in x[:baseline_index])
next_group=start_group;stopped='time limit';best=None;final_limit_candidate=None
tool_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def checkpoint():
 data=dict(schemaVersion=1,scope='Heuristic shop-allocation beam over fixed real-map event order; not global optimality or actual-game proof',sourceProposalSHA256=digest,sourceToolSHA256=tool_sha,objective=a.objective,minFinalXP=a.min_final_xp,minFinalGold=a.min_final_gold,resumeCapRelaxationAllowed=a.allow_relaxed_cap,xpPurchaseCap=a.xp_cap,beamWidth=a.beam,branchesPerParent=a.branches,originalPrefixAnchorEnabled=a.anchor_original_prefix,resourceProjectionPruningEnabled=a.resource_projection_pruning,leanCloneEnabled=a.lean_clone,diverseSelectionEnabled=a.diverse_selection,pruningHeuristicNotGlobalEquivalenceProof=True,nextGroupIndex=next_group,totalGroups=len(groups),frontier=[dict(actions=r.actions,resources=r.resources(),xpPurchases=n)for r,n in frontier],stages=stages,stats=stats,stopReason=stopped,completeNumericalCandidate=best,finalBossModelLimitCandidate=final_limit_candidate,instructionCounterIsLowerBoundWhenUnsupported=bool(stats['unsupportedTransitions']),actualGameReplayed=False,clockDeadlineSimulated=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
 if not frontier and (out/'checkpoint.json').exists() and json.loads((out/'checkpoint.json').read_text()).get('frontier'):
  shutil.copyfile(out/'checkpoint.json',out/'last-nonempty-checkpoint.json')
 temp=out/'checkpoint.tmp';temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(out/'checkpoint.json')
 report={k:v for k,v in data.items()if k!='frontier'};report['frontierStates']=len(frontier);(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')

for gi in range(start_group,len(groups)):
 if time.perf_counter()>deadline:break
 lo,hi=groups[gi];end=groups[gi+1][0]if gi+1<len(groups)else len(x);shop=x[lo];is_xp=shop['shop']in(5,6);survivors=[];timed_out=False
 for parent,used in frontier:
  original=parent.resources();effects={}
  for option in (1,2,3):
   probe=fork_route(parent)
   try:probe.touch(shop['floor'],*shop['position'],shop_choice=option)
   except Unsupported:
    stats['unsupportedTransitions']+=1;continue
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
   gold_sizes=sorted({0,(hi-lo)//4,(hi-lo)//2,3*(hi-lo)//4,hi-lo}) if a.objective=='remaining-gold' else [hi-lo]
   for n in gold_sizes:
    for nh in sorted({0,n//4,n//2,3*n//4,n}):
     rest=n-nh
     for na in sorted({0,rest//4,rest//2,3*rest//4,rest}):
      counts=(nh,na,rest-na)
      if any(count and option not in effects for option,count in enumerate(counts,1)):continue
      predicted={k:original[k]+sum(count*effects[option][k]for option,count in enumerate(counts,1)if count)for k in FIELDS};predicted['keys']=original['keys']
      if predicted['money']<0:continue
      candidates.append(dict(counts=counts,predicted=predicted,used=used))
  source_candidate=None
  if a.anchor_original_prefix:
   original_counts=tuple(sum(v['choice']==option for v in x[lo:hi])for option in (1,2,3))
   source_candidate=next((z for z in candidates if z['counts']==original_counts),None)
  candidates=select(candidates,a.branches,lambda z:z['predicted'],lambda z:z['used'])
  if source_candidate is not None and not any(z is source_candidate for z in candidates):
   candidates=candidates[:max(0,a.branches-1)]+[source_candidate]
  for candidate in candidates:
   if time.perf_counter()>deadline:timed_out=True;break
   stats['expandedTransitions']+=1;child=fork_route(parent);before_steps=child.instructions;failing_index=None;before_resources=None;before_location=None;before_action_count=None
   try:
    for option,count in enumerate(candidate['counts'],1):
     for _ in range(count):child.touch(shop['floor'],*shop['position'],shop_choice=option)
    if child.resources()!=candidate['predicted']:
     stats['linearSummaryDisagreements']+=1;raise ValueError('Shop summary mismatch; reject')
    for failing_index,v in enumerate(x[hi:end],hi):
     before_resources=child.resources();before_location=child.location();before_action_count=len(child.actions)
     child.replay_action(v)
    survivors.append((child,candidate['used']));stats['acceptedTransitions']+=1
   except Unsupported as exc:
    stats['unsupportedTransitions']+=1
    if failing_index==len(x)-1 and child.root.get('Display_kill')==1 and (a.objective!='remaining-xp' or before_resources['experience']>=a.min_final_xp) and (a.objective!='remaining-gold' or before_resources['money']>=a.min_final_gold):
     final_limit_candidate=dict(xpPurchases=candidate['used'],sourceActionIndex=failing_index,error=str(exc),resourcesBeforeFinalAction=before_resources,locationBeforeFinalAction=before_location,originalBattleGateOpened=True,completeNumericalReplay=False,actualGameReplayed=False,recordBreakingRoute=False)
     proposed={k:v for k,v in x[-1].items() if k in ('kind','floor','position','originalTile')}
     (out/'final-boss-model-limit-candidate-private.json').write_text(json.dumps({'actions':child.actions[:before_action_count],'resources':before_resources,'proposedFinalAction':proposed,'evidence':final_limit_candidate},indent=2)+'\n')
   except ValueError:stats['rejectedTransitions']+=1
   finally:stats['modelInstructions']+=child.instructions-before_steps
   if final_limit_candidate:break
  if final_limit_candidate:break
  if a.anchor_original_prefix and len(survivors)>a.beam*4:
   survivors=prune_nodes(survivors)
   survivors=select(survivors,a.beam*4,lambda z:z[0].resources(),lambda z:z[1]);gc.collect()
  if timed_out:break
 if final_limit_candidate:
  stopped='final battle interpreter limit; actual H5 verification required';checkpoint();break
 if timed_out:break
 survivors=prune_nodes(survivors)
 distinct={}
 for r,n in survivors:
  res=r.resources();key=(tuple(res[k]for k in FIELDS),tuple(res['keys']),r.location(),n)
  distinct.setdefault(key,(r,n))
 kept=select(list(distinct.values()),a.beam,lambda z:z[0].resources(),lambda z:z[1])
 anchored=False
 if baseline is not None:
  before_steps=baseline.instructions
  for v in x[baseline_index:end]:
   baseline.replay_action(v)
   baseline_used+=v.get('shop')in(5,6) and v.get('choice')in(1,2,3)
  stats['modelInstructions']+=baseline.instructions-before_steps;baseline_index=end
  if baseline_used<=a.xp_cap:
   br=baseline.resources();signature=(br,baseline.location(),baseline_used)
   kept=[node for node in kept if (node[0].resources(),node[0].location(),node[1])!=signature]
   kept=kept[:max(0,a.beam-1)]+[(fork_route(baseline),baseline_used)];anchored=True
 stages.append(dict(groupIndex=gi,sourceRange=[lo,hi],shop=shop['shop'],nextSourceIndex=end,acceptedChildren=len(survivors),distinctResourceStates=len(distinct),retainedStates=len(kept),legalOriginalPrefixAnchorInserted=anchored))
 frontier=kept;next_group=gi+1
 del distinct,survivors
 if a.lean_clone:gc.collect()
 if not frontier:stopped='frontier empty under this heuristic';checkpoint();break
 if end==len(x):
  r,n=(max(frontier,key=lambda z:(z[0].resources()['experience' if a.objective=='remaining-xp' else 'money'],-z[1],z[0].resources()['hp'])) if a.objective in ('remaining-xp','remaining-gold') else min(frontier,key=lambda z:(z[1],-z[0].resources()['hp'])));best=dict(objective=a.objective,numericGoalReached=(r.resources()['experience']>=a.min_final_xp if a.objective=='remaining-xp' else r.resources()['money']>=a.min_final_gold if a.objective=='remaining-gold' else n<=a.xp_cap),xpPurchases=n,resources=r.resources(),sourceActionsFinished=len(x),generatedActions=len(r.actions));(out/'proposal-best-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources(),'xpPurchases':n},indent=2));stopped='complete numerical candidate requires actual H5 replay';checkpoint();print('NUMERICAL_CANDIDATE',json.dumps(best),flush=True);break
 checkpoint();print(json.dumps({'completedGroups':next_group,'nextSourceIndex':end,'frontier':len(frontier),'stats':stats,'elapsedSeconds':time.perf_counter()-started}),flush=True)
else:stopped='all groups completed'
checkpoint();print('STOP',stopped,'groups',next_group,'of',len(groups),flush=True)
