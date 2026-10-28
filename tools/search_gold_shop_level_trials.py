"""Bounded original-bytecode low-gold-shop experiment; no native/H5 record claim."""
import sys,json,time,hashlib,resource,copy,argparse
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--swf',required=True);parser.add_argument('--out',default='generated/GoldShopLevelTrialsReproduction');args=parser.parse_args()
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Expected pinned2018 archive')
src=Path('experiments/full-route-hp28568-proposal.json');raw=src.read_bytes();
if hashlib.sha256(raw).hexdigest()!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Source proposal changed')
actions=json.loads(raw)['actions'];out=Path(args.out);out.mkdir(exist_ok=False)
rows=[]
for redirect in (1087,980,930):
 r=OriginalRoute(args.swf,random_policy='worst-support');started=time.perf_counter();error=None;failed=None
 try:
  for i,a in enumerate(actions):
   failed=i
   if i in (1087,1255,1616):
    count={1087:17,1255:21,1616:48}[i]
    r.fly(5)
    for _ in range(count):r.touch(5,1,7,shop_choice=1)
    if i==1616:
     while r.resources()['experience']>=30:r.touch(5,1,7,shop_choice=2)
    r.fly(12)
   if 1087<=i<=1104 or 1255<=i<=1277 or 1616<=i<=1666:continue
   if 1555<=i<=1614:
    if i<1557:r.touch(a['floor'],*a['position'],shop_choice=1)
    continue
   if a.get('shop')==2 and a.get('choice')==3 and i>=redirect:
    r.touch(a['floor'],*a['position'],shop_choice=2)
   else:r.replay_action(a)
 except Exception as e:error=f'{type(e).__name__}: {e}'
 row=dict(redirectGoldDEFToATKFromSource=redirect,completeNumericalReplay=error is None and failed==1712,error=error,lastProcessedSource=failed,resources=r.resources(),location=r.location(),goldShopPurchases=sum(a.get('shop')in(1,2)and a.get('choice')in(1,2,3)for a in r.actions),metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 rows.append(row);print(json.dumps(row),flush=True)
 (out/f'proposal-{redirect}-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources()}))
 (out/'receipt.json').write_text(json.dumps({'scope':'Three original-bytecode numerical gold-shop-count160 trials; no native/H5 game or record proof','sourceProposalSHA256':hashlib.sha256(raw).hexdigest(),'rows':rows},indent=2))
