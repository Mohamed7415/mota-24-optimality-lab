"""Finite fixed-order numerical HP search with no AD10088 constraint.
No native/H5 game or record claim follows from these2018 bytecode trials.
"""
import sys,json,time,copy,hashlib,resource,itertools,argparse
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--swf',required=True);parser.add_argument('--grid',choices=('coarse','refined','fullhp'),default='coarse');parser.add_argument('--prior',default='experiments/late-hp-unconstrained-coarse.json');parser.add_argument('--out',required=True);args=parser.parse_args()
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Expected pinned2018 archive')
src=Path('experiments/full-route-hp28568-proposal.json');raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()=='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9'
actions=json.loads(raw)['actions'];out=Path(args.out);out.mkdir(exist_ok=False);base=OriginalRoute(args.swf,random_policy='worst-support');started=time.perf_counter()
for a in actions[:1328]:base.replay_action(a)
recipes=[(29,0,11,0)]+[(d,h,d2,h2)for d in (0,5,10,15)for h in (0,2,4,6)for d2 in (0,5)for h2 in (0,2)]
if args.grid=='refined':
 previous=json.load(open(args.prior))
 if previous['sourceProposalSHA256']!=hashlib.sha256(raw).hexdigest():raise ValueError('Prior grid uses a different proposal')
 seen={(x['recipe']['goldGroup1Defense'],x['recipe']['goldGroup1HP'],x['recipe']['goldGroup2Defense'],x['recipe']['goldGroup2HP'])for x in previous['rows']}
 recipes=[(d,h,d2,h2)for d in (10,15,20,25,29)for h in (0,2,4,6,10)if d+h<=29 for d2 in (0,5,11)for h2 in (0,3,6,11)if d2+h2<=11 and (d,h,d2,h2)not in seen]
if args.grid=='fullhp':
 recipes=[(d,29-d,d2,11-d2)for d in (0,5,10,15,20,25,29)for d2 in (0,3,6,9,11)]
rows=[];best=None
for number,(d,h,d2,h2) in enumerate(recipes):
 r=copy.deepcopy(base);case_started=time.perf_counter();error=None;i=None
 try:
  for i,a in enumerate(actions[1328:],1328):
   if 1328<=i<=1356:
    offset=i-1328
    if offset<d:r.touch(a['floor'],*a['position'],shop_choice=3)
    elif offset<d+h:r.touch(a['floor'],*a['position'],shop_choice=1)
    continue
   if 1437<=i<=1447:
    offset=i-1437
    if offset<d2:r.touch(a['floor'],*a['position'],shop_choice=3)
    elif offset<d2+h2:r.touch(a['floor'],*a['position'],shop_choice=1)
    continue
   if 1555<=i<=1614:
    if i==1555:
     while r.resources()['money']>=100:r.touch(a['floor'],*a['position'],shop_choice=1)
    continue
   r.replay_action(a)
 except Exception as e:error=f'{type(e).__name__}: {e}'
 row=dict(case=number,recipe=dict(goldGroup1Defense=d,goldGroup1HP=h,goldGroup2Defense=d2,goldGroup2HP=h2,lateGoldPolicy='Spend available100-gold budget on4000HP'),completeNumericalReplay=error is None and i==1712,lastSourceAction=i,error=error,resources=r.resources(),location=r.location(),generatedActions=len(r.actions),suffixBytecodeInstructions=r.instructions-base.instructions,metrics=dict(elapsedSeconds=time.perf_counter()-case_started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
 rows.append(row)
 if row['completeNumericalReplay'] and (best is None or row['resources']['hp']>best['resources']['hp']):
  best=row;print('BEST',json.dumps(row),flush=True)
  (out/'proposal-best-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources(),'recipe':row['recipe']},indent=2))
 if number%10==0:print('PROGRESS',number+1,'of',len(recipes),flush=True)
 report=dict(schemaVersion=1,scope='Fixed-order2018 original-bytecode HP grid; no native/H5 or record proof',sourceProposalSHA256=hashlib.sha256(raw).hexdigest(),fixedPrefixActions=1328,cases=len(recipes),completed=len(rows),complete=len(rows)==len(recipes),best=best,rows=rows,clockDeadlineSimulated=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,totalSuffixBytecodeInstructions=sum(x['suffixBytecodeInstructions']for x in rows),peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print('COMPLETE',json.dumps({k:v for k,v in report.items()if k!='rows'}),flush=True)
