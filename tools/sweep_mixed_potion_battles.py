"""Delay one battle on the verified mixed-potion schedule; bounded numeric search.

The supplied candidates were measured with the baseline navigation graph, limited
to a 160-event span and stopped at dialogues. Changes to consumed sets or numeric
labels may invalidate that reachability, so positive witnesses require separate
original-bytecode replay and a full suffix. Never infer a global bound or record.
"""
import argparse,hashlib,json,subprocess,sys,time,resource
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--mutations',default='experiments/early-battle-delay-mutations.json');p.add_argument('--out',default='generated/MixedBattleSweep');p.add_argument('--limit',type=int,default=0);a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=False);raw=Path(a.mutations).read_bytes();candidates=json.loads(raw)
 if a.limit:candidates=candidates[:a.limit]
 start=time.perf_counter();results=[];verified=[]
 for n,pair in enumerate(candidates):
  d=out/f'candidate-{n:04d}';cmd=[sys.executable,'tools/search_mixed_potion_reserve.py','--advance','135,143','--extra-advance','352,353','--extra-advance','352,549','--must-eat','333,375,376,549','--target-reserve','1300','--delay',','.join(map(str,pair)),'--out',str(d)]
  with (out/f'candidate-{n:04d}.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError(f'Candidate {n} failed; inspect log')
  s=json.loads((d/'summary.json').read_text());row=dict(mutation=pair,targetNumericSurvives=s['targetNumericSurvives'],originalBytecodeVerified=s.get('originalBytecodeVerified',False),numericHP=s.get('numericHP'),maximumReservedHealingForTargetStatsUnderCap=s['maximumReservedHealingForTargetStatsUnderCap'],metrics=s['metrics']);results.append(row)
  if row['originalBytecodeVerified']:verified.append(dict(index=n,mutation=pair,directory=str(d),hp=row['numericHP']))
  receipt=dict(schemaVersion=1,sourceSHA256=s['sourceSHA256'],mutationListSHA256=hashlib.sha256(raw).hexdigest(),scope=__doc__,fixedAdvance=[135,143],fixedExtraAdvances=[[352,353],[352,549]],mustEat=[333,375,376,549],targetReservedHealing=1300,targetStats=[696,625,2],enumeratedCases=len(candidates),completed=len(results),complete=len(results)==len(candidates),verified=verified,results=results,recordBreakingRoute=False,metrics=dict(states=sum(x['metrics']['states'] for x in results),transitions=sum(x['metrics']['transitions'] for x in results),elapsedSeconds=time.perf_counter()-start,childPeakRSSBytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
  (out/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
  if n%25==0 or s['targetNumericSurvives']:print(json.dumps(dict(index=n,total=len(candidates),elapsedSeconds=time.perf_counter()-start,**row)),flush=True)
  if verified:print('FOUND',verified[-1],flush=True);break
if __name__=='__main__':main()
