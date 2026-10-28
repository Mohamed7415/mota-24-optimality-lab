"""Finite three-stage XP allocation experiment on the pinned2018 numerical route.
No real-clock simulation, actual game ending or world-record claim.
"""
import argparse,copy,hashlib,itertools,json,resource,sys,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--swf',required=True);p.add_argument('--out',required=True);args=p.parse_args()
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
if digest!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Source mismatch')
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Archive mismatch')
actions=json.loads(raw)['actions'];out=Path(args.out);out.mkdir(exist_ok=False);started=time.perf_counter();base=OriginalRoute(args.swf,random_policy='worst-support')
for a in actions[:1087]:base.replay_action(a)
rows=[];best=None;recipes=list(itertools.product((0,3,6),(0,4,8),(0,6,12,17)))
for recipe in recipes:
 r=copy.deepcopy(base);error=None;index=None;case_start=time.perf_counter()
 try:
  for index,a in enumerate(actions[1087:],1087):
   if index in (1087,1255,1616):
    group=(1087,1255,1616).index(index)
    for _ in range(recipe[group]):r.touch(13,4,6,shop_choice=1)
    budget=r.resources()['experience']//95
    defense=budget*(7,6,0)[group]//(18,23,1)[group]
    for _ in range(budget-defense):r.touch(13,4,6,shop_choice=2)
    for _ in range(defense):r.touch(13,4,6,shop_choice=3)
   if 1087<=index<=1104 or 1255<=index<=1277 or 1616<=index<=1666:continue
   if 1437<=index<=1447:continue
   if 1555<=index<=1614:
    if index==1555:
     while r.resources()['money']>=100:r.touch(a['floor'],*a['position'],shop_choice=1)
    continue
   r.replay_action(a)
 except Exception as e:error=f'{type(e).__name__}: {e}'
 row=dict(threeLevelPurchaseRecipe=list(recipe),completeNumericalReplay=error is None and index==1712,lastSourceAction=index,error=error,resources=r.resources(),generatedActions=len(r.actions),suffixBytecodeInstructions=r.instructions-base.instructions,metrics=dict(elapsedSeconds=time.perf_counter()-case_start));rows.append(row)
 if row['completeNumericalReplay'] and (best is None or row['resources']['hp']>best['resources']['hp']):
  best=row;(out/'proposal-best-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources(),'recipe':list(recipe)},indent=2));print('BEST',json.dumps(row),flush=True)
 report=dict(schemaVersion=1,scope='36 fixed-order three-group XP leveling recipes on original2018 bytecode only',sourceProposalSHA256=digest,fixedPrefixSourceActions=1087,policy='3-level XP purchases at1087/1255/1616; remaining95XP stats use original early DEF ratios7/18 and6/23, then allATK; omit second-group11 GOLD DEF; all late GOLD buys4000HP',cases=len(recipes),completed=len(rows),complete=len(rows)==len(recipes),rows=rows,best=best,clockDeadlineSimulated=False,actualGameReplayed=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),totalSuffixBytecodeInstructions=sum(x['suffixBytecodeInstructions']for x in rows)))
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print('COMPLETE',json.dumps({k:v for k,v in report.items()if k!='rows'}),flush=True)
