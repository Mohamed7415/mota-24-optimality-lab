"""Bounded late XP leveling/stat grid after a pinned numerical HP prefix.
Only reviewed AVM1 simulation runs here. No game clock, actual ending or record proof.
"""
import argparse,copy,hashlib,json,resource,sys,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--swf',required=True);p.add_argument('--out',required=True);args=p.parse_args()
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes();source_sha=hashlib.sha256(raw).hexdigest()
if source_sha!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Proposal mismatch')
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Archive mismatch')
actions=json.loads(raw)['actions'];out=Path(args.out);out.mkdir(exist_ok=False);started=time.perf_counter();base=OriginalRoute(args.swf,random_policy='worst-support')
for i,a in enumerate(actions[:1616]):
 if 1437<=i<=1447:continue
 if 1555<=i<=1614:
  if i==1555:
   while base.resources()['money']>=100:base.touch(a['floor'],*a['position'],shop_choice=1)
  continue
 base.replay_action(a)
rows=[];best=None
for levels in (0,3,6,9,12,15,17):
 for defense_percent in (0,25,50,75,100):
  r=copy.deepcopy(base);start=time.perf_counter();error=None;index=1616
  try:
   for _ in range(levels):r.touch(13,4,6,shop_choice=1)
   budget=r.resources()['experience']//95;defense=budget*defense_percent//100
   for _ in range(budget-defense):r.touch(13,4,6,shop_choice=2)
   for _ in range(defense):r.touch(13,4,6,shop_choice=3)
   for index,a in enumerate(actions[1667:],1667):r.replay_action(a)
  except Exception as e:error=f'{type(e).__name__}: {e}'
  row=dict(recipe=dict(threeLevelPurchases=levels,remainingStatDefensePercent=defense_percent),completeNumericalReplay=error is None and index==1712,lastSourceAction=index,error=error,resources=r.resources(),generatedActions=len(r.actions),suffixBytecodeInstructions=r.instructions-base.instructions,metrics=dict(elapsedSeconds=time.perf_counter()-start))
  rows.append(row)
  if row['completeNumericalReplay'] and (best is None or row['resources']['hp']>best['resources']['hp']):
   best=row;(out/'proposal-best-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources(),'recipe':row['recipe']},indent=2));print('BEST',json.dumps(row),flush=True)
  report=dict(schemaVersion=1,scope='35 finite late XP recipes on a fixed2018 numerical HP prefix only; no actual-game or record proof',sourceProposalSHA256=source_sha,fixedPrefixSourceActions=1616,prefixPolicy='Original order;29 first-group GOLD DEF; omit11 second-group GOLD DEF; all late available GOLD buys4000HP',cases=35,completed=len(rows),complete=len(rows)==35,best=best,rows=rows,clockDeadlineSimulated=False,actualGameReplayed=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),totalSuffixBytecodeInstructions=sum(x['suffixBytecodeInstructions']for x in rows)))
  (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print('COMPLETE',json.dumps({k:v for k,v in report.items()if k!='rows'}),flush=True)
