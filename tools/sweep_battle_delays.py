"""Check bounded battle delays with affordable ASAP purchases and potion DP.

Stop at the first bytecode-verified prefix for full-route follow-up. Results are
numeric and bounded; no native completion or record claim is inferred.
"""
import argparse,hashlib
import json,subprocess,sys,time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('mutations');ap.add_argument('--out',default='generated/BattleDelaySweep');args=ap.parse_args()
mutation_bytes=Path(args.mutations).read_bytes();pairs=json.loads(mutation_bytes);out=Path(args.out);out.mkdir(exist_ok=False);start=time.perf_counter();results=[]
for index,pair in enumerate(pairs):
 folder=out/f'case-{index:04d}'
 proc=subprocess.run([sys.executable,'tools/search_potion_deferral.py','--asap-gold','--asap-xp','--delay',','.join(map(str,pair)),'--out',str(folder)],capture_output=True,text=True)
 (out/f'case-{index:04d}.log').write_text(proc.stdout+proc.stderr)
 if proc.returncode:raise RuntimeError(f'Case {index} failed: '+proc.stderr[-500:])
 r=json.loads((folder/'summary.json').read_text());results.append(r)
 if r['targetNumericSurvives']:print('NUMERIC',index,pair,r,flush=True)
 if r.get('originalBytecodeVerified'):
  print('FOUND',index,pair,folder,flush=True);break
 if index%25==0:print('PROGRESS',index,len(pairs),time.perf_counter()-start,flush=True)
report=dict(mutationListSHA256=hashlib.sha256(mutation_bytes).hexdigest(),scope='Bounded battle delays with ASAP affordable stat purchases and all early potion subsets; graph pruning and single best HP witness per compressed state may miss routes.',casesCompleted=len(results),enumeratedCases=len(pairs),verified=[dict(index=i,pair=pairs[i],hp=r.get('numericHP')) for i,r in enumerate(results) if r.get('originalBytecodeVerified')],numericSurvivors=sum(r['targetNumericSurvives'] for r in results),metrics=dict(states=sum(r['metrics']['states'] for r in results),transitions=sum(r['metrics']['transitions'] for r in results),peakChildRSSBytes=max((r['metrics']['processPeakRSSBytes'] for r in results),default=0),seconds=time.perf_counter()-start))
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print('FINISHED',report,flush=True)
