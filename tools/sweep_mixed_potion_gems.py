"""Bounded pairwise gem-order mutations on the 28554 mixed-potion prefix.

Candidate contacts come from the already measured baseline reachability list.
They need not stay reachable after two mutations; positive DP labels are accepted
only after the child tool replays all actions in the original-bytecode adapter.
"""
import argparse,hashlib,json,subprocess,sys,time,resource
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--mutations',default='experiments/early-reachable-mutations.json');p.add_argument('--out',default='generated/MixedGemSweep');a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=False);source=Path('experiments/full-route-ending-10088-proposal.json');events=json.loads(source.read_bytes())['actions'];raw=Path(a.mutations).read_bytes();pairs=json.loads(raw)
 candidates=[(i,j) for i,j in pairs if events[j].get('originalTile') in (9,10) and j!=143]
 # Preserve the full candidate set so reproduction need not regenerate contacts.
 (out/'mutations.json').write_text(json.dumps(candidates)+'\n');start=time.perf_counter();results=[]
 for n,pair in enumerate([None]+candidates):
  d=out/f'candidate-{n:03d}';cmd=[sys.executable,'tools/search_mixed_potion_reserve.py','--advance','135,143','--extra-advance','352,353','--extra-advance','352,549','--must-eat','333,375,376,549','--target-reserve','1300','--out',str(d)]
  if pair:cmd+=['--extra-advance',','.join(map(str,pair))]
  with (out/f'candidate-{n:03d}.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError(f'Candidate {n} failed; inspect its log')
  s=json.loads((d/'summary.json').read_text());results.append(dict(mutation=pair,targetNumericSurvives=s['targetNumericSurvives'],originalBytecodeVerified=s.get('originalBytecodeVerified',False),numericHP=s.get('numericHP'),maximumReservedHealingForTargetStatsUnderCap=s['maximumReservedHealingForTargetStatsUnderCap'],metrics=s['metrics']))
  print(json.dumps(dict(index=n,total=len(candidates)+1,**results[-1])),flush=True)
  receipt=dict(schemaVersion=1,sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),reachabilityMutationListSHA256=hashlib.sha256(raw).hexdigest(),scope='One additional baseline-reachable red/blue gem advancement combined with the declared 28554 prefix transformations. Numeric relaxed DP; positive witnesses require bytecode replay. Not exhaustive two-event, full-map or global search.',targetReservedHealing=1300,targetStats=[696,625,2],fixedAdvance=[135,143],fixedExtraAdvances=[[352,353],[352,549]],mustEat=[333,375,376,549],candidates=candidates,completed=len(results),results=results,complete=len(results)==len(candidates)+1,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-start,childPeakRSSBytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
  (out/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
